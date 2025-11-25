"""Database schema and initialization for Bloom GCSE Mathematics Tutor.

This module provides SQLite database setup and connection management.
All timestamps use ISO8601 format.
"""

import sqlite3
from pathlib import Path
from typing import Optional


def get_connection(db_path: str = "bloom.db") -> sqlite3.Connection:
    """Get a database connection with foreign keys enabled.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        SQLite connection object
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_database(db_path: str = "bloom.db") -> None:
    """Initialize database schema if not exists.
    
    Creates all 8 tables required for the tutoring system:
    - topics: High-level syllabus categories
    - subtopics: Specific learning units within topics
    - sessions: Tutoring sessions for subtopics
    - messages: Conversation history
    - calculator_history: Calculator operations log
    - progress: Per-subtopic completion tracking
    - agent_checkpoints: LangGraph state persistence
    - cached_expositions: Cached lesson expositions for API cost reduction
    
    Args:
        db_path: Path to SQLite database file
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Create all tables
    cursor.executescript("""
        -- Syllabus structure: Topics (high-level categories)
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );
        
        -- Syllabus structure: Subtopics (specific learning units)
        CREATE TABLE IF NOT EXISTS subtopics (
            id INTEGER PRIMARY KEY,
            topic_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_subtopics_topic_id ON subtopics(topic_id);
        
        -- Tutoring sessions
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id INTEGER NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('active', 'completed', 'abandoned')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            questions_attempted INTEGER NOT NULL DEFAULT 0,
            questions_correct INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(state);
        CREATE INDEX IF NOT EXISTS idx_sessions_subtopic ON sessions(subtopic_id);
        
        -- Conversation history
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'tutor')),
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
        
        -- Calculator operation logs
        CREATE TABLE IF NOT EXISTS calculator_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            expression TEXT NOT NULL,
            result TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_calculator_session ON calculator_history(session_id);
        
        -- Student progress tracking
        CREATE TABLE IF NOT EXISTS progress (
            subtopic_id INTEGER PRIMARY KEY,
            questions_attempted INTEGER NOT NULL DEFAULT 0,
            questions_correct INTEGER NOT NULL DEFAULT 0,
            is_complete BOOLEAN NOT NULL DEFAULT 0,
            last_accessed TEXT,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        );
        
        -- LangGraph agent state checkpoints for session resumption
        CREATE TABLE IF NOT EXISTS agent_checkpoints (
            session_id INTEGER PRIMARY KEY,
            state_data TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
        
        -- Cached lesson expositions for API cost reduction
        CREATE TABLE IF NOT EXISTS cached_expositions (
            subtopic_id INTEGER PRIMARY KEY,
            exposition_content TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            model_identifier TEXT NOT NULL,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        );
    """)
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {db_path}")


def load_syllabus_from_json(syllabus_data: dict, db_path: str = "bloom.db") -> dict:
    """Load syllabus topics and subtopics from validated JSON data.
    
    This function REPLACES existing topics/subtopics but PRESERVES progress data.
    
    Args:
        syllabus_data: Validated syllabus dictionary (already validated by Pydantic)
        db_path: Path to database file
        
    Returns:
        Dictionary with counts: {"topics_loaded": int, "subtopics_loaded": int}
        
    Raises:
        sqlite3.IntegrityError: If database constraints are violated
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing syllabus data (cascade will handle subtopics)
        # Note: Progress table is NOT deleted - students keep their progress
        cursor.execute("DELETE FROM topics")
        
        topics_count = 0
        subtopics_count = 0
        
        # Insert topics and subtopics from JSON
        for topic in syllabus_data["topics"]:
            cursor.execute(
                "INSERT INTO topics (id, name, description) VALUES (?, ?, ?)",
                (topic["id"], topic["name"], topic.get("description", ""))
            )
            topics_count += 1
            
            # Insert subtopics for this topic
            for subtopic in topic["subtopics"]:
                cursor.execute(
                    "INSERT INTO subtopics (id, topic_id, name, description) VALUES (?, ?, ?, ?)",
                    (subtopic["id"], topic["id"], subtopic["name"], subtopic.get("description", ""))
                )
                subtopics_count += 1
        
        conn.commit()
        return {
            "topics_loaded": topics_count,
            "subtopics_loaded": subtopics_count
        }
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_cached_exposition(subtopic_id: int, db_path: str = "bloom.db") -> Optional[dict]:
    """Retrieve cached exposition for a subtopic.
    
    Args:
        subtopic_id: Subtopic ID to look up
        db_path: Path to database file
        
    Returns:
        Dict with keys {exposition_content, generated_at, model_identifier} or None if not cached
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT exposition_content, generated_at, model_identifier
        FROM cached_expositions
        WHERE subtopic_id = ?
    """, (subtopic_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "exposition_content": row["exposition_content"],
            "generated_at": row["generated_at"],
            "model_identifier": row["model_identifier"],
        }
    return None


def save_cached_exposition(
    subtopic_id: int,
    content: str,
    model_identifier: str,
    db_path: str = "bloom.db"
) -> None:
    """Save generated exposition to cache.
    
    Args:
        subtopic_id: Subtopic ID this exposition belongs to
        content: Full text of the exposition
        model_identifier: LLM model used (e.g., "gpt-4")
        db_path: Path to database file
    """
    from datetime import datetime, UTC
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO cached_expositions 
        (subtopic_id, exposition_content, generated_at, model_identifier)
        VALUES (?, ?, ?, ?)
    """, (subtopic_id, content, datetime.now(UTC).isoformat(), model_identifier))
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Allow direct execution for database setup
    init_database()

