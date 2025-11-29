"""LangGraph tutoring agent with stateful conversation management.

This module defines the tutoring agent that manages the conversation flow
through different states: exposition, questioning, evaluation, diagnosis, and socratic.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Literal, Optional, TypedDict

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from openai import AsyncOpenAI

from bloom.database import (
    get_cached_exposition,
    get_cached_image,
    save_cached_exposition,
    save_cached_image,
    validate_image_data,
)

# pylint: disable=logging-fstring-interpolation, broad-exception-caught

# Load environment variables
load_dotenv()

# LLM Configuration (load directly to avoid circular import with main.py)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH", "bloom.db")

# Image Generation Configuration (spec 003)
ENABLE_IMAGE_GENERATION = os.getenv("ENABLE_IMAGE_GENERATION", "true").lower() == "true"
IMAGE_GENERATION_MODEL = os.getenv("IMAGE_GENERATION_MODEL", "gemini-3-pro-image")
IMAGE_GENERATION_RESOLUTION = os.getenv("IMAGE_GENERATION_RESOLUTION", "2K")

# Configure logger for state machine
logger = logging.getLogger("bloom.tutor_agent")

# Image cache statistics (spec 003 - Phase 4)
_image_cache_stats = {"hits": 0, "misses": 0, "hit_rate": 0.0}


def get_image_cache_stats() -> dict:
    """Get current image cache statistics.

    Returns:
        Dict with hits, misses, and hit_rate percentage
    """
    return _image_cache_stats.copy()


def _update_cache_stats(is_hit: bool) -> None:
    """Update cache statistics and calculate hit rate.

    Args:
        is_hit: True if cache hit, False if cache miss
    """
    global _image_cache_stats
    if is_hit:
        _image_cache_stats["hits"] += 1
    else:
        _image_cache_stats["misses"] += 1

    total = _image_cache_stats["hits"] + _image_cache_stats["misses"]
    if total > 0:
        _image_cache_stats["hit_rate"] = (_image_cache_stats["hits"] / total) * 100
        logger.info(
            f"📊 Image cache stats: {_image_cache_stats['hits']} hits, "
            f"{_image_cache_stats['misses']} misses, "
            f"{_image_cache_stats['hit_rate']:.1f}% hit rate"
        )


# ============================================================================
# Agent State Definition
# ============================================================================


class MessageDict(TypedDict):
    """Type definition for chat messages in agent state."""

    role: str  # 'student' or 'tutor'
    content: str
    timestamp: str


class CalculatorHistoryDict(TypedDict):
    """Type definition for calculator operations."""

    expression: str
    result: str


class EvaluationDict(TypedDict):
    """Type definition for answer evaluation results."""

    correct: bool
    feedback: str


class TutorState(TypedDict):
    """State definition for the tutoring agent.

    This state is passed between nodes in the LangGraph state machine.
    """

    subtopic_id: int
    subtopic_name: str
    current_state: Literal["exposition", "questioning", "evaluation", "diagnosis", "socratic"]
    messages: list[MessageDict]
    questions_correct: int
    questions_attempted: int
    calculator_visible: bool
    last_student_answer: Optional[str]
    calculator_history: list[CalculatorHistoryDict]
    last_question: Optional[str]  # Store the last question asked
    last_evaluation: Optional[EvaluationDict]  # Store evaluation result


# ============================================================================
# Multi-Provider LLM Client Wrapper
# ============================================================================


class LLMClient:
    """Unified client for multiple LLM providers with retry logic."""

    def __init__(self, provider: str = LLM_PROVIDER, model: str = LLM_MODEL):
        self.provider = provider
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazily initialize the appropriate LLM client."""
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            self._client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        elif self.provider == "anthropic":
            self._client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        elif self.provider == "xai":
            self._client = AsyncOpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")
        elif self.provider == "google":
            # Google Gemini uses a different API pattern
            try:
                import google.generativeai as genai

                genai.configure(api_key=GOOGLE_API_KEY)
                self._client = genai
            except ImportError as exc:
                raise ImportError(
                    "google-generativeai package required for Google provider"
                ) from exc
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        return self._client

    async def generate(self, prompt: str, max_retries: int = 3) -> str:
        """Generate a response from the LLM with retry logic.

        Args:
            prompt: The prompt to send to the LLM
            max_retries: Maximum number of retry attempts

        Returns:
            Generated text response

        Raises:
            Exception: If all retries fail
        """
        client = self._get_client()

        for attempt in range(max_retries):
            try:
                if self.provider in ["openai", "xai"]:
                    response = await client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=1000,
                    )
                    return response.choices[0].message.content

                elif self.provider == "anthropic":
                    response = await client.messages.create(
                        model=self.model,
                        max_tokens=1000,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return response.content[0].text

                elif self.provider == "google":
                    model = client.GenerativeModel(self.model)
                    response = await model.generate_content_async(prompt)
                    return response.text

            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    raise RuntimeError(
                        f"LLM API failed after {max_retries} attempts: {str(e)}"
                    ) from e
                # Exponential backoff
                await asyncio.sleep(2**attempt)

        raise RuntimeError("LLM generation failed")


# Global LLM client instance
llm_client = LLMClient()


# ============================================================================
# State Node Functions
# ============================================================================


async def exposition_node(state: TutorState) -> TutorState:
    """Generate or retrieve cached concept explanation for the current subtopic.

    This is typically the first state in a tutoring session.
    Checks cache before generating to reduce LLM API costs.

    If there are existing messages, this handles follow-up questions about the concept.
    """
    logger.info(
        "→ ENTERING STATE: exposition (subtopic: %s)", state.get("subtopic_name", "Unknown")
    )

    subtopic_id = state["subtopic_id"]

    # Check if this is initial exposition or a follow-up question
    # Initial exposition: no messages yet or only tutor messages
    is_initial = not any(msg["role"] == "student" for msg in state["messages"])

    if is_initial:
        # Initial exposition - check cache first
        cached = get_cached_exposition(subtopic_id, DATABASE_PATH)

        if cached:
            # Cache hit - use cached content
            explanation = cached["exposition_content"]
            logger.info(
                f"✓ Cache HIT for subtopic {subtopic_id} (model: {cached['model_identifier']})"
            )
        else:
            # Cache miss - generate via LLM
            logger.info(f"✗ Cache MISS for subtopic {subtopic_id}, generating new exposition")

            prompt = f"""
You are a patient, encouraging GCSE mathematics tutor,
helping a student learn {state['subtopic_name']}.

Your task: Provide a clear, engaging explanation of this topic.
- Use friendly, age-appropriate language (14-16 years old)
- Include a concrete example
- Keep it concise (2-3 paragraphs)
- End by asking if they have any questions before moving to practice

Do NOT ask a practice question yet - just explain the concept clearly."""

            try:
                explanation = await llm_client.generate(prompt)

                # NEW: Save to cache after successful generation
                save_cached_exposition(
                    subtopic_id=subtopic_id,
                    content=explanation,
                    model_identifier=LLM_MODEL,
                    db_path=DATABASE_PATH,
                )
                logger.info(f"✓ Cached new exposition for subtopic {subtopic_id}")

            except Exception as e:
                # Error handling
                logger.error("Exposition generation failed: %s", str(e))
                state["messages"].append(
                    {
                        "role": "tutor",
                        "content": "I'm having trouble connecting right now."
                        f"Please try again in a moment. "
                        f"(Error: {str(e)})",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                return state

        # Image Generation Integration (spec 003 - US2/US3)
        # Retrieve cached image or generate new one
        # This happens asynchronously so text displays first
        try:
            # Check if image already exists in cache (US2: Cache Retrieval)
            cached_image = get_cached_image(subtopic_id, DATABASE_PATH)

            if cached_image:
                # Cache hit - image available instantly (<1s)
                logger.info(
                    f"✓ Image cache HIT | "
                    f"subtopic_id={subtopic_id} | "
                    f"size={cached_image['file_size']} bytes | "
                    f"format={cached_image.get('image_format', 'PNG')} | "
                    f"model={cached_image.get('model_identifier', 'unknown')} | "
                    f"generated_at={cached_image.get('generated_at', 'unknown')}"
                )
                _update_cache_stats(is_hit=True)
                # Image metadata available for frontend via /api/image/{subtopic_id}
            else:
                # Cache miss - generate image (US3: First-Time Generation)
                logger.info(
                    f"✗ Image cache MISS | "
                    f"subtopic_id={subtopic_id} | "
                    f"action=generating_new_image"
                )
                _update_cache_stats(is_hit=False)

                # Generate image asynchronously (non-blocking for text display)
                image_data = await generate_whiteboard_image(
                    exposition_text=explanation,
                    model=IMAGE_GENERATION_MODEL,
                    resolution=IMAGE_GENERATION_RESOLUTION,
                )

                if image_data:
                    # Validate image before caching
                    if validate_image_data(image_data):
                        # Save validated image to cache
                        save_cached_image(
                            subtopic_id=subtopic_id,
                            image_data=image_data,
                            model_identifier=IMAGE_GENERATION_MODEL,
                            prompt_version="v1",
                            db_path=DATABASE_PATH,
                        )
                        logger.info(
                            f"✓ Image CACHED | "
                            f"subtopic_id={subtopic_id} | "
                            f"size={len(image_data)} bytes | "
                            f"model={IMAGE_GENERATION_MODEL} | "
                            f"format=PNG | "
                            f"prompt_version=v1"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Image VALIDATION_FAILED | "
                            f"subtopic_id={subtopic_id} | "
                            f"size={len(image_data)} bytes | "
                            f"action=not_caching"
                        )
                else:
                    logger.warning(
                        f"⚠️ Image GENERATION_FAILED | "
                        f"subtopic_id={subtopic_id} | "
                        f"result=None | "
                        f"action=continuing_text_only"
                    )

        except Exception as e:
            # Graceful degradation: log error but don't fail the session
            logger.error(
                f"❌ Image ERROR | "
                f"subtopic_id={subtopic_id} | "
                f"error_type={type(e).__name__} | "
                f"error={str(e)} | "
                f"action=text_only_fallback",
                exc_info=True,
            )
            # Session continues with text-only mode
    else:
        # Follow-up question - student asked something about the concept
        logger.info("Student asked follow-up question in exposition")

        # Build conversation context
        recent_context = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in state["messages"][-5:]]
        )

        prompt = f"""
You are a patient, encouraging GCSE mathematics tutor,
helping a student learn {state['subtopic_name']}.

The student has asked a follow-up question about the concept you're explaining.

Recent conversation:
{recent_context}

Your task: Answer their question clearly and helpfully.
- Be patient and encouraging
- Provide additional explanation or examples if needed
- Keep it focused on the concept of {state['subtopic_name']}
- After answering, ask if they'd like to try a practice question or have more questions

Do NOT ask a practice question yet unless they explicitly request one."""

        try:
            explanation = await llm_client.generate(prompt)
            logger.info("Generated response to follow-up question")

        except Exception as e:
            # Error handling
            logger.error("Follow-up response generation failed: %s", str(e))
            state["messages"].append(
                {
                    "role": "tutor",
                    "content": (
                        "I'm having trouble connecting right now. "
                        f"Please try again in a moment. "
                        f"(Error: {str(e)})"
                    ),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            return state

    # Add message to state (whether cached or freshly generated)
    state["messages"].append(
        {"role": "tutor", "content": explanation, "timestamp": datetime.utcnow().isoformat()}
    )

    # Stay in exposition state - wait for student to request a question
    logger.info("← STAYING IN STATE: exposition (waiting for student to request question)")

    return state


async def questioning_node(state: TutorState) -> TutorState:
    """Generate an appropriate GCSE-level question.

    This node creates questions to test student understanding.
    """
    logger.info(
        "→ ENTERING STATE: questioning (subtopic: %s)", state.get("subtopic_name", "Unknown")
    )

    # Build context from recent messages
    recent_context = "\n".join(
        [
            f"{msg['role']}: {msg['content']}"
            for msg in state["messages"][-5:]  # Last 5 messages for context
        ]
    )

    prompt = f"""You are a GCSE mathematics tutor teaching {state['subtopic_name']}.

Recent conversation:
{recent_context}

Your task: Ask ONE clear, appropriate practice question.
- Make it suitable for GCSE level
- The question should test understanding of {state['subtopic_name']}
- Be specific and clear about what you're asking
- If the question requires numerical calculation, it should be solvable with basic arithmetic

Just ask the question - no additional explanation needed."""

    try:
        question = await llm_client.generate(prompt)

        state["messages"].append(
            {"role": "tutor", "content": question, "timestamp": datetime.utcnow().isoformat()}
        )

        state["last_question"] = question
        state["questions_attempted"] += 1

        # Determine if calculator should be visible
        state["calculator_visible"] = await should_show_calculator(question)

        # Next state: wait for student answer, then evaluate
        # Set to "questioning" so next student response triggers evaluation
        state["current_state"] = "questioning"
        logger.info("← TRANSITIONING TO STATE: questioning (waiting for student answer)")

    except Exception as e:
        state["messages"].append(
            {
                "role": "tutor",
                "content": f"I'm having trouble generating a question. Let's try again. (Error: {str(e)})",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    return state


async def evaluation_node(state: TutorState) -> TutorState:
    """Evaluate the student's answer.

    Determines if the answer is correct, partially correct, or incorrect.
    Sets current_state to route to next node via conditional edges.
    """
    logger.info(
        "→ ENTERING STATE: evaluation (answer: %s)", state.get("last_student_answer", "None")[:50]
    )

    if not state["last_student_answer"]:
        # No answer to evaluate yet
        return state

    prompt = f"""You are evaluating a GCSE mathematics student's answer.

Question: {state.get('last_question', 'N/A')}
Student's answer: {state['last_student_answer']}

Evaluate the answer and respond with JSON in this exact format:
{{
    "correct": true/false,
    "feedback": "Brief feedback explaining why it's correct or incorrect"
}}

Be encouraging even when incorrect. Keep feedback brief (1-2 sentences)."""

    try:
        response = await llm_client.generate(prompt)

        # Parse JSON response
        # Extract JSON from response (handle markdown code blocks)
        json_str = response.strip()
        if json_str.startswith("```"):
            # Remove markdown code blocks
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1])

        evaluation = json.loads(json_str)

        state["last_evaluation"] = evaluation

        # Update counters
        if evaluation.get("correct", False):
            state["questions_correct"] += 1

            # Add positive feedback
            state["messages"].append(
                {
                    "role": "tutor",
                    "content": f"✓ {evaluation['feedback']}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Route to questioning for next question
            state["current_state"] = "questioning"
            logger.info("✓ Answer CORRECT - routing to questioning")
        else:
            # Incorrect answer - just acknowledge it, Socratic node will guide
            # Keep feedback brief and don't give away the answer
            state["messages"].append(
                {
                    "role": "tutor",
                    "content": "Not quite.",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Route to diagnosis to analyze the error (then to socratic)
            state["current_state"] = "diagnosis"
            logger.info("✗ Answer INCORRECT - routing to diagnosis")

    except Exception as e:
        state["messages"].append(
            {
                "role": "tutor",
                "content": f"I had trouble evaluating that. Could you try rephrasing your answer? (Error: {str(e)})",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    return state


async def diagnosis_node(state: TutorState) -> TutorState:
    """Identify the student's misconception.

    Analyzes incorrect answers to understand what went wrong.
    This node doesn't add messages - it just prepares context for socratic node.
    """
    logger.info("→ ENTERING STATE: diagnosis (analyzing incorrect answer)")

    # Store diagnostic information in state for socratic node to use
    # This node is silent - it just analyzes
    # The socratic node will do the actual guiding

    # Route to socratic guidance
    state["current_state"] = "socratic"
    logger.info("← TRANSITIONING TO STATE: socratic (will provide guided hint)")

    return state


async def socratic_node(state: TutorState) -> TutorState:
    """Ask guiding questions to help student discover the right approach.

    Uses Socratic method - asking questions rather than giving answers.
    """
    logger.info("→ ENTERING STATE: socratic (providing Socratic guidance)")

    # Get recent conversation context
    recent_messages = "\n".join(
        [f"{msg['role']}: {msg['content']}" for msg in state["messages"][-3:]]
    )

    prompt = f"""You are a GCSE mathematics tutor using the Socratic method to guide a student.

Original question: {state.get('last_question', 'N/A')}
Student's incorrect answer: {state['last_student_answer']}
Topic: {state['subtopic_name']}

Recent conversation:
{recent_messages}

THE SOCRATIC METHOD - Critical Guidelines:
1. NEVER tell them what to do
2. NEVER give the answer or steps
3. ALWAYS ask a question that makes them think
4. Focus on ONE key concept they're missing
5. Guide them to discover the error themselves

Examples of good Socratic questions:
- "When you expand a bracket, how many terms do you need to multiply?"
- "What does the minus sign in front of a bracket do to the terms inside?"
- "If you have 5(2y - 3), what are you multiplying 5 by?"

Your task: Ask ONE simple, focused question that guides them toward understanding.
Be warm and encouraging. Don't explain - just ask."""

    try:
        hint_question = await llm_client.generate(prompt)

        state["messages"].append(
            {"role": "tutor", "content": hint_question, "timestamp": datetime.utcnow().isoformat()}
        )

        # Stay in socratic state - next student message will be evaluated
        state["current_state"] = "socratic"
        logger.info("← STAYING IN STATE: socratic (waiting for student to try again)")

    except Exception:
        state["messages"].append(
            {
                "role": "tutor",
                "content": "Let's think about this step by step. What's the first thing you need to do when expanding brackets?",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        state["current_state"] = "socratic"

    return state


# ============================================================================
# Image Generation Functions (spec 003)
# ============================================================================


async def generate_whiteboard_image(
    exposition_text: str,
    model: str = IMAGE_GENERATION_MODEL,
    resolution: str = IMAGE_GENERATION_RESOLUTION,
) -> Optional[bytes]:
    """Generate whiteboard-style image from exposition text.

    Uses Google Gemini image generation to create a professor's whiteboard
    visualization with diagrams, arrows, boxes, and colorful captions.

    Args:
        exposition_text: The full text exposition content to visualize
        model: Gemini image model to use (default: from env)
        resolution: Image resolution (1K, 2K, or 4K) - defaults to 2K

    Returns:
        PNG image bytes at specified resolution, or None if generation fails

    Note:
        - 2K resolution (2048x2048) provides excellent quality
        - Generation typically takes 5-10 seconds
        - Failures are logged but don't raise exceptions
    """
    # Check if image generation is enabled
    if not ENABLE_IMAGE_GENERATION:
        logger.info(
            f"Image generation DISABLED | " f"flag=ENABLE_IMAGE_GENERATION | " f"action=skipping"
        )
        return None

    # Whiteboard prompt template
    prompt = f"""
now take the text from your reply and transform it into a professor's whiteboard image:
diagrams, arrows, boxes, and captions explaining the core idea visually. Use colors as well.

Text to visualize:
{exposition_text}"""

    try:
        # Initialize Google Gemini Client for image generation
        from google import genai
        from google.genai import types

        logger.info(
            f"🎨 Image GENERATION_START | "
            f"model={model} | "
            f"resolution={resolution} | "
            f"text_length={len(exposition_text)} chars"
        )
        start_time = asyncio.get_event_loop().time()

        # Create client with API key
        client = genai.Client(api_key=GOOGLE_API_KEY)

        # Configure for specified resolution (2K = 2048x2048)
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            # Note: Resolution is determined by model capabilities
            # 2K images will be generated at 2048x2048 (1:1 aspect ratio)
        )

        # Call Gemini API to generate image
        response = await asyncio.to_thread(
            client.models.generate_content, model=model, contents=prompt, config=config
        )

        # Extract PNG image bytes from response
        image_data = None
        for part in response.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                break

        if image_data is None:
            logger.error(
                f"❌ Image GENERATION_FAILED | "
                f"error=no_image_data_in_response | "
                f"model={model}"
            )
            return None

        # Log success with timing and file size (T094: duration, T093: detailed context)
        duration = asyncio.get_event_loop().time() - start_time
        logger.info(
            f"✓ Image GENERATION_SUCCESS | "
            f"duration={duration:.2f}s | "
            f"size={len(image_data)} bytes | "
            f"size_mb={len(image_data) / 1048576:.2f} MB | "
            f"model={model} | "
            f"resolution={resolution}"
        )

        return image_data

    except ImportError as e:
        logger.error(
            f"❌ Image GENERATION_ERROR | "
            f"error_type=ImportError | "
            f"error=google-genai_not_available | "
            f"details={str(e)}",
            exc_info=False,
        )
        return None
    except Exception as e:
        logger.error(
            f"❌ Image GENERATION_ERROR | "
            f"error_type={type(e).__name__} | "
            f"error={str(e)} | "
            f"model={model}",
            exc_info=True,
        )
        return None


# ============================================================================
# Utility Functions
# ============================================================================


async def should_show_calculator(question_text: str) -> bool:
    """Determine if calculator should be visible based on question type.

    Args:
        question_text: The question being asked

    Returns:
        True if calculator should be shown (numerical problem)
    """
    prompt = f"""Classify this math question as NUMERICAL or NON_NUMERICAL.

NUMERICAL: Requires actual number computation (e.g., "Calculate 3/4 + 2/5", "What is 15% of 240?")
NON_NUMERICAL: Algebraic manipulation, proofs, concepts (e.g., "Simplify 2x + 3x", "Explain Pythagoras' theorem")

Question: {question_text}

Answer with only one word: NUMERICAL or NON_NUMERICAL"""

    try:
        response = await llm_client.generate(prompt)
        logger.info(f"Calculator visibility assessed: {response}")
        return "NUMERICAL" in response.upper()
    except Exception:
        # Default to showing calculator if classification fails
        return False


# ============================================================================
# Conditional Routing Functions
# ============================================================================


def route_from_exposition(state: TutorState) -> str:
    """Route from exposition based on student response.

    If student asks for question, go to questioning.
    Otherwise stay in exposition to continue dialogue.
    """
    # Check if last student message requests a question
    if state["messages"]:
        last_msg = state["messages"][-1]
        if last_msg["role"] == "student":
            content = last_msg["content"].lower()
            # Simple keyword detection
            if any(word in content for word in ["question", "practice", "try", "test", "quiz"]):
                logger.info("→ Routing from exposition to questioning")
                return "questioning"

    # Default: stay in exposition (END means wait for next message)
    return "END"


def route_from_questioning(_state: TutorState) -> str:
    """Route from questioning based on whether we have an answer.

    After generating question, wait for student answer (END).
    """
    # After asking question, always wait for student response
    return "END"


def route_from_evaluation(state: TutorState) -> str:
    """Route from evaluation based on correctness.

    - Correct → questioning (new question)
    - Incorrect → diagnosis (analyze error)
    """
    if state.get("last_evaluation"):
        if state["last_evaluation"].get("correct", False):
            logger.info("→ Routing from evaluation to questioning (correct answer)")
            return "questioning"
        else:
            logger.info("→ Routing from evaluation to diagnosis (incorrect answer)")
            return "diagnosis"

    # Fallback: wait for answer
    return "END"


def route_from_diagnosis(_state: TutorState) -> str:
    """Route from diagnosis to socratic guidance.

    After diagnosing error, provide Socratic hints.
    """
    logger.info("→ Routing from diagnosis to socratic")
    return "socratic"


def route_from_socratic(_state: TutorState) -> str:
    """Route from socratic node.

    After asking guiding question, wait for student to try again (END).
    """
    # After Socratic hint, wait for student response
    return "END"


# ============================================================================
# LangGraph State Machine Setup
# ============================================================================


def create_tutor_graph():
    """Create the LangGraph state machine for tutoring.

    Returns:
        Configured StateGraph ready for execution
    """
    # Create the graph
    graph = StateGraph(TutorState)

    # Add nodes
    graph.add_node("exposition", exposition_node)
    graph.add_node("questioning", questioning_node)
    graph.add_node("evaluation", evaluation_node)
    graph.add_node("diagnosis", diagnosis_node)
    graph.add_node("socratic", socratic_node)

    # Set entry point
    graph.set_entry_point("exposition")

    # Add conditional edges (routing logic)
    graph.add_conditional_edges(
        "exposition",
        route_from_exposition,
        {
            "questioning": "questioning",
            "END": "__end__",  # Wait for next student message
        },
    )

    graph.add_conditional_edges(
        "questioning",
        route_from_questioning,
        {
            "END": "__end__",  # Wait for student answer
        },
    )

    graph.add_conditional_edges(
        "evaluation",
        route_from_evaluation,
        {
            "questioning": "questioning",  # Correct → new question
            "diagnosis": "diagnosis",  # Incorrect → analyze error
            "END": "__end__",
        },
    )

    graph.add_conditional_edges(
        "diagnosis",
        route_from_diagnosis,
        {
            "socratic": "socratic",  # Always go to Socratic guidance
        },
    )

    graph.add_conditional_edges(
        "socratic",
        route_from_socratic,
        {
            "END": "__end__",  # Wait for student to try again
        },
    )

    # Compile the graph
    return graph.compile()


# Initialize the graph
tutor_graph = create_tutor_graph()


# ============================================================================
# Checkpoint Save/Restore Functions
# ============================================================================


def save_agent_checkpoint(session_id: int, state: TutorState, db_path: str = "bloom.db") -> None:
    """Save agent state to database for session resumption.

    Args:
        session_id: Session ID
        state: Current agent state
        db_path: Path to database file
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    state_json = json.dumps(state)

    cursor.execute(
        """
        INSERT OR REPLACE INTO agent_checkpoints (session_id, state_data)
        VALUES (?, ?)
    """,
        (session_id, state_json),
    )

    conn.commit()
    conn.close()


def load_agent_checkpoint(session_id: int, db_path: str = "bloom.db") -> Optional[TutorState]:
    """Load agent state from database.

    Args:
        session_id: Session ID
        db_path: Path to database file

    Returns:
        Restored agent state or None if no checkpoint found
    """
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT state_data
        FROM agent_checkpoints
        WHERE session_id = ?
    """,
        (session_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row[0])
    return None
