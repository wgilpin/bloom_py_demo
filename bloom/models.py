"""Pydantic models for data validation and schema enforcement.

This module defines schemas for:
- Syllabus loading and validation (JSON format)
- Agent state management (LangGraph state)
- Request/response data structures
"""

from typing import Literal, Optional, TypedDict

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Syllabus Models (for JSON loading and validation)
# ============================================================================


class SubtopicSchema(BaseModel):
    """Schema for a single subtopic in the syllabus."""

    id: int = Field(..., gt=0, description="Unique subtopic ID (must be positive)")
    name: str = Field(..., min_length=1, description="Subtopic name")
    description: str = Field(default="", description="Optional subtopic description")

    @field_validator("name")
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
    subtopics: list[SubtopicSchema] = Field(
        ..., min_length=1, description="At least one subtopic required"
    )

    @field_validator("name")
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

    @field_validator("topics")
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


class SessionStateMessageDict(TypedDict):
    """Type definition for messages in SessionState (Pydantic model)."""
    role: str
    content: str


class SessionStateCalculatorDict(TypedDict):
    """Type definition for calculator history in SessionState (Pydantic model)."""
    expression: str
    result: str


class SessionState(BaseModel):
    """LangGraph agent state for tutoring sessions.

    This represents the current state of the tutoring agent and is used
    by LangGraph to manage the conversation flow.
    """

    subtopic_id: int = Field(..., description="Current subtopic being studied")
    current_state: Literal["exposition", "questioning", "evaluation", "diagnosis", "socratic"] = (
        Field(default="exposition", description="Current tutoring state node")
    )
    messages: list[SessionStateMessageDict] = Field(
        default_factory=list, description="Chat history (role, content pairs)"
    )
    questions_correct: int = Field(default=0, ge=0, description="Count of correct answers")
    questions_attempted: int = Field(default=0, ge=0, description="Count of questions attempted")
    calculator_visible: bool = Field(
        default=False, description="Whether calculator should be shown"
    )
    last_student_answer: Optional[str] = Field(
        default=None, description="Most recent student answer"
    )
    calculator_history: list[SessionStateCalculatorDict] = Field(
        default_factory=list, description="Calculator operations (expression, result pairs)"
    )
    hints_given: int = Field(
        default=0, ge=0, description="Count of Socratic hints given for current question"
    )

    @field_validator("questions_correct")
    @classmethod
    def correct_not_exceed_attempted(cls, v: int, info) -> int:
        """Ensure correct answers don't exceed attempted."""
        attempted = info.data.get("questions_attempted", 0)
        if v > attempted:
            raise ValueError(
                f"questions_correct ({v}) cannot exceed questions_attempted ({attempted})"
            )
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


# ============================================================================
# Database Helper Functions
# ============================================================================

from datetime import datetime, timezone

from bloom.database import get_connection


# TypedDict definitions for database return types
class SessionDict(TypedDict):
    """Type definition for session database records."""
    id: int
    subtopic_id: int
    state: str
    created_at: str
    updated_at: str
    questions_attempted: int
    questions_correct: int


class MessageDict(TypedDict):
    """Type definition for message database records."""
    id: int
    role: str
    content: str
    timestamp: str


class ProgressDict(TypedDict):
    """Type definition for progress database records."""
    subtopic_id: int
    questions_attempted: int
    questions_correct: int
    is_complete: bool
    last_accessed: str | None


class ProgressUpdateDict(TypedDict):
    """Type definition for progress update results."""
    questions_attempted: int
    questions_correct: int
    is_complete: bool


class TopicProgressDict(TypedDict):
    """Type definition for aggregated topic progress."""
    topic_id: int
    topic_name: str
    total_subtopics: int
    completed_subtopics: int
    completion_percent: float


class SyllabusLoadResultDict(TypedDict):
    """Type definition for syllabus load operation results."""
    topics_loaded: int
    subtopics_loaded: int


class CachedImage(TypedDict):
    """Type definition for cached whiteboard image records.
    
    Stores generated whiteboard-style PNG images for subtopic expositions.
    """
    subtopic_id: int
    image_data: bytes
    image_format: str
    generated_at: str
    prompt_version: str
    model_identifier: str
    file_size: int


def create_session(subtopic_id: int, db_path: str = "bloom.db") -> int:
    """Create a new tutoring session.

    Args:
        subtopic_id: ID of the subtopic to study
        db_path: Path to database file

    Returns:
        session_id: ID of the created session
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """
        INSERT INTO sessions (subtopic_id, state, created_at, updated_at)
        VALUES (?, 'active', ?, ?)
    """,
        (subtopic_id, now, now),
    )

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    if session_id is None:
        raise RuntimeError("Failed to create session: lastrowid returned None")
    
    return session_id


def get_session(session_id: int, db_path: str = "bloom.db") -> Optional[SessionDict]:
    """Get session details by ID.

    Args:
        session_id: Session ID to retrieve
        db_path: Path to database file

    Returns:
        Session data as dict or None if not found
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, subtopic_id, state, created_at, updated_at,
               questions_attempted, questions_correct
        FROM sessions
        WHERE id = ?
    """,
        (session_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row["id"],
            "subtopic_id": row["subtopic_id"],
            "state": row["state"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "questions_attempted": row["questions_attempted"],
            "questions_correct": row["questions_correct"],
        }
    return None


def update_session(
    session_id: int,
    questions_attempted: Optional[int] = None,
    questions_correct: Optional[int] = None,
    state: Optional[str] = None,
    db_path: str = "bloom.db",
) -> None:
    """Update session counters and state.

    Args:
        session_id: Session ID to update
        questions_attempted: New attempted count (or None to skip)
        questions_correct: New correct count (or None to skip)
        state: New state (or None to skip)
        db_path: Path to database file
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    updates: list[str] = []
    params: list[int | str] = []

    if questions_attempted is not None:
        updates.append("questions_attempted = ?")
        params.append(questions_attempted)

    if questions_correct is not None:
        updates.append("questions_correct = ?")
        params.append(questions_correct)

    if state is not None:
        updates.append("state = ?")
        params.append(state)

    # Always update timestamp
    updates.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())

    params.append(session_id)

    cursor.execute(
        f"""
        UPDATE sessions
        SET {', '.join(updates)}
        WHERE id = ?
    """,
        params,
    )

    conn.commit()
    conn.close()


