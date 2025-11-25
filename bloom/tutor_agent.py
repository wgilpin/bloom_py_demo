"""LangGraph tutoring agent with stateful conversation management.

This module defines the tutoring agent that manages the conversation flow
through different states: exposition, questioning, evaluation, diagnosis, and socratic.
"""

import json
import asyncio
import logging
from typing import Literal, TypedDict, Optional
from datetime import datetime

from langgraph.graph import StateGraph
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from bloom.main import (
    LLM_PROVIDER,
    LLM_MODEL,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    XAI_API_KEY,
    DATABASE_PATH,
)
from bloom.database import get_cached_exposition, save_cached_exposition

# Configure logger for state machine
logger = logging.getLogger("bloom.tutor_agent")


# ============================================================================
# Agent State Definition
# ============================================================================


class TutorState(TypedDict):
    """State definition for the tutoring agent.

    This state is passed between nodes in the LangGraph state machine.
    """

    subtopic_id: int
    subtopic_name: str
    current_state: Literal["exposition", "questioning", "evaluation", "diagnosis", "socratic"]
    messages: list[dict]  # {role: str, content: str}
    questions_correct: int
    questions_attempted: int
    calculator_visible: bool
    last_student_answer: Optional[str]
    calculator_history: list[dict]  # {expression: str, result: str}
    last_question: Optional[str]  # Store the last question asked
    last_evaluation: Optional[dict]  # Store evaluation result {correctness: str, feedback: str, misconception: str}
    hints_given: int  # Counter for Socratic hints provided for current question


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
    Uses Socratic principles: guide discovery, build on existing knowledge.
    Checks cache first to reduce API costs and improve response time.
    """
    logger.info("→ ENTERING STATE: exposition (subtopic: %s)", state.get('subtopic_name', 'Unknown'))
    
    # Initialize hints counter
    if "hints_given" not in state:
        state["hints_given"] = 0
    
    subtopic_id = state["subtopic_id"]
    
    # Check cache first
    cached = get_cached_exposition(subtopic_id, DATABASE_PATH)
    
    if cached:
        # Cache hit - use cached content
        exposition = cached["exposition_content"]
        logger.info("✓ Cache HIT for subtopic %s (model: %s)", subtopic_id, cached['model_identifier'])
        
        # Add tutor message to history
        state["messages"].append(
            {"role": "tutor", "content": exposition, "timestamp": datetime.utcnow().isoformat()}
        )
        
        logger.info("← STAYING IN STATE: exposition (waiting for student to request question)")
        
    else:
        # Cache miss - generate via LLM
        logger.info("✗ Cache MISS for subtopic %s, generating new exposition", subtopic_id)
        
        # Socratic teaching principles from docs/socratic_approach.md
        prompt = f"""You are a patient, encouraging GCSE mathematics tutor helping a student learn {state['subtopic_name']}.

CORE PHILOSOPHY - SOCRATIC METHOD:
You are a Facilitator, not an Instructor. Your goal is to help students construct mental models themselves through guided discovery.

TEACHING PRINCIPLES:
- Guide discovery through questions, don't provide direct answers
- Start with clear explanations before asking questions
- Use friendly, age-appropriate language (14-16 years old)
- Include a concrete, relatable example
- Connect to real-world applications when possible
- Build on what students likely already know

Your task: Provide a clear, engaging explanation of {state['subtopic_name']}.
- Keep it concise (2-3 paragraphs)
- Include one worked example to illustrate the concept
- End by asking if they have any questions before moving to practice
- Be warm and encouraging - make them feel confident to ask questions

