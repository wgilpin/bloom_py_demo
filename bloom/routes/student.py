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
    save_agent_checkpoint,
    load_agent_checkpoint,
)
from bloom.main import DATABASE_PATH, templates

logger = logging.getLogger("bloom.routes")


router = APIRouter(prefix="", tags=["student"])


# ============================================================================
# Homepage & Syllabus Navigation
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Homepage with syllabus navigation and session resumption check."""
    from bloom.database import get_connection
    
    # Check for active session
    conn = get_connection(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, subtopic_id, created_at, updated_at
        FROM sessions
        WHERE state = 'active'
        ORDER BY updated_at DESC
        LIMIT 1
    """)
    
    active_session = cursor.fetchone()
    
    if active_session:
        # Get subtopic name for the active session
        cursor.execute("""
            SELECT st.name, t.name as topic_name
            FROM subtopics st
            JOIN topics t ON t.id = st.topic_id
            WHERE st.id = ?
        """, (active_session["subtopic_id"],))
        
        subtopic_info = cursor.fetchone()
        
        conn.close()
        
        # Show resumption prompt
        return templates.TemplateResponse(
            "homepage.html",
            {
                "request": request,
                "active_session": {
                    "id": active_session["id"],
                    "subtopic_id": active_session["subtopic_id"],
                    "subtopic_name": subtopic_info["name"] if subtopic_info else "Unknown",
                    "topic_name": subtopic_info["topic_name"] if subtopic_info else "Unknown",
                    "updated_at": active_session["updated_at"],
                }
            }
        )
    
    conn.close()
    
    # No active session, show syllabus
    return templates.TemplateResponse(
        "homepage.html",
        {
            "request": request,
            "active_session": None,
        }
    )