def add_message(session_id: int, role: str, content: str, db_path: str = "bloom.db") -> int:
    """Add a message to session history.

    Args:
        session_id: Session ID
        role: 'student' or 'tutor'
        content: Message text
        db_path: Path to database file

    Returns:
        message_id: ID of the created message
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages (session_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
    """,
        (session_id, role, content, datetime.now(timezone.utc).isoformat()),
    )

    message_id = cursor.lastrowid
    conn.commit()
    conn.close()

    if message_id is None:
        raise RuntimeError("Failed to create message: lastrowid returned None")
    
    return message_id


def get_messages_for_session(session_id: int, db_path: str = "bloom.db") -> list[MessageDict]:
    """Get all messages for a session, ordered by timestamp.

    Args:
        session_id: Session ID
        db_path: Path to database file

    Returns:
        List of message dicts with role, content, timestamp
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, role, content, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """,
        (session_id,),
    )

    messages: list[MessageDict] = []
    for row in cursor.fetchall():
        msg: MessageDict = {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "timestamp": row["timestamp"],
        }
        messages.append(msg)

    conn.close()
    return messages


# ============================================================================
# Progress Tracking Functions
# ============================================================================


def update_progress(
    subtopic_id: int, is_correct: bool, completion_threshold: int = 3, db_path: str = "bloom.db"
) -> ProgressUpdateDict:
    """Update progress for a subtopic after answering a question.

    Args:
        subtopic_id: Subtopic ID to update
        is_correct: Whether the answer was correct
        completion_threshold: Number of correct answers needed for completion
        db_path: Path to database file

    Returns:
        Updated progress dict with keys: questions_attempted, questions_correct, is_complete
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()
    correct_increment = 1 if is_correct else 0

    # Insert or update progress
    cursor.execute(
        """
        INSERT INTO progress (subtopic_id, questions_attempted, questions_correct, is_complete, last_accessed)
        VALUES (?, 1, ?, 0, ?)
        ON CONFLICT(subtopic_id) DO UPDATE SET
            questions_attempted = questions_attempted + 1,
            questions_correct = questions_correct + ?,
            is_complete = CASE WHEN questions_correct + ? >= ? THEN 1 ELSE 0 END,
            last_accessed = ?
    """,
        (
            subtopic_id,
            correct_increment,
            now,
            correct_increment,
            correct_increment,
            completion_threshold,
            now,
        ),
    )

    # Fetch updated progress
    cursor.execute(
        """
        SELECT questions_attempted, questions_correct, is_complete
        FROM progress
        WHERE subtopic_id = ?
    """,
        (subtopic_id,),
    )

    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return {
        "questions_attempted": row["questions_attempted"],
        "questions_correct": row["questions_correct"],
        "is_complete": bool(row["is_complete"]),
    }


def get_progress_for_subtopic(subtopic_id: int, db_path: str = "bloom.db") -> Optional[ProgressDict]:
    """Get progress data for a specific subtopic.

    Args:
        subtopic_id: Subtopic ID
        db_path: Path to database file

    Returns:
        Progress dict or None if no progress exists
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT subtopic_id, questions_attempted, questions_correct, is_complete, last_accessed
        FROM progress
        WHERE subtopic_id = ?
    """,
        (subtopic_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "subtopic_id": row["subtopic_id"],
            "questions_attempted": row["questions_attempted"],
            "questions_correct": row["questions_correct"],
            "is_complete": bool(row["is_complete"]),
            "last_accessed": row["last_accessed"],
        }
    return None


def aggregate_topic_progress(db_path: str = "bloom.db") -> list[TopicProgressDict]:
    """Aggregate progress statistics at the topic level.

    Args:
        db_path: Path to database file

    Returns:
        List of topic progress dicts with keys:
            - topic_id, topic_name, total_subtopics, completed_subtopics, completion_percent
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
            t.id AS topic_id,
            t.name AS topic_name,
            COUNT(DISTINCT st.id) AS total_subtopics,
            COALESCE(SUM(p.is_complete), 0) AS completed_subtopics,
            CASE 
                WHEN COUNT(DISTINCT st.id) > 0 
                THEN CAST(COALESCE(SUM(p.is_complete), 0) AS FLOAT) / COUNT(DISTINCT st.id) * 100
                ELSE 0
            END AS completion_percent
        FROM topics t
        JOIN subtopics st ON st.topic_id = t.id
        LEFT JOIN progress p ON p.subtopic_id = st.id
        GROUP BY t.id, t.name
        ORDER BY t.id
    """
    )

    results: list[TopicProgressDict] = []
    for row in cursor.fetchall():
        progress: TopicProgressDict = {
            "topic_id": row["topic_id"],
            "topic_name": row["topic_name"],
            "total_subtopics": row["total_subtopics"],
            "completed_subtopics": row["completed_subtopics"],
            "completion_percent": round(row["completion_percent"], 1),
        }
        results.append(progress)

    conn.close()
    return results
