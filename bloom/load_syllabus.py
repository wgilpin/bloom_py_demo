"""Load sample syllabus into database.

This script loads the syllabus_sample.json file into the database.
Run this once after initializing the database.
"""

import json
import sqlite3
from pathlib import Path

from bloom.database import get_connection, init_database
from bloom.models import SyllabusSchema


def load_syllabus_from_json(json_path: str, db_path: str = "bloom.db") -> None:
    """Load syllabus from JSON file into database.
    
    Args:
        json_path: Path to syllabus JSON file
        db_path: Path to database file
    """
    # Read and validate JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate with Pydantic
    syllabus = SyllabusSchema(**data)
    
    # Connect to database
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing syllabus (but preserve progress)
        cursor.execute("DELETE FROM topics")
        
        # Insert topics
        for topic in syllabus.topics:
            cursor.execute("""
                INSERT INTO topics (id, name, description)
                VALUES (?, ?, ?)
            """, (topic.id, topic.name, topic.description))
            
            # Insert subtopics
            for subtopic in topic.subtopics:
                cursor.execute("""
                    INSERT INTO subtopics (id, topic_id, name, description)
                    VALUES (?, ?, ?, ?)
                """, (subtopic.id, topic.id, subtopic.name, subtopic.description))
        
        conn.commit()
        print(f"✓ Loaded {len(syllabus.topics)} topics with {sum(len(t.subtopics) for t in syllabus.topics)} subtopics")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error loading syllabus: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Initialize database first
    print("Initializing database...")
    init_database()
    
    # Load sample syllabus
    syllabus_path = Path(__file__).parent.parent / "syllabus_sample.json"
    print(f"Loading syllabus from {syllabus_path}...")
    load_syllabus_from_json(str(syllabus_path))
    
    print("\n✓ Database is ready!")
    print("  You can now start the server with: uv run uvicorn bloom.main:app --reload")

