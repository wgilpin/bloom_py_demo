# Feature Specification: Bloom GCSE Mathematics Tutor

**Feature Branch**: `001-bloom-tutor-app`  
**Created**: 2025-11-24  
**Status**: Draft  
**Input**: User description: "Develop bloom, a demo for a tutor app that teaches UK GCSE mathematics. Allow the syllabus to be loaded in json format. This is a single user demo. track progress on the different areas of the syllabus. The core UI is a chat app, using LLMs and agents to deliver the tutoring. The loop will be exposition -> user chat -> set question -> user answer -> error diagnosis -> socratric tutoring -> repeat, although state may move between any of these as appropriate to the actual interaction. The user can access a built in calculator, which the system can monitor, or they can just type in their answers in the chat"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Chat-Based Tutoring Session (Priority: P1)

A student opens Bloom and engages in a single tutoring session on a mathematics subtopic. The tutor explains a concept, asks a question, receives the student's typed answer (with or without calculator assistance depending on question type), provides feedback, and continues the conversation naturally.

**Why this priority**: This is the core value proposition—an interactive AI tutor. Without this, there's no product. This story delivers immediate value and can be demonstrated independently.

**Independent Test**: Can be fully tested by starting the app, selecting any math topic, engaging in a conversation where the student answers 2-3 questions, and receiving appropriate feedback. Delivers a complete tutoring experience.

**Acceptance Scenarios**:

1. **Given** the app is open, **When** the student starts a session, **Then** the tutor presents an explanation of a math concept
2. **Given** an explanation has been shown, **When** the tutor asks a question, **Then** the student can type their answer in the chat interface
3. **Given** the student submits an answer, **When** the answer is correct, **Then** the tutor provides positive feedback and moves to the next concept or question
4. **Given** the student submits an answer, **When** the answer is incorrect, **Then** the tutor provides hints and guidance without revealing the full answer
5. **Given** the tutoring session is active, **When** the student asks a clarifying question, **Then** the tutor responds contextually before continuing the lesson flow

---

### User Story 2 - Syllabus Navigation and Progress Tracking (Priority: P2)

A student can see the full GCSE mathematics syllabus (pre-loaded by admin) organized by topics and subtopics, select which subtopic to study, and view their progress across all subtopics they've attempted.

**Why this priority**: Progress tracking motivates students and provides structure. The hierarchical organization helps students navigate the curriculum logically. This makes Bloom feel like a complete learning system rather than a single-conversation chatbot. Separating admin setup from student experience keeps the student interface simple.

**Independent Test**: With a syllabus already loaded (admin function), open the app as a student, view topics and subtopics (e.g., "Number" with subtopics like "Fractions", "Percentages"), select a subtopic, complete a session on that subtopic, and verify progress is saved and displayed at both subtopic and topic levels.

**Acceptance Scenarios**:

1. **Given** a syllabus has been loaded by admin, **When** the student opens the app, **Then** all GCSE math topics and subtopics are displayed in an organized hierarchical structure
2. **Given** the syllabus is displayed, **When** the student selects a specific subtopic (e.g., "Operations with Fractions" under "Fractions" under "Number"), **Then** a tutoring session for that subtopic begins
3. **Given** the syllabus is displayed, **When** the student views a topic with subtopics, **Then** all subtopics are visible and selectable without requiring additional navigation steps
4. **Given** the student has completed questions on a subtopic, **When** they view the syllabus, **Then** progress indicators show which subtopics have been attempted and completion level, with topic-level progress reflecting aggregated subtopic completion
5. **Given** the student exits the app during an active session, **When** they return later, **Then** they are offered the option to resume the exact conversation state or start a new session, and their progress data persists regardless of choice

---

### User Story 3 - Context-Aware Integrated Calculator (Priority: P3)

A student working on a numerical problem sees an in-app calculator automatically appear when calculations are needed. The calculator does not appear for non-numerical work like algebraic manipulation. The tutor can see what calculations were performed to better understand the student's problem-solving approach.