@router.get("/syllabus", response_class=HTMLResponse)
async def get_syllabus(request: Request):
    """Get full syllabus with progress data (HTML for htmx)."""
    from bloom.database import get_connection
    
    conn = get_connection(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Load topics with subtopics and progress
    cursor.execute("""
        SELECT 
            t.id AS topic_id,
            t.name AS topic_name,
            t.description AS topic_description,
            st.id AS subtopic_id,
            st.name AS subtopic_name,
            st.description AS subtopic_description,
            COALESCE(p.questions_correct, 0) AS questions_correct,
            COALESCE(p.questions_attempted, 0) AS questions_attempted,
            COALESCE(p.is_complete, 0) AS is_complete
        FROM topics t
        JOIN subtopics st ON st.topic_id = t.id
        LEFT JOIN progress p ON p.subtopic_id = st.id
        ORDER BY t.id, st.id
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Group by topics
    topics_dict = {}
    for row in rows:
        topic_id = row["topic_id"]
        
        if topic_id not in topics_dict:
            topics_dict[topic_id] = {
                "id": topic_id,
                "name": row["topic_name"],
                "description": row["topic_description"],
                "subtopics": []
            }
        
        topics_dict[topic_id]["subtopics"].append({
            "id": row["subtopic_id"],
            "name": row["subtopic_name"],
            "description": row["subtopic_description"],
            "questions_correct": row["questions_correct"],
            "questions_attempted": row["questions_attempted"],
            "is_complete": bool(row["is_complete"]),
        })
    
    topics = list(topics_dict.values())
    
    return templates.TemplateResponse(
        "syllabus.html",
        {
            "request": request,
            "topics": topics
        }
    )


@router.get("/progress")
async def get_progress():
    """Get progress summary for all topics."""
    from bloom.models import aggregate_topic_progress
    
    topic_progress = aggregate_topic_progress(DATABASE_PATH)
    
    return {
        "topic_progress": topic_progress
    }


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
            "hints_given": 0,
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


@router.post("/session/resume")
async def resume_session(request: Request, session_id: int = Form(...)):
    """Resume an active session from checkpoint (FR-020).
    
    Restores agent state and redirects to chat interface.
    """
    logger.info(f"Resuming session {session_id}")
    
    try:
        # Verify session exists and is active
        session = get_session(session_id, DATABASE_PATH)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session["state"] != "active":
            raise HTTPException(status_code=400, detail="Session is not active")
        
        # Load agent checkpoint
        state = load_agent_checkpoint(session_id, DATABASE_PATH)
        if not state:
            raise HTTPException(status_code=500, detail="Agent state not found")
        
        # Get subtopic name
        from bloom.database import get_connection
        conn = get_connection(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT st.name
            FROM subtopics st
            WHERE st.id = ?
        """, (session["subtopic_id"],))
        
        subtopic_row = cursor.fetchone()
        conn.close()
        
        subtopic_name = subtopic_row["name"] if subtopic_row else f"Subtopic {session['subtopic_id']}"
        
        logger.info(f"Session {session_id} resumed successfully")
        
        # Redirect to chat interface
        return templates.TemplateResponse(
            "chat.html",
            {
                "request": request,
                "session_id": session_id,
                "subtopic_name": subtopic_name,
                "calculator_visible": state.get("calculator_visible", False),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume session: {str(e)}"
        )


@router.post("/session/abandon")
async def abandon_session(session_id: int = Form(None)):
    """Abandon active session(s) (Start Fresh action).
    
    If session_id is provided, abandons that specific session.
    If session_id is None/not provided, abandons ALL active sessions.
    Marks session(s) as abandoned without deleting data.
    """
    from bloom.database import get_connection
    
    try:
        conn = get_connection(DATABASE_PATH)
        cursor = conn.cursor()
        
        if session_id:
            # Abandon specific session
            logger.info(f"Abandoning session {session_id}")
            
            # Verify session exists
            session = get_session(session_id, DATABASE_PATH)
            if not session:
                conn.close()
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Mark session as abandoned
            update_session(session_id, state="abandoned", db_path=DATABASE_PATH)
            logger.info(f"Session {session_id} marked as abandoned")
            abandoned_count = 1
        else:
            # Abandon ALL active sessions
            logger.info("Abandoning all active sessions")
            
            cursor.execute("""
                UPDATE sessions
                SET state = 'abandoned', updated_at = ?
                WHERE state = 'active'
            """, (datetime.utcnow().isoformat(),))
            
            abandoned_count = cursor.rowcount
            conn.commit()
            logger.info(f"Abandoned {abandoned_count} active session(s)")
        
        conn.close()
        
        return {
            "status": "success", 
            "message": f"Abandoned {abandoned_count} session(s)",
            "count": abandoned_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to abandon session(s): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to abandon session(s): {str(e)}"
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
    
    # Get subtopic_id for image loading (spec 003)
    session = get_session(session_id, DATABASE_PATH)
    subtopic_id = session.get("subtopic_id") if session else None
    
    html_parts = []
    for msg in messages:
        html_parts.append(templates.get_template("components/message.html").render(
            message=msg,
            subtopic_id=subtopic_id,
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
        
        # Get message count BEFORE adding student message (for rendering later)
        existing_db_count = len(get_messages_for_session(session_id, DATABASE_PATH))
        
        # Add student message to state and database
        state["messages"].append({
            "role": "student",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        add_message(session_id, "student", message, DATABASE_PATH)
        
        # Update last_student_answer for evaluation
        state["last_student_answer"] = message
        
        # Import nodes and routing functions
        from bloom.tutor_agent import (
            exposition_node,
            questioning_node,
            evaluation_node,
            diagnosis_node,
            socratic_node,
            route_from_exposition,
            route_from_questioning,
            route_from_evaluation,
            route_from_diagnosis,
            route_from_socratic,
        )
        
        # Map node names to functions
        node_map = {
            "exposition": exposition_node,
            "questioning": questioning_node,
            "evaluation": evaluation_node,
            "diagnosis": diagnosis_node,
            "socratic": socratic_node,
        }
        
        # Map node names to routing functions
        route_map = {
            "exposition": route_from_exposition,
            "questioning": route_from_questioning,
            "evaluation": route_from_evaluation,
            "diagnosis": route_from_diagnosis,
            "socratic": route_from_socratic,
        }
        
        current_state = state["current_state"]
        logger.info("Current agent state: %s (invoking graph from this node)", current_state)
        
        # For exposition state, check if student is requesting a question
        # If so, skip re-running exposition and go straight to questioning
        # If student is asking a follow-up question, run exposition to answer it
        if current_state == "exposition":
            route_func = route_map.get("exposition")
            if route_func:
                next_node = route_func(state)
                logger.info(f"Routing decision from exposition: exposition → {next_node}")
                
                if next_node == "questioning":
                    # Student requested question, go straight to questioning
                    state["current_state"] = "questioning"
                    current_state = "questioning"
                elif next_node == "END":
                    # Student asked a follow-up question, run exposition to answer it
                    logger.info("Student asked follow-up question in exposition, generating response")
                    state = await exposition_node(state)
                    # Stay in exposition state
                    current_state = "exposition"
        
        # For questioning state, student has submitted an answer - move to evaluation
        elif current_state == "questioning":
            logger.info("Student submitted answer, transitioning to evaluation")
            state["current_state"] = "evaluation"
            current_state = "evaluation"
        
        # Execute graph flow using conditional routing
        # Continue until we reach END (wait for next student message)
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations and current_state != "exposition":
            # Get current node
            node_name = state["current_state"]
            
            if node_name not in node_map:
                logger.error(f"Unknown node: {node_name}")
                break
            
            # Execute current node
            node_func = node_map[node_name]
            logger.info(f"Executing node: {node_name}")
            state = await node_func(state)
            
            # Determine next node using routing function
            route_func = route_map.get(node_name)
            if route_func:
                next_node = route_func(state)
                logger.info(f"Routing decision: {node_name} → {next_node}")
                
                if next_node == "END" or next_node == "__end__":
                    # Graph execution complete - waiting for student
                    logger.info("Graph execution complete (reached END)")
                    break
                
                # Update state to next node
                state["current_state"] = next_node
            else:
                logger.warning(f"No routing function for {node_name}")
                break
            
            iteration += 1
        
        if iteration >= max_iterations:
            logger.error("Graph execution hit max iterations - possible infinite loop")
        
        # Update session counters
        update_session(
            session_id,
            questions_attempted=state["questions_attempted"],
            questions_correct=state["questions_correct"],
            db_path=DATABASE_PATH
        )
        
        # Update progress after evaluation (FR-008: 3-5 correct = complete)
        # Check if a question was evaluated in this turn
        from bloom.models import update_progress
        from bloom.main import COMPLETION_THRESHOLD
        
        prev_attempted = session["questions_attempted"]
        new_attempted = state["questions_attempted"]
        
        if new_attempted > prev_attempted:
            # A question was evaluated in this turn
            prev_correct = session["questions_correct"]
            new_correct = state["questions_correct"]
            is_correct = new_correct > prev_correct
            
            logger.info(f"Question evaluated: correct={is_correct}, total={new_correct}/{new_attempted}")
            
            update_progress(
                session["subtopic_id"],
                is_correct,
                COMPLETION_THRESHOLD,
                DATABASE_PATH
            )
        
        # Save new tutor messages to database
        # Get messages added since the original count (includes student message + tutor responses)
        new_messages = state["messages"][existing_db_count:]
        
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
        
        # Return ALL new messages (student + tutor) as HTML
        # Get subtopic_id for image loading (spec 003)
        session = get_session(session_id, DATABASE_PATH)
        subtopic_id = session.get("subtopic_id") if session else None
        
        html_parts = []
        for msg in new_messages:
            html_parts.append(templates.get_template("components/message.html").render(
                message=msg,
                subtopic_id=subtopic_id,
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
            subtopic_id=None,
            request=request,
        )


# ============================================================================
# Image Serving Endpoint (spec 003)
# ============================================================================

@router.get("/api/image/{subtopic_id}")
async def serve_image(subtopic_id: int):
    """Serve cached whiteboard image for a subtopic.
    
    Returns cached image (PNG or JPEG) with appropriate headers for browser caching.
    Returns 404 if image not found (graceful degradation on frontend).
    
    Args:
        subtopic_id: Subtopic ID to fetch image for
        
    Returns:
        Response with image/png or image/jpeg content-type and binary data
        
    Raises:
        HTTPException: 404 if image not found or corrupted
    """
    from fastapi.responses import Response
    from bloom.database import get_cached_image
    
    try:
        # Retrieve cached image
        cached_image = get_cached_image(subtopic_id, DATABASE_PATH)
        
        if cached_image is None:
            # No image found - return 404 for graceful degradation
            logger.debug(f"Image not found for subtopic {subtopic_id}")
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Extract image data and format
        image_data = cached_image["image_data"]
        image_format = cached_image.get("image_format", "PNG")
        
        # Validate image data exists
        if not image_data or len(image_data) == 0:
            logger.warning(f"Corrupted image data for subtopic {subtopic_id}")
            raise HTTPException(status_code=404, detail="Image data corrupted")
        
        # Determine correct media type
        media_type = "image/jpeg" if image_format == "JPEG" else "image/png"
        
        # Return image with appropriate headers
        return Response(
            content=image_data,
            media_type=media_type,
            headers={
                # Browser caching: cache for 1 week (images don't change often)
                "Cache-Control": "public, max-age=604800, immutable",
                # Additional metadata
                "Content-Length": str(len(image_data)),
                "X-Image-Format": image_format,
                "X-Generated-At": cached_image.get("generated_at", ""),
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (404)
        raise
    except Exception as e:
        # Log unexpected errors but return 404 for graceful degradation
        logger.error(f"Error serving image for subtopic {subtopic_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail="Image unavailable")


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
        # Get subtopic_id for image loading (spec 003)
        session = get_session(session_id, DATABASE_PATH)
        subtopic_id = session.get("subtopic_id") if session else None
        
        html_parts = []
        for msg in new_messages:
            html_parts.append(templates.get_template("components/message.html").render(
                message=msg,
                subtopic_id=subtopic_id,
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
            subtopic_id=None,
            request=request,
        )

