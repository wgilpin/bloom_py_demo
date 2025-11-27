"""Database schema and initialization for Bloom GCSE Mathematics Tutor.

This module provides SQLite database setup and connection management.
All timestamps use ISO8601 format.
"""

import os
import sqlite3
from typing import Optional, TypedDict

# Load MAX_IMAGE_SIZE from environment (used for image validation)
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", "5242880"))  # 5MB in bytes for 2K resolution images


class SyllabusLoadResultDict(TypedDict):
    """Type definition for syllabus load operation results."""
    topics_loaded: int
    subtopics_loaded: int


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
    
    Creates all 9 tables required for the tutoring system:
    - topics: High-level syllabus categories
    - subtopics: Specific learning units within topics
    - sessions: Tutoring sessions for subtopics
    - messages: Conversation history
    - calculator_history: Calculator operations log
    - progress: Per-subtopic completion tracking
    - agent_checkpoints: LangGraph state persistence
    - cached_expositions: Cached lesson expositions for cost reduction
    - cached_images: Cached whiteboard images for visual learning
    
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
        
        -- Cached whiteboard images for visual learning
        CREATE TABLE IF NOT EXISTS cached_images (
            subtopic_id INTEGER PRIMARY KEY,
            image_data BLOB NOT NULL,
            image_format TEXT NOT NULL DEFAULT 'PNG',
            generated_at TEXT NOT NULL,
            prompt_version TEXT NOT NULL DEFAULT 'v1',
            model_identifier TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        );
    """)
    
    conn.commit()
    conn.close()
    # Note: Logging handled by main.py during startup


def load_syllabus_from_json(syllabus_data: dict, db_path: str = "bloom.db") -> SyllabusLoadResultDict:
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
        model_identifier: LLM model used (e.g., "gpt-4", "claude-3-5-sonnet-20241022")
        db_path: Path to database file
    """
    from datetime import datetime
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO cached_expositions 
        (subtopic_id, exposition_content, generated_at, model_identifier)
        VALUES (?, ?, ?, ?)
    """, (subtopic_id, content, datetime.utcnow().isoformat(), model_identifier))
    
    conn.commit()
    conn.close()


# ============================================================================
# Image Cache Functions (spec 003)
# ============================================================================


def validate_image_data(image_data: bytes, max_size: int = MAX_IMAGE_SIZE) -> bool:
    """Validate image data meets technical requirements.
    
    Performs technical validation only:
    - Checks file size is under max_size limit
    - Validates image is valid PNG or JPEG format
    - Verifies image is not corrupted
    
    Args:
        image_data: Binary image data to validate
        max_size: Maximum allowed file size in bytes (default: 5MB)
        
    Returns:
        True if image passes all validation checks, False otherwise
    """
    import logging
    from PIL import Image
    import io
    
    logger = logging.getLogger("bloom.database")
    
    # Check file size
    if len(image_data) > max_size:
        logger.warning(f"Image validation failed: size {len(image_data)} exceeds max {max_size}")
        return False
    
    # Validate image format and integrity
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Verify format is PNG or JPEG (Gemini API may return either)
        if img.format not in ['PNG', 'JPEG']:
            logger.warning(f"Image validation failed: format is {img.format}, expected PNG or JPEG")
            return False
        
        # Verify image is not corrupted
        img.verify()
        logger.debug(f"Image validated successfully: {len(image_data)} bytes, {img.size} pixels, format={img.format}")
        return True
        
    except Exception as e:
        logger.warning(f"Image validation failed: {str(e)}")
        return False


def get_cached_image(subtopic_id: int, db_path: str = "bloom.db") -> Optional[dict]:
    """Retrieve cached whiteboard image for a subtopic.
    
    Args:
        subtopic_id: Subtopic ID to look up
        db_path: Path to database file
        
    Returns:
        Dict with image data and metadata or None if not cached
        Keys: {subtopic_id, image_data, image_format, generated_at, 
               prompt_version, model_identifier, file_size}
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT subtopic_id, image_data, image_format, generated_at, 
               prompt_version, model_identifier, file_size
        FROM cached_images
        WHERE subtopic_id = ?
    """, (subtopic_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "subtopic_id": row["subtopic_id"],
            "image_data": row["image_data"],
            "image_format": row["image_format"],
            "generated_at": row["generated_at"],
            "prompt_version": row["prompt_version"],
            "model_identifier": row["model_identifier"],
            "file_size": row["file_size"],
        }
    return None


def save_cached_image(
    subtopic_id: int,
    image_data: bytes,
    model_identifier: str,
    prompt_version: str = "v1",
    db_path: str = "bloom.db"
) -> None:
    """Save generated whiteboard image to cache.
    
    Args:
        subtopic_id: Subtopic ID this image belongs to
        image_data: Binary image data (PNG or JPEG)
        model_identifier: Model used (e.g., "gemini-3-pro-image")
        prompt_version: Version of prompt template used (default: "v1")
        db_path: Path to database file
    """
    from datetime import datetime
    import logging
    from PIL import Image
    import io
    
    logger = logging.getLogger("bloom.database")
    file_size = len(image_data)
    
    # Detect actual image format
    try:
        img = Image.open(io.BytesIO(image_data))
        image_format = img.format  # Will be 'PNG' or 'JPEG'
    except Exception:
        image_format = 'PNG'  # Default fallback
    
    # T095: Log file size for storage monitoring
    logger.debug(
        f"💾 Saving cached image | "
        f"subtopic_id={subtopic_id} | "
        f"size={file_size} bytes | "
        f"size_mb={file_size / 1048576:.2f} MB | "
        f"format={image_format} | "
        f"model={model_identifier}"
    )
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO cached_images 
        (subtopic_id, image_data, image_format, generated_at, 
         prompt_version, model_identifier, file_size)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        subtopic_id, 
        image_data, 
        image_format,
        datetime.utcnow().isoformat(), 
        prompt_version,
        model_identifier,
        file_size
    ))
    
    conn.commit()
    conn.close()
    
    logger.debug(f"✓ Image saved to cache | subtopic_id={subtopic_id} | format={image_format}")


def delete_cached_image(subtopic_id: int, db_path: str = "bloom.db") -> None:
    """Delete cached image for a specific subtopic.
    
    Args:
        subtopic_id: Subtopic ID whose image should be deleted
        db_path: Path to database file
    """
    import logging
    
    logger = logging.getLogger("bloom.database")
    
    # Get file size before deletion for logging
    cached = get_cached_image(subtopic_id, db_path)
    file_size = cached.get("file_size", 0) if cached else 0
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM cached_images 
        WHERE subtopic_id = ?
    """, (subtopic_id,))
    
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    if deleted:
        logger.info(
            f"🗑️ Deleted cached image | "
            f"subtopic_id={subtopic_id} | "
            f"freed_size={file_size} bytes"
        )


def delete_all_cached_images(db_path: str = "bloom.db") -> int:
    """Delete all cached images from the database.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Number of images deleted
    """
    import logging
    
    logger = logging.getLogger("bloom.database")
    
    # Get total size before deletion for logging
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), SUM(file_size) FROM cached_images")
    row = cursor.fetchone()
    count_before = row[0] if row[0] else 0
    total_size = row[1] if row[1] else 0
    
    cursor.execute("DELETE FROM cached_images")
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    if deleted_count > 0:
        logger.info(
            f"🗑️ Deleted ALL cached images | "
            f"count={deleted_count} | "
            f"freed_size={total_size} bytes | "
            f"freed_size_mb={total_size / 1048576:.2f} MB"
        )
    
    return deleted_count


if __name__ == "__main__":
    # Allow direct execution for database setup
    init_database()