**Why this priority**: Many GCSE math problems require numerical computation, but not all do. A context-aware calculator improves user experience without cluttering the interface during algebraic or conceptual work. This gives the tutor insight into student thinking, but the core tutoring works without it.

**Independent Test**: Start tutoring sessions on different subtopic types: verify the calculator appears for numerical problems (e.g., "Calculate 3/4 + 2/5"), does not appear for algebraic problems (e.g., "Simplify 2x + 3x"), and can be used to compute intermediate steps with the tutor acknowledging the calculator usage in feedback.

**Acceptance Scenarios**:

1. **Given** a tutoring session poses a numerical problem (e.g., "Calculate 15% of 240"), **When** the question is displayed, **Then** the calculator interface automatically appears
2. **Given** a tutoring session poses an algebraic problem (e.g., "Simplify 3x + 5x - 2"), **When** the question is displayed, **Then** no calculator interface is shown
3. **Given** the calculator is visible, **When** the student performs calculations, **Then** those calculations are recorded by the system
4. **Given** the student has used the calculator, **When** they submit an answer, **Then** the tutor can reference the calculation steps in feedback (e.g., "I see you calculated 240 × 0.15 first, which is the right approach")
5. **Given** the calculator is visible, **When** the student chooses to type the answer directly without using the calculator, **Then** the system accepts the answer normally without requiring calculator usage
6. **Given** a problem initially doesn't need calculation but the student asks a follow-up requiring numbers, **When** the context shifts to numerical work, **Then** the calculator becomes available

---

### User Story 4 - Socratic Tutoring and Error Diagnosis (Priority: P4)

When a student provides an incorrect answer, the tutor analyzes the type of error, asks guiding questions to help the student discover their mistake, and supports multiple rounds of hints before revealing the answer.

**Why this priority**: This transforms Bloom from a simple Q&A bot into a genuine pedagogical tool. However, basic feedback (P1) is sufficient for an MVP demo.

**Independent Test**: Intentionally provide an incorrect answer with a common misconception (e.g., adding fractions incorrectly), verify the tutor identifies the error type, asks probing questions, and guides toward the correct approach over 2-3 conversational turns.

**Acceptance Scenarios**:

1. **Given** the student submits an incorrect answer, **When** the tutor analyzes the error, **Then** the feedback identifies the specific misconception (e.g., "It looks like you may have forgotten to find a common denominator")
2. **Given** the student receives an error hint, **When** they still don't understand, **Then** the tutor asks a Socratic question to guide their thinking (e.g., "What would happen if we tried to add 1/2 + 1/3 directly without changing the denominators?")
3. **Given** the student has received multiple hints, **When** they request the full answer, **Then** the tutor provides the complete solution with step-by-step explanation
4. **Given** the student makes progress after hints, **When** they submit a revised answer, **Then** the tutor acknowledges the improvement and continues accordingly

---

### Edge Cases

