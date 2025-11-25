"""Admin routes for Bloom tutoring system.

This module handles:
- Syllabus upload and validation
- Progress management (reset, export)
- Admin utilities
"""

import logging
import json
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import ValidationError

from bloom.models import SyllabusSchema
from bloom.database import load_syllabus_from_json
from bloom.main import DATABASE_PATH, templates

logger = logging.getLogger("bloom.routes.admin")


router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# Syllabus Management
# ============================================================================

@router.post("/syllabus/validate")
async def validate_syllabus(file: UploadFile = File(...)):
    """Pre-validate syllabus JSON without loading into database.
    
    Returns detailed validation errors if invalid.
    """
    logger.info(f"Validating syllabus file: {file.filename}")
    
    try:
        # Read file contents
        contents = await file.read()
        data = json.loads(contents)
        
        # Validate with Pydantic
        syllabus = SyllabusSchema(**data)
        
        # Count entities
        topics_count = len(syllabus.topics)
        subtopics_count = sum(len(topic.subtopics) for topic in syllabus.topics)
        
        logger.info(f"✓ Validation passed: {topics_count} topics, {subtopics_count} subtopics")
        
        return JSONResponse({
            "status": "valid",
            "title": syllabus.title,
            "topics_count": topics_count,
            "subtopics_count": subtopics_count,
            "topics": [
                {
                    "id": topic.id,
                    "name": topic.name,
                    "subtopics_count": len(topic.subtopics)
                }
                for topic in syllabus.topics
            ]
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"✗ Invalid JSON: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_type": "invalid_json",
                "message": f"Invalid JSON format: {str(e)}",
                "details": str(e)
            }
        )
    
    except ValidationError as e:
        logger.error(f"✗ Validation failed: {e}")
        errors = []
        for error in e.errors():
            loc = " → ".join(str(x) for x in error["loc"])
            errors.append({
                "field": loc,
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_type": "validation_error",
                "message": "Syllabus validation failed",
                "errors": errors
            }
        )
    
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_type": "server_error",
                "message": str(e)
            }
        )


@router.post("/syllabus/upload")
async def upload_syllabus(file: UploadFile = File(...)):
    """Upload and load syllabus JSON into database.
    
    Validates first, then replaces existing syllabus.
    Preserves student progress.
    """
    logger.info(f"Uploading syllabus file: {file.filename}")
    
    try:
        # Read and parse file
        contents = await file.read()
        data = json.loads(contents)
        
        # Validate with Pydantic
        logger.debug("Validating syllabus structure")
        syllabus = SyllabusSchema(**data)
        
        # Load into database
        logger.debug("Loading syllabus into database")
        result = load_syllabus_from_json(syllabus.model_dump(), DATABASE_PATH)
        
        logger.info(
            f"✓ Syllabus loaded successfully: "
            f"{result['topics_loaded']} topics, {result['subtopics_loaded']} subtopics"
        )
        
        return JSONResponse({
            "status": "success",
            "message": "Syllabus loaded successfully",
            "title": syllabus.title,
            "topics_loaded": result["topics_loaded"],
            "subtopics_loaded": result["subtopics_loaded"]
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"✗ Invalid JSON: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "invalid_json",
                "message": f"Invalid JSON format: {str(e)}"
            }
        )
    
    except ValidationError as e:
        logger.error(f"✗ Validation failed: {e}")
        errors = []
        for error in e.errors():
            loc = " → ".join(str(x) for x in error["loc"])
            errors.append({
                "field": loc,
                "message": error["msg"],
                "type": error["type"]
            })
        
        raise HTTPException(
            status_code=400,
            detail={
                "error_type": "validation_error",
                "message": "Syllabus validation failed",
                "errors": errors
            }
        )
    
    except Exception as e:
        logger.error(f"✗ Database error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "database_error",
                "message": str(e)
            }
        )


# ============================================================================
# Progress Management
# ============================================================================

@router.post("/progress/reset")
async def reset_progress():
    """Clear all progress and sessions (testing utility).
    
    WARNING: This deletes all student progress and session data!
    """
    from bloom.database import get_connection
    
    logger.warning("Resetting all progress and sessions")
    
    try:
        conn = get_connection(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Delete all progress and sessions
        cursor.execute("DELETE FROM progress")
        cursor.execute("DELETE FROM sessions")
        
        conn.commit()
        conn.close()
        
        logger.info("✓ All progress and sessions cleared")
        
        return JSONResponse({
            "status": "success",
            "message": "All progress and sessions have been cleared"
        })
        
    except Exception as e:
        logger.error(f"✗ Failed to reset progress: {e}")
        raise HTTPException(
            status_code=500,
            detail={"message": str(e)}
        )


# ============================================================================
# Admin Interface
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin dashboard for syllabus management."""
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )

