"""Pydantic models for data validation and schema enforcement.

This module defines schemas for:
- Syllabus loading and validation (JSON format)
- Agent state management (LangGraph state)
- Request/response data structures
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Syllabus Models (for JSON loading and validation)
# ============================================================================

class SubtopicSchema(BaseModel):
    """Schema for a single subtopic in the syllabus."""
    
    id: int = Field(..., gt=0, description="Unique subtopic ID (must be positive)")
    name: str = Field(..., min_length=1, description="Subtopic name")
    description: str = Field(default="", description="Optional subtopic description")
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Subtopic name cannot be empty or whitespace")
        return v.strip()


class TopicSchema(BaseModel):
    """Schema for a single topic in the syllabus."""
    
    id: int = Field(..., gt=0, description="Unique topic ID (must be positive)")
    name: str = Field(..., min_length=1, description="Topic name")
    description: str = Field(default="", description="Optional topic description")
    subtopics: list[SubtopicSchema] = Field(..., min_length=1, description="At least one subtopic required")
    
    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Ensure name is not just whitespace."""
        if not v.strip():
            raise ValueError("Topic name cannot be empty or whitespace")
        return v.strip()


class SyllabusSchema(BaseModel):
    """Schema for the complete GCSE mathematics syllabus."""
    
    title: str = Field(..., min_length=1, description="Syllabus title")
    topics: list[TopicSchema] = Field(..., min_length=1, description="At least one topic required")
    
    @field_validator('topics')
    @classmethod
    def validate_unique_ids(cls, topics: list[TopicSchema]) -> list[TopicSchema]:
        """Ensure all topic and subtopic IDs are unique."""
        # Check unique topic IDs
        topic_ids = [t.id for t in topics]
        if len(topic_ids) != len(set(topic_ids)):
            duplicates = [tid for tid in topic_ids if topic_ids.count(tid) > 1]
            raise ValueError(f"Duplicate topic IDs found: {set(duplicates)}")
        
        # Check unique subtopic IDs across all topics
        subtopic_ids = [s.id for t in topics for s in t.subtopics]
        if len(subtopic_ids) != len(set(subtopic_ids)):
            duplicates = [sid for sid in subtopic_ids if subtopic_ids.count(sid) > 1]
            raise ValueError(f"Duplicate subtopic IDs found: {set(duplicates)}")
        
        return topics


# ============================================================================
# Agent State Models (for LangGraph)
# ============================================================================

class SessionState(BaseModel):
    """LangGraph agent state for tutoring sessions.
    
    This represents the current state of the tutoring agent and is used
    by LangGraph to manage the conversation flow.
    """
    
    subtopic_id: int = Field(..., description="Current subtopic being studied")
    current_state: Literal["exposition", "questioning", "evaluation", "diagnosis", "socratic"] = Field(
        default="exposition",
        description="Current tutoring state node"
    )
    messages: list[dict] = Field(
        default_factory=list,
        description="Chat history (role, content pairs)"
    )
    questions_correct: int = Field(default=0, ge=0, description="Count of correct answers")
    questions_attempted: int = Field(default=0, ge=0, description="Count of questions attempted")
    calculator_visible: bool = Field(default=False, description="Whether calculator should be shown")
    last_student_answer: Optional[str] = Field(default=None, description="Most recent student answer")
    calculator_history: list[dict] = Field(
        default_factory=list,
        description="Calculator operations (expression, result pairs)"
    )
    
    @field_validator('questions_correct')
    @classmethod
    def correct_not_exceed_attempted(cls, v: int, info) -> int:
        """Ensure correct answers don't exceed attempted."""
        attempted = info.data.get('questions_attempted', 0)
        if v > attempted:
            raise ValueError(f"questions_correct ({v}) cannot exceed questions_attempted ({attempted})")
        return v


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message."""
    
    message: str = Field(..., min_length=1, max_length=2000, description="Student message")
    session_id: int = Field(..., gt=0, description="Active session ID")


class StartSessionRequest(BaseModel):
    """Request body for starting a new tutoring session."""
    
    subtopic_id: int = Field(..., gt=0, description="Subtopic to study")


class CalculatorRequest(BaseModel):
    """Request body for logging calculator operations."""
    
    session_id: int = Field(..., gt=0, description="Active session ID")
    expression: str = Field(..., min_length=1, description="Calculator expression")
    result: str = Field(..., description="Calculation result or 'Error'")