- What happens when a student submits a nonsensical or off-topic response (e.g., "I don't know" or random text)?
- How does the system handle extremely long tutoring sessions (20+ questions in a single subtopic)?
- What if the admin loads a malformed syllabus JSON file with invalid topic/subtopic data? System validates and displays specific error messages (e.g., "Missing 'name' field in Topic 3")
- What if the syllabus has more than two levels of nesting (topic → subtopic → sub-subtopic)? Validation rejects with clear error explaining two-level limit
- What if no syllabus has been loaded when a student tries to use the app? System displays friendly message directing admin to load syllabus first
- Admin knows if syllabus loaded successfully through explicit success confirmation message or detailed validation errors
- Can the admin update or replace the syllabus after initial loading, and what happens to existing student progress?
- How does the tutor respond if the student asks a question completely outside the current subtopic scope?
- What happens if the student closes the app mid-session? Progress and full conversation state are saved; on return, student is offered option to resume where they left off or start a new session
- How does the calculator handle invalid mathematical expressions or division by zero?
- What if a topic has zero subtopics or a subtopic is missing required fields?
- How does the system determine whether a question requires numerical calculation vs algebraic manipulation?
- What if a problem has both algebraic and numerical components (e.g., "Solve 2x + 3 = 11 and verify your answer")?
- What if the student wants to use the calculator for a non-numerical problem despite it being hidden?
- When LLM API fails or times out: System displays a friendly error message, allows the student to retry with the same question, and preserves conversation context and session state

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an admin function to load a GCSE mathematics syllabus from a JSON file containing topics, subtopics, descriptions, and hierarchical organization where subtopics are the selectable learning units
- **FR-002**: System MUST display the pre-loaded syllabus to students without requiring them to interact with file loading or admin functions
- **FR-003**: System MUST present a chat interface as the primary student interaction method
- **FR-004**: System MUST use an LLM to generate tutor responses that are contextually appropriate to the conversation
- **FR-005**: System MUST support the following tutoring states: exposition (explaining concepts), questioning (posing problems), answer evaluation (assessing student responses), error diagnosis (identifying mistakes), and Socratic tutoring (guided discovery)
- **FR-006**: System MUST allow fluid transitions between tutoring states based on conversation flow, not a rigid sequence
- **FR-007**: System MUST accept student answers as typed text in the chat interface regardless of calculator visibility
- **FR-008**: System MUST track student progress for each subtopic in the syllabus, including number of questions attempted and completion status (subtopic marked complete after 3-5 correct answers), with topic-level progress aggregated from subtopic data
- **FR-009**: System MUST persist progress data and active session state (including conversation history and context) to a local SQLite database so it survives app restarts
- **FR-020**: System MUST offer students the option to resume their last active session (restoring full conversation state) or start a new session when returning to the app
- **FR-021**: System MUST provide an in-chat action button allowing students to end the current session and start a new topic at any time, with confirmation to prevent accidental termination, while preserving progress data
- **FR-010**: System MUST provide an integrated calculator widget that appears automatically when the current question or problem requires numerical computation
- **FR-011**: System MUST hide the calculator widget when the current question involves non-numerical work (e.g., algebraic manipulation, geometric reasoning, conceptual understanding)
- **FR-012**: System MUST record calculator operations performed by the student for potential reference by the tutoring logic
- **FR-013**: System MUST distinguish between correct answers, partially correct answers, and incorrect answers
- **FR-014**: System MUST provide feedback appropriate to the quality of the student's response (praise for correct, hints for incorrect, clarification for partial)
- **FR-015**: System MUST support single-user operation for students (no student authentication required for this demo), with a separate admin function for syllabus loading
- **FR-016**: System MUST allow students to ask clarifying questions at any point during the tutoring session
- **FR-017**: System MUST display the syllabus structure in a navigable format showing topics and their subtopics, allowing students to select subtopics to begin tutoring sessions
- **FR-018**: System MUST handle LLM API failures gracefully by displaying a friendly error message, allowing retry with the same question, and preserving conversation context and session state
- **FR-019**: System MUST validate syllabus JSON structure during admin loading and display clear error messages identifying specific issues (e.g., missing required fields, invalid data types, malformed structure) to help admins correct the file

### Key Entities *(include if feature involves data)*

- **Syllabus**: Represents the GCSE mathematics curriculum, organized in a two-level hierarchy: topics contain subtopics (e.g., Topic: "Number" → Subtopics: "Fractions", "Percentages", "Ratio"). Contains all topics, subtopics, descriptions, and relationships.
- **Topic**: A high-level category in the syllabus (e.g., "Number", "Algebra", "Geometry"). Has a name, description, and contains one or more subtopics. Not directly selectable for tutoring.
- **Subtopic**: A specific area of study within a topic (e.g., "Operations with Fractions" under "Number"). Has a name, description, and parent topic reference. This is the selectable unit that students choose to study.
- **Tutoring Session**: Represents a single continuous interaction between student and tutor focused on one subtopic. Tracks current state (exposition, questioning, etc.), conversation history, and session-specific progress. Sessions are persisted and can be resumed after app restart, with students given the option to continue or start fresh.
- **Student Progress**: Tracks which subtopics have been attempted, questions answered, correct vs incorrect answer ratios, and completion status for each subtopic. A subtopic is marked complete after the student answers 3-5 questions correctly. Can be aggregated to show topic-level progress.
- **Message**: A single chat message, either from the student or the tutor. Contains text content, timestamp, and sender identification.
- **Calculator History**: A record of calculations performed during a session, including the expression entered and result computed. Calculator availability is context-aware based on whether the current question requires numerical computation.

