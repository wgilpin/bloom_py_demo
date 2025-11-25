"""Load sample syllabus into database.

This script loads the syllabus_sample.json file into the database.
Run this once after initializing the database.
"""

import json
from pathlib import Path

from bloom.database import init_database, load_syllabus_from_json
from bloom.models import SyllabusSchema


if __name__ == "__main__":
    # Initialize database first
    print("Initializing database...")
    init_database()
    
    # Load sample syllabus
    syllabus_path = Path(__file__).parent.parent / "syllabus_sample.json"
    print(f"Loading syllabus from {syllabus_path}...")
    
    # Read and validate JSON
    with open(syllabus_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate with Pydantic
    syllabus = SyllabusSchema(**data)
    
    # Load into database
    result = load_syllabus_from_json(syllabus.model_dump())
    
    print(f"✓ Loaded {result['topics_loaded']} topics with {result['subtopics_loaded']} subtopics")
    print("\n✓ Database is ready!")
    print("  You can now start the server with: uv run uvicorn bloom.main:app --reload")