Do NOT ask a practice question yet - just explain the concept clearly."""

        try:
            exposition = await llm_client.generate(prompt)

            # Save to cache after successful generation
            save_cached_exposition(
                subtopic_id=subtopic_id,
                content=exposition,
                model_identifier=LLM_MODEL,
                db_path=DATABASE_PATH
            )
            logger.info("✓ Cached new exposition for subtopic %s", subtopic_id)

            # Add tutor message to history
            state["messages"].append(
                {"role": "tutor", "content": exposition, "timestamp": datetime.utcnow().isoformat()}
            )

            # Stay in exposition state - wait for student to request a question
            # Don't change state here; the routing logic will handle the transition
            # state["current_state"] remains "exposition"
            logger.info("← STAYING IN STATE: exposition (waiting for student to request question)")

        except Exception as e:
            logger.error("Exposition generation failed: %s", str(e))
            # Error handling
            state["messages"].append(
                {
                    "role": "tutor",
                    "content": f"I'm having trouble connecting right now. Please try again in a moment. (Error: {str(e)})",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    return state


async def questioning_node(state: TutorState) -> TutorState:
    """Generate an appropriate GCSE-level question.

    This node creates questions to test student understanding.
    Resets hint counter for the new question.
    """
    logger.info("→ ENTERING STATE: questioning (subtopic: %s)", state.get('subtopic_name', 'Unknown'))
    
    # Reset hints counter for new question
    state["hints_given"] = 0
    
    # Build context from recent messages
    recent_context = "\n".join(
        [
            f"{msg['role']}: {msg['content']}"
            for msg in state["messages"][-5:]  # Last 5 messages for context
        ]
    )

    # Socratic teaching principles
    prompt = f"""You are a patient, encouraging GCSE mathematics tutor teaching {state['subtopic_name']}.

Recent conversation:
{recent_context}

SOCRATIC TEACHING PRINCIPLES:
- Guide discovery through questions, don't provide direct answers
- When student answers incorrectly, you'll ask guiding questions (not give solutions)
- Build on their existing knowledge with clear, age-appropriate language (14-16 years old)

Your task: Ask ONE clear, appropriate practice question.
- Make it suitable for GCSE level (appropriate difficulty)
- The question should test understanding of {state['subtopic_name']}
- Be specific and clear about what you're asking
- If the question requires numerical calculation, it should be solvable with basic arithmetic
- Frame the question in an engaging way

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
        logger.error("Question generation failed: %s", str(e))
        state["messages"].append(
            {
                "role": "tutor",
                "content": f"I'm having trouble generating a question. Let's try again. (Error: {str(e)})",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    return state


async def evaluation_node(state: TutorState) -> TutorState:
    """Evaluate the student's answer with detailed classification.

    Determines if the answer is correct, partially correct, or incorrect.
    Uses Socratic principles: diagnose before prescribing.
    """
    logger.info("→ ENTERING STATE: evaluation (answer: %s)", state.get('last_student_answer', 'None')[:50])
    
    if not state["last_student_answer"]:
        # No answer to evaluate yet
        return state
    
    # Check if student is requesting the full answer
    answer_lower = state["last_student_answer"].lower().strip()
    request_keywords = ["give me the answer", "just tell me", "what's the answer", "show me the answer", 
                       "i give up", "i don't know", "tell me how", "just show me"]
    
    is_answer_request = any(keyword in answer_lower for keyword in request_keywords)

    # Socratic Rule I: Diagnose Before You Prescribe
    # We need to understand what the student actually did, not assume competence
    prompt = f"""You are a GCSE mathematics tutor evaluating a student's answer using the Socratic method.

Question: {state.get('last_question', 'N/A')}
Student's answer: {state['last_student_answer']}
Topic: {state['subtopic_name']}

Your task: Carefully evaluate the student's response.

FIRST: Verify what the student ACTUALLY did. Do not assume they used a correct method.

Classify the answer as one of:
- "correct": The answer is fully correct
- "partial": The answer shows some understanding but has errors or is incomplete
- "incorrect": The answer is wrong or shows a fundamental misconception

Respond with JSON in this exact format:
{{
    "correctness": "correct" | "partial" | "incorrect",
    "feedback": "Brief, encouraging feedback (1-2 sentences)",
    "assessment": "What did the student actually do? What approach did they take?"
}}

Be encouraging even when incorrect. Focus on what you observed, not what you hoped to see."""

    try:
        response = await llm_client.generate(prompt)

        # Parse JSON response (handle markdown code blocks)
        json_str = response.strip()
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join([line for line in lines[1:-1] if line.strip()])

        evaluation = json.loads(json_str)
        correctness = evaluation.get("correctness", "incorrect")

        state["last_evaluation"] = evaluation

        # Handle different correctness levels
        if correctness == "correct":
            state["questions_correct"] += 1
            
            # Reset hints counter for next question
            state["hints_given"] = 0

            # Add positive feedback
            state["messages"].append(
                {
                    "role": "tutor",
                    "content": f"✓ {evaluation['feedback']}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Immediately generate next question
            logger.info("✓ Answer CORRECT - generating next question")
            state = await questioning_node(state)
            
        elif correctness == "partial":
            # Partial answer: provide encouraging feedback and guide to completion
            state["messages"].append(
                {
                    "role": "tutor",
                    "content": f"You're on the right track! {evaluation['feedback']}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            
            # Transition to diagnosis to identify what's missing
            state["current_state"] = "diagnosis"
            logger.info("◐ Answer PARTIAL - transitioning to diagnosis")
            
        else:  # incorrect
            # Check if student is requesting the answer directly
            if is_answer_request and state["hints_given"] >= 3:
                # Student has received enough hints and is explicitly asking for answer
                logger.info("Student requesting full answer after %d hints", state["hints_given"])
                state["current_state"] = "socratic"  # socratic_node will provide full solution
            else:
                # Standard incorrect answer flow
                state["messages"].append(
                    {
                        "role": "tutor",
                        "content": f"Not quite. {evaluation['feedback']}",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                
                # Next: diagnose the error
                state["current_state"] = "diagnosis"
                logger.info("✗ Answer INCORRECT - transitioning to diagnosis")

    except Exception as e:
        logger.error("Evaluation failed: %s", str(e))
        state["messages"].append(
            {
                "role": "tutor",
                "content": f"I had trouble evaluating that. Could you try rephrasing your answer? (Error: {str(e)})",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    return state


async def diagnosis_node(state: TutorState) -> TutorState:
    """Identify the student's specific misconception.

    Analyzes incorrect answers to understand what went wrong.
    Follows Socratic Rule I: Diagnose Before You Prescribe - research the thinking first.
    """
    logger.info("→ ENTERING STATE: diagnosis (analyzing incorrect answer)")
    
    # Get the assessment from evaluation if available
    assessment = ""
    if state.get("last_evaluation") and "assessment" in state["last_evaluation"]:
        assessment = f"\nObserved approach: {state['last_evaluation']['assessment']}"
    
    # Common misconception patterns for GCSE mathematics
    misconception_examples = """
Common GCSE misconception types:
- Linearity misconception: Treating non-linear operations as linear (e.g., (x+3)² = x² + 9)
- Operation confusion: Adding when should multiply, or vice versa (e.g., (2x)(3x) = 5x)
- Sign errors: Mistakes with negative numbers or when distributing negatives
- Order of operations: Ignoring BIDMAS/PEMDAS rules
- Common denominator: Forgetting to find common denominator when adding fractions
- Cancellation errors: Incorrectly canceling terms that aren't factors
- Unit confusion: Mixing up units or conversion factors
"""

    # Socratic Rule I: Diagnose Before You Prescribe
    prompt = f"""You are a GCSE mathematics tutor analyzing a student's mistake using the Socratic method.

Question: {state.get('last_question', 'N/A')}
Student's answer: {state['last_student_answer']}
Topic: {state['subtopic_name']}{assessment}

{misconception_examples}

CRITICAL: Follow Socratic Rule I - "Diagnose Before You Prescribe"
You cannot guide a student if you don't know where they are standing.

Your task: Identify the SPECIFIC misconception type.

Respond with JSON:
{{
    "misconception_type": "Brief name of the misconception (e.g., 'linearity misconception', 'forgot common denominator')",
    "explanation": "One sentence explaining what conceptual error they made",
    "diagnostic_question": "ONE focused question to help them recognize their error (do NOT give the answer)"
}}

Remember: Attack the concept, not the calculation. Go up a level to fix the mental model."""

    try:
        response = await llm_client.generate(prompt)
        
        # Parse JSON response
        json_str = response.strip()
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join([line for line in lines[1:-1] if line.strip()])

        diagnosis = json.loads(json_str)
        
        # Store misconception in evaluation state
        if state.get("last_evaluation"):
            state["last_evaluation"]["misconception"] = diagnosis.get("misconception_type", "unknown")
        
        # Present the diagnostic question to the student
        # Socratic Rule II: One Turn, One Question
        diagnostic_message = f"{diagnosis.get('explanation', '')} {diagnosis.get('diagnostic_question', '')}"
        
        state["messages"].append(
            {"role": "tutor", "content": diagnostic_message.strip(), "timestamp": datetime.utcnow().isoformat()}
        )
        
        logger.info("Diagnosed misconception: %s", diagnosis.get('misconception_type', 'unknown'))

        # Next: provide Socratic guidance
        state["current_state"] = "socratic"
        logger.info("← TRANSITIONING TO STATE: socratic (will provide guided hint)")

    except Exception as e:
        logger.error("Diagnosis failed: %s", str(e))
        state["messages"].append(
            {
                "role": "tutor",
                "content": "Let me help you think through this step by step. Can you walk me through how you got that result?",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        state["current_state"] = "socratic"

    return state


async def socratic_node(state: TutorState) -> TutorState:
    """Ask guiding questions with escalating hints.

    Uses Socratic method - asking questions rather than giving answers.
    Tracks hint count and escalates from subtle to explicit guidance.
    After 3 hints, provides full step-by-step solution if requested.
    """
    logger.info("→ ENTERING STATE: socratic (hint #%d)", state.get('hints_given', 0) + 1)
    
    # Increment hints counter
    current_hints = state.get("hints_given", 0)
    state["hints_given"] = current_hints + 1
    
    # Check if student is requesting full answer after enough hints
    answer_lower = state.get("last_student_answer", "").lower().strip()
    request_keywords = ["give me the answer", "just tell me", "what's the answer", "show me the answer", 
                       "i give up", "i don't know", "tell me how", "just show me"]
    is_answer_request = any(keyword in answer_lower for keyword in request_keywords)
    
    # Provide full solution if:
    # 1. Student has received 3+ hints, AND
    # 2. Student explicitly requests the answer
    if state["hints_given"] > 3 and is_answer_request:
        logger.info("Providing full step-by-step solution after %d hints", state["hints_given"])
        
        prompt = f"""You are a GCSE mathematics tutor. The student has struggled with this question despite multiple hints.

Question: {state.get('last_question', 'N/A')}
Student's incorrect answer: {state['last_student_answer']}
Topic: {state['subtopic_name']}
Hints already given: {state['hints_given']}

The student has explicitly requested the full answer. Provide a clear, step-by-step solution:
1. Show each step clearly
2. Explain WHY each step is necessary
3. Highlight the key concept they were missing
4. End with encouragement to try a similar problem next

Be kind and supportive - struggling is part of learning."""

        try:
            solution = await llm_client.generate(prompt)
            
            state["messages"].append(
                {
                    "role": "tutor",
                    "content": f"I can see you've been working hard on this. Let me show you the full solution:\n\n{solution}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Reset hints and move to next question
            state["hints_given"] = 0
            logger.info("← GENERATING NEXT QUESTION after providing solution")
            state = await questioning_node(state)
            
        except Exception as e:
            logger.error("Failed to generate solution: %s", str(e))
            state["messages"].append(
                {
                    "role": "tutor",
                    "content": "Let me show you the key steps to solve this problem...",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            state["current_state"] = "socratic"
            
        return state
    
    # Otherwise, provide escalating hints based on count
    # Hint strategy:
    # - Hint 1: Subtle, conceptual question (Rule III: Attack the concept, not calculation)
    # - Hint 2: More directed, guide toward specific step
    # - Hint 3: Explicit, but still let them do the final step
    # - Hint 4+: Very explicit guidance
    
    hint_level = "subtle" if state["hints_given"] == 1 else \
                 "directed" if state["hints_given"] == 2 else \
                 "explicit" if state["hints_given"] == 3 else "very_explicit"
    
    # Get misconception info if available
    misconception_context = ""
    if state.get("last_evaluation") and "misconception" in state["last_evaluation"]:
        misconception_context = f"\nIdentified misconception: {state['last_evaluation']['misconception']}"
    
    # Socratic teaching principles from docs/socratic_approach.md
    socratic_rules = """
SOCRATIC METHOD RULES:
1. Rule II: One Turn, One Question - Ask EXACTLY ONE focused question
2. Rule III: Attack the Concept, Not the Calculation - Fix the mental model, not just the numbers
3. Rule IV: Cognitive Conflict - Present counter-examples that make their model fail
"""

    prompt = f"""You are a GCSE mathematics tutor using the Socratic method.

Question: {state.get('last_question', 'N/A')}
Student's incorrect answer: {state['last_student_answer']}
Topic: {state['subtopic_name']}
Hint number: {state['hints_given']}{misconception_context}

{socratic_rules}

Hint level: {hint_level}

Your task based on hint level:

SUBTLE (Hint 1): Ask a broad conceptual question. Target the fundamental concept.
Example: "When two brackets are touching like (a)(b), what mathematical operation is happening between them?"

DIRECTED (Hint 2): Guide toward a specific step, but don't solve it for them.
Example: "Good question. Let's think about the first step. What should we do with the brackets first before we can simplify?"

EXPLICIT (Hint 3): Be very specific about what to do, but let them execute it.
Example: "To solve this, you need to multiply each term in the first bracket by each term in the second bracket. Can you try that?"

VERY_EXPLICIT (Hint 4+): Walk through the first step, then ask them to do the next.
Example: "Let me show you the first step: 2x × x = 2x². Now, can you multiply 2x × (-4)?"

Remember: 
- Ask EXACTLY ONE question (Rule II)
- For misconceptions like linearity, use cognitive conflict (Rule IV) - test with simple numbers
- Be encouraging and patient

Respond with just your hint question/guidance."""

    try:
        hint_message = await llm_client.generate(prompt)

        state["messages"].append(
            {
                "role": "tutor",
                "content": hint_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Next: wait for student to try again with the hint
        # Set to "socratic" so next message triggers evaluation
        state["current_state"] = "socratic"
        logger.info("← STAYING IN STATE: socratic (waiting for student attempt after hint #%d)", state["hints_given"])

    except Exception as e:
        logger.error("Socratic guidance failed: %s", str(e))
        state["messages"].append(
            {
                "role": "tutor",
                "content": "Think about the key steps in this problem. What should you do first?",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        state["current_state"] = "socratic"

    return state


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
        return "NUMERICAL" in response.upper()
    except Exception:
        # Default to showing calculator if classification fails
        return True


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

    # Define edges (state transitions)
    # Note: Actual transitions are determined by updating state["current_state"] in each node
    # LangGraph will automatically route to the node matching current_state

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
    
    cursor.execute("""
        INSERT OR REPLACE INTO agent_checkpoints (session_id, state_data)
        VALUES (?, ?)
    """, (session_id, state_json))
    
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
    
    cursor.execute("""
        SELECT state_data
        FROM agent_checkpoints
        WHERE session_id = ?
    """, (session_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None