## Clarifications

### Session 2025-11-24

- Q: What should happen when the LLM API fails or times out during a tutoring session? → A: Show friendly error message, allow retry with same question, preserve session
- Q: When is a subtopic considered "complete" for progress tracking? → A: After answering a minimum number of questions correctly (e.g., 3-5 correct)
- Q: Where should student progress data be stored? → A: local sqlite instance
- Q: How should the system handle and report syllabus loading validation? → A: Validate schema and show clear error messages with specific issues
- Q: When a student returns after closing the app mid-session, what do they see? → A: Resume exact conversation state with option to start anew

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Students can complete a full tutoring session (explanation + 3 questions with feedback) on any topic in under 10 minutes
- **SC-002**: The tutor provides contextually appropriate responses with no irrelevant or off-topic content in 95% of interactions
- **SC-003**: Students can load a syllabus containing at least 10 topics with 2-5 subtopics each and navigate to any subtopic within 2 clicks
- **SC-004**: Progress data persists correctly—students see accurate progress indicators after restarting the app 100% of the time
- **SC-005**: The chat interface feels responsive, with tutor responses appearing within 3 seconds of student message submission under normal network conditions
- **SC-006**: The integrated calculator appears for 100% of numerical problems and is hidden for 100% of non-numerical problems (algebraic, geometric proofs, conceptual questions) in testing
- **SC-007**: The integrated calculator handles all basic arithmetic operations (add, subtract, multiply, divide, exponents) without errors
- **SC-008**: In testing with 10 different incorrect answers, the tutor provides helpful hints or Socratic questions at least 8 times (80% success rate)

## Assumptions

- The system supports multiple LLM providers (OpenAI, Anthropic, Google Gemini, xAI Grok) with provider selection via environment variable
- GCSE mathematics syllabus structure will follow standard UK examination board organization (AQA, Edexcel, OCR patterns) with a two-level hierarchy: topics (high-level categories) containing subtopics (specific learning units)
- Single-user demo means no student accounts or authentication—students access the app directly
- An "admin" role exists for setup/configuration purposes (loading syllabus), separate from the student experience
- Admin syllabus loading is a one-time or infrequent setup operation, not part of normal student workflow
- For this demo, admin functionality can be simple (e.g., command-line script, admin page, or file placement)—complexity to be determined during planning
- Student progress and syllabus data are stored in a local SQLite database instance (no remote server or cloud storage required)
- "Monitor" calculator usage means logging operations for potential use in tutoring logic, not enforcing calculator use
- Calculator visibility is determined by question type/context—the LLM or tutoring logic will classify whether the current question requires numerical computation, with edge cases (mixed algebra-numerical problems) resolved during planning
- Socratic tutoring will rely on LLM capabilities—no custom error taxonomy required for MVP
- Progress tracking granularity is at the subtopic level (number of questions attempted/correct per subtopic), not individual question history, with topic-level progress derived by aggregating subtopic progress
- Subtopic completion threshold (3, 4, or 5 correct answers) will be configurable or determined during planning based on demo goals
- The calculator will be a simple arithmetic calculator—no graphing or advanced scientific functions for MVP
- The calculator appears/hides dynamically based on question context, with the mechanism (LLM classification, keyword matching, or explicit question metadata) to be determined during planning
- JSON syllabus format will be determined during planning, with reasonable assumptions (array of topic objects containing name, description, and array of subtopic objects with their own names and descriptions)
