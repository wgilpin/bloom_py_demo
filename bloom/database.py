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
    
    Creates all 7 tables required for the tutoring system:
    - topics: High-level syllabus categories
    - subtopics: Specific learning units within topics
    - sessions: Tutoring sessions for subtopics
    - messages: Conversation history
    - calculator_history: Calculator operations log
    - progress: Per-subtopic completion tracking
    - agent_checkpoints: LangGraph state persistence
    
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
    """)
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {db_path}")


if __name__ == "__main__":
    # Allow direct execution for database setup
    init_database()

