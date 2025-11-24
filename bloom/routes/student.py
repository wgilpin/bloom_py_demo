"""Student-facing routes for Bloom tutoring system.

This module handles:
- Session creation and management
- Chat interface rendering
- Message handling and LLM interaction
- Error handling and retry logic
"""

import logging
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime

from bloom.models import (
    create_session,
    get_session,
    update_session,
    add_message,
    get_messages_for_session,
)
from bloom.tutor_agent import (
    TutorState,
    tutor_graph,
    save_agent_checkpoint,
    load_agent_checkpoint,
)
from bloom.main import DATABASE_PATH, templates

logger = logging.getLogger("bloom.routes")


router = APIRouter(prefix="", tags=["student"])


# ============================================================================
# Homepage (Temporary - will be replaced by full syllabus in Phase 4)
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Temporary homepage with hardcoded subtopics for testing Phase 3."""
    
    # Hardcoded sample topics for Phase 3 testing
    sample_topics = [
        {
            "id": 1,
            "name": "Number",
            "subtopics": [
                {"id": 101, "name": "Operations with Fractions"},
                {"id": 102, "name": "Percentages"},
                {"id": 103, "name": "Ratio and Proportion"},
            ]
        },
        {
            "id": 2,
            "name": "Algebra",
            "subtopics": [
                {"id": 201, "name": "Solving Linear Equations"},
                {"id": 202, "name": "Expanding and Factorising"},
            ]
        },
        {
            "id": 3,
            "name": "Geometry",
            "subtopics": [
                {"id": 301, "name": "Angles in Shapes"},
                {"id": 302, "name": "Pythagoras' Theorem"},
            ]
        }
    ]
    
    return templates.TemplateResponse(
        "homepage.html",
        {
            "request": request,
            "topics": sample_topics,
        }
    )


# ============================================================================
# Session Management
# ============================================================================

@router.post("/session/start")
async def start_session(
    request: Request,
    subtopic_id: int = Form(...),
    subtopic_name: str = Form(...),
):
    """Initialize a new tutoring session for a subtopic.
    
    Creates session, initializes agent state, and generates initial exposition.
    """
    logger.info(f"Starting session for subtopic_id={subtopic_id}, name='{subtopic_name}'")
    
    try:
        # Create new session in database
        logger.debug(f"Creating session in database for subtopic {subtopic_id}")
        session_id = create_session(subtopic_id, DATABASE_PATH)
        logger.info(f"Session created with ID: {session_id}")
        
        # Initialize agent state
        logger.debug("Initializing agent state")
        initial_state: TutorState = {
            "subtopic_id": subtopic_id,
            "subtopic_name": subtopic_name,
            "current_state": "exposition",
            "messages": [],
            "questions_correct": 0,
            "questions_attempted": 0,
            "calculator_visible": False,
            "last_student_answer": None,
            "calculator_history": [],
            "last_question": None,
            "last_evaluation": None,
        }
        
        # Run agent to generate initial exposition
        logger.info("Generating initial exposition via LLM")
        from bloom.tutor_agent import exposition_node
        state = await exposition_node(initial_state)
        logger.debug(f"Exposition generated, {len(state['messages'])} messages in state")
        
        # Save messages to database
        logger.debug("Saving messages to database")
        for msg in state["messages"]:
            add_message(
                session_id,
                msg["role"],
                msg["content"],
                DATABASE_PATH
            )
        
        # Save agent checkpoint
        logger.debug("Saving agent checkpoint")
        save_agent_checkpoint(session_id, state, DATABASE_PATH)
        
        logger.info(f"Session {session_id} initialized successfully")
        
        # Redirect to chat interface
        return templates.TemplateResponse(
            "chat.html",
            {
                "request": request,
                "session_id": session_id,
                "subtopic_name": subtopic_name,
                "calculator_visible": state["calculator_visible"],
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to start session: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start session: {str(e)}"
        )


# ============================================================================
# Chat Interface
# ============================================================================

@router.get("/chat", response_class=HTMLResponse)
async def get_chat(request: Request, session_id: int):
    """Render the chat interface for an active session."""
    
    # Get session details
    session = get_session(session_id, DATABASE_PATH)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Load agent state for calculator visibility
    state = load_agent_checkpoint(session_id, DATABASE_PATH)
    calculator_visible = state.get("calculator_visible", False) if state else False
    
    # Get subtopic name (we'll need to query this - simplified for now)
    subtopic_name = f"Subtopic {session['subtopic_id']}"
    
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "session_id": session_id,
            "subtopic_name": subtopic_name,
            "calculator_visible": calculator_visible,
        }
    )


@router.get("/chat/messages", response_class=HTMLResponse)
async def get_chat_messages(request: Request, session_id: int):
    """Return message history as HTML fragments for htmx."""
    
    messages = get_messages_for_session(session_id, DATABASE_PATH)
    
    html_parts = []
    for msg in messages:
        html_parts.append(templates.get_template("components/message.html").render(
            message=msg,
            request=request,
        ))
    
    return HTMLResponse(content="".join(html_parts))


# ============================================================================
# Message Handling
# ============================================================================

@router.post("/chat/message", response_class=HTMLResponse)
async def post_chat_message(
    request: Request,
    session_id: int = Form(...),
    message: str = Form(...),
):
    """Process student message and generate tutor response via agent."""
    
    logger.info(f"Received message for session {session_id}: '{message[:50]}...'")
    
    try:
        # Get session
        session = get_session(session_id, DATABASE_PATH)
        if not session:
            logger.error(f"Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Load agent state
        state = load_agent_checkpoint(session_id, DATABASE_PATH)
        if not state:
            logger.error(f"Agent state not found for session {session_id}")
            raise HTTPException(status_code=500, detail="Agent state not found")
        
        # Add student message to state and database
        state["messages"].append({
            "role": "student",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        add_message(session_id, "student", message, DATABASE_PATH)
        
        # Update last_student_answer for evaluation
        state["last_student_answer"] = message
        
        # Determine next node based on current state
        from bloom.tutor_agent import (
            questioning_node,
            evaluation_node,
            diagnosis_node,
            socratic_node,
            exposition_node,
        )
        
        current_state = state["current_state"]
        
        # Route to appropriate node
        if current_state == "exposition":
            # After exposition, student asks question or we move to questioning
            state = await questioning_node(state)
        elif current_state == "questioning":
            # Student answered, evaluate it
            state = await evaluation_node(state)
        elif current_state == "evaluation":
            # After evaluation, either question again or diagnose
            # (evaluation_node already transitions)
            pass
        elif current_state == "diagnosis":
            state = await socratic_node(state)
        elif current_state == "socratic":
            # Student tried again after hint
            state = await evaluation_node(state)
        
        # Update session counters
        update_session(
            session_id,
            questions_attempted=state["questions_attempted"],
            questions_correct=state["questions_correct"],
            db_path=DATABASE_PATH
        )
        
        # Save new tutor messages to database
        # Get only messages added since we last saved
        existing_count = len(get_messages_for_session(session_id, DATABASE_PATH))
        new_messages = state["messages"][existing_count:]
        
        for msg in new_messages:
            if msg["role"] == "tutor":  # Student message already added
                add_message(
                    session_id,
                    msg["role"],
                    msg["content"],
                    DATABASE_PATH
                )
        
        # Save updated agent checkpoint
        save_agent_checkpoint(session_id, state, DATABASE_PATH)
        
        # Return only the new tutor message(s) as HTML
        html_parts = []
        for msg in new_messages:
            html_parts.append(templates.get_template("components/message.html").render(
                message=msg,
                request=request,
            ))
        
        return HTMLResponse(content="".join(html_parts))
        
    except Exception as e:
        # Return error message as HTML
        error_msg = {
            "role": "tutor",
            "content": f"I'm having trouble right now. Please try again. (Error: {str(e)})",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return templates.get_template("components/message.html").render(
            message=error_msg,
            request=request,
        )


# ============================================================================
# Error Handling & Retry
# ============================================================================

@router.post("/chat/retry", response_class=HTMLResponse)
async def retry_last_message(request: Request, session_id: int = Form(...)):
    """Retry last LLM call if it failed (FR-018).
    
    Re-runs the agent from the last checkpoint with the same input.
    """
    
    try:
        # Load agent state
        state = load_agent_checkpoint(session_id, DATABASE_PATH)
        if not state:
            raise HTTPException(status_code=500, detail="No state to retry")
        
        # Re-run the current node
        from bloom.tutor_agent import (
            questioning_node,
            evaluation_node,
            diagnosis_node,
            socratic_node,
            exposition_node,
        )
        
        current_state = state["current_state"]
        
        if current_state == "exposition":
            state = await exposition_node(state)
        elif current_state == "questioning":
            state = await questioning_node(state)
        elif current_state == "evaluation":
            state = await evaluation_node(state)
        elif current_state == "diagnosis":
            state = await diagnosis_node(state)
        elif current_state == "socratic":
            state = await socratic_node(state)
        
        # Save new messages
        existing_count = len(get_messages_for_session(session_id, DATABASE_PATH))
        new_messages = state["messages"][existing_count:]
        
        for msg in new_messages:
            add_message(session_id, msg["role"], msg["content"], DATABASE_PATH)
        
        # Save checkpoint
        save_agent_checkpoint(session_id, state, DATABASE_PATH)
        
        # Return new messages as HTML
        html_parts = []
        for msg in new_messages:
            html_parts.append(templates.get_template("components/message.html").render(
                message=msg,
                request=request,
            ))
        
        return HTMLResponse(content="".join(html_parts))
        
    except Exception as e:
        error_msg = {
            "role": "tutor",
            "content": f"Retry failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return templates.get_template("components/message.html").render(
            message=error_msg,
            request=request,
        )

