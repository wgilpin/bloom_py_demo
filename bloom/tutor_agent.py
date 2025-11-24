"""LangGraph tutoring agent with stateful conversation management.

This module defines the tutoring agent that manages the conversation flow
through different states: exposition, questioning, evaluation, diagnosis, and socratic.
"""

import json
import asyncio
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
)


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
    last_evaluation: Optional[dict]  # Store evaluation result {correct: bool, feedback: str}


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
    """Generate concept explanation for the current subtopic.

    This is typically the first state in a tutoring session.
    """
    prompt = f"""You are a patient, encouraging GCSE mathematics tutor helping a student learn {state['subtopic_name']}.

Your task: Provide a clear, engaging explanation of this topic.
- Use friendly, age-appropriate language (14-16 years old)
- Include a concrete example
- Keep it concise (2-3 paragraphs)
- End by asking if they have any questions before moving to practice

Do NOT ask a practice question yet - just explain the concept clearly."""

    try:
        explanation = await llm_client.generate(prompt)

        # Add tutor message to history
        state["messages"].append(
            {"role": "tutor", "content": explanation, "timestamp": datetime.utcnow().isoformat()}
        )

        # Transition to questioning after student responds
        state["current_state"] = "questioning"

    except Exception as e:
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
    """
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
        state["current_state"] = "evaluation"

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
    """
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
                    "content": f"✓ {evaluation['feedback']} Let's move on to another question!",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Next: ask another question
            state["current_state"] = "questioning"
        else:
            # Incorrect answer
            state["messages"].append(
                {
                    "role": "tutor",
                    "content": f"Not quite. {evaluation['feedback']}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Next: diagnose the error
            state["current_state"] = "diagnosis"

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
    """
    prompt = f"""You are a GCSE mathematics tutor analyzing a student's mistake.

Question: {state.get('last_question', 'N/A')}
Student's incorrect answer: {state['last_student_answer']}
Topic: {state['subtopic_name']}

Your task: Identify the likely misconception or error in their approach.
Respond in 1-2 sentences explaining what they might have misunderstood.
Be gentle and encouraging."""

    try:
        diagnosis = await llm_client.generate(prompt)

        state["messages"].append(
            {"role": "tutor", "content": diagnosis, "timestamp": datetime.utcnow().isoformat()}
        )

        # Next: provide Socratic guidance
        state["current_state"] = "socratic"

    except Exception as e:
        state["messages"].append(
            {
                "role": "tutor",
                "content": "Let me help you think through this step by step.",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        state["current_state"] = "socratic"

    return state


async def socratic_node(state: TutorState) -> TutorState:
    """Ask guiding questions to help student discover the right approach.

    Uses Socratic method - asking questions rather than giving answers.
    """
    prompt = f"""You are a GCSE mathematics tutor using the Socratic method.

Question: {state.get('last_question', 'N/A')}
Student's incorrect answer: {state['last_student_answer']}
Topic: {state['subtopic_name']}

Your task: Ask ONE guiding question to help them discover the right approach.
- Don't give the answer directly
- Ask a question that prompts them to think about a key step or concept
- Keep it simple and focused

Just ask the question - be encouraging."""

    try:
        hint_question = await llm_client.generate(prompt)

        state["messages"].append(
            {"role": "tutor", "content": hint_question, "timestamp": datetime.utcnow().isoformat()}
        )

        # Next: back to evaluation when student answers
        state["current_state"] = "evaluation"

    except Exception as e:
        state["messages"].append(
            {
                "role": "tutor",
                "content": "Think about the key steps in this problem. What should you do first?",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

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


def create_tutor_graph() -> StateGraph:
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
