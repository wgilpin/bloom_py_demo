# Tasks: Bloom GCSE Mathematics Tutor

**Input**: Design documents from `/specs/001-bloom-tutor-app/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL per constitution. This task list focuses on implementation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `bloom/` at repository root (FastAPI + htmx integrated)
- All paths shown below use this structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create bloom/ directory structure per implementation plan
- [x] T002 Initialize pyproject.toml with dependencies: fastapi, uvicorn[standard], langgraph, openai, anthropic, google-generativeai, pydantic
- [x] T003 [P] Create README.md with quickstart instructions from quickstart.md
- [x] T004 [P] Create syllabus_sample.json with sample GCSE math syllabus (3 topics, 10 subtopics)
- [x] T005 [P] Create .gitignore with bloom.db, __pycache__, .env entries

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create database schema in bloom/database.py with all 7 tables (topics, subtopics, sessions, messages, calculator_history, progress, agent_checkpoints)
- [x] T007 Implement database initialization function in bloom/database.py with PRAGMA foreign_keys = ON
- [x] T008 [P] Create Pydantic models in bloom/models.py (SyllabusSchema, TopicSchema, SubtopicSchema, SessionState)
- [x] T009 [P] Create FastAPI app in bloom/main.py with CORS middleware, static files mount, and templates config
- [x] T010 [P] Create base HTML template in bloom/templates/base.html with htmx CDN, Tailwind CDN, and base layout
- [x] T011 Create LangGraph agent structure in bloom/tutor_agent.py with 5 state nodes: exposition, questioning, evaluation, diagnosis, socratic
- [x] T012 Implement agent state transitions in bloom/tutor_agent.py with LangGraph StateGraph configuration
- [x] T013 [P] Create environment variable loading in bloom/main.py for LLM_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, XAI_API_KEY, LLM_MODEL, DATABASE_PATH, COMPLETION_THRESHOLD
- [x] T014 [P] Create bloom/routes/__init__.py as empty module file

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Chat-Based Tutoring Session (Priority: P1) 🎯 MVP

**Goal**: Interactive AI tutor that explains concepts, asks questions, and provides feedback through chat

**Independent Test**: Start app, select any subtopic, chat with tutor, answer 2-3 questions, receive feedback

### Implementation for User Story 1

- [ ] T015 [P] [US1] Create Session model methods in bloom/models.py (create_session, get_session, update_session)
- [ ] T016 [P] [US1] Create Message model methods in bloom/models.py (add_message, get_messages_for_session)
- [ ] T017 [US1] Implement multi-provider LLM client wrapper in bloom/tutor_agent.py supporting OpenAI, Anthropic, Google Gemini, and xAI Grok with retry logic and error handling (FR-018)
- [ ] T018 [US1] Implement exposition_node in bloom/tutor_agent.py that generates concept explanation for subtopic
- [ ] T019 [US1] Implement questioning_node in bloom/tutor_agent.py that generates appropriate GCSE-level questions
- [ ] T020 [US1] Implement evaluation_node in bloom/tutor_agent.py that assesses answer correctness (FR-013)
- [ ] T021 [US1] Implement diagnosis_node in bloom/tutor_agent.py that identifies student misconceptions
- [ ] T022 [US1] Implement socratic_node in bloom/tutor_agent.py that asks guiding questions (FR-014)
- [ ] T023 [US1] Create agent checkpoint save/restore functions in bloom/tutor_agent.py using agent_checkpoints table
- [ ] T024 [US1] Create POST /session/start endpoint in bloom/routes/student.py that initializes session and agent state
- [ ] T025 [US1] Create GET /chat endpoint in bloom/routes/student.py that renders chat interface
- [ ] T026 [US1] Create POST /chat/message endpoint in bloom/routes/student.py that processes student input via agent
- [ ] T027 [US1] Create GET /chat/messages endpoint in bloom/routes/student.py that returns message history as HTML fragments
- [ ] T028 [US1] Create POST /chat/retry endpoint in bloom/routes/student.py for LLM failure retry (FR-018)
- [ ] T029 [US1] Create chat.html template in bloom/templates/chat.html with htmx message form and history container
- [ ] T030 [US1] Create message.html component in bloom/templates/components/message.html for rendering individual messages

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Syllabus Navigation and Progress Tracking (Priority: P2)

**Goal**: Students can browse syllabus, select subtopics, and see progress indicators

**Independent Test**: Load syllabus via admin, browse topics/subtopics, complete session, verify progress displays correctly

### Implementation for User Story 2

- [ ] T031 [P] [US2] Create syllabus loading function in bloom/database.py that validates and inserts topics/subtopics from JSON
- [ ] T032 [P] [US2] Create progress tracking functions in bloom/models.py (update_progress, get_progress_for_subtopic, aggregate_topic_progress)
- [ ] T033 [US2] Implement syllabus validation in bloom/routes/admin.py using Pydantic schemas with detailed error messages (FR-019)
- [ ] T034 [US2] Create POST /admin/syllabus/upload endpoint in bloom/routes/admin.py that loads and validates JSON
- [ ] T035 [US2] Create POST /admin/syllabus/validate endpoint in bloom/routes/admin.py for pre-validation without loading
- [ ] T036 [US2] Create GET / endpoint in bloom/routes/student.py that shows syllabus with progress or resume prompt
- [ ] T037 [US2] Create GET /syllabus endpoint in bloom/routes/student.py that returns topics/subtopics with progress data
- [ ] T038 [US2] Create GET /progress endpoint in bloom/routes/student.py that returns progress summary JSON
- [ ] T039 [US2] Create POST /session/resume endpoint in bloom/routes/student.py that restores session from checkpoint (FR-020)
- [ ] T040 [US2] Create POST /session/abandon endpoint in bloom/routes/student.py for "Start Fresh" action
- [ ] T041 [US2] Implement progress update logic in bloom/routes/student.py after each answer evaluation (FR-008: 3-5 correct = complete)
- [ ] T042 [US2] Create syllabus.html template in bloom/templates/syllabus.html with topic/subtopic hierarchical display
- [ ] T043 [US2] Create progress.html component in bloom/templates/components/progress.html with completion indicators
- [ ] T044 [US2] Create admin.html template in bloom/templates/admin.html with syllabus upload form
- [ ] T045 [US2] Add session resumption modal to base.html that prompts "Resume" or "Start Fresh" when active session exists

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Context-Aware Integrated Calculator (Priority: P3)

**Goal**: Calculator appears automatically for numerical questions, records operations for tutor feedback

**Independent Test**: Start numerical question session (percentages), verify calculator appears; start algebraic session, verify calculator hidden

### Implementation for User Story 3

- [ ] T046 [P] [US3] Create calculator history functions in bloom/models.py (log_calculation, get_recent_calculations)
- [ ] T047 [US3] Implement calculator visibility classifier in bloom/tutor_agent.py that asks LLM to classify question as NUMERICAL or NON_NUMERICAL
- [ ] T048 [US3] Add calculator_visible flag to agent state in bloom/tutor_agent.py based on question classification (FR-010, FR-011)
- [ ] T049 [US3] Create POST /calculator/compute endpoint in bloom/routes/student.py that evaluates expression safely and logs to database (FR-012)
- [ ] T050 [US3] Create GET /calculator endpoint in bloom/routes/student.py that returns calculator HTML or empty div based on visibility flag
- [ ] T051 [US3] Create calculator.html component in bloom/templates/components/calculator.html with button grid and display
- [ ] T052 [US3] Create calculator.js in bloom/static/js/calculator.js with button click handling and expression evaluation
- [ ] T053 [US3] Update chat/message endpoint in bloom/routes/student.py to include calculator visibility in htmx response (swap calculator container)
- [ ] T054 [US3] Update agent nodes in bloom/tutor_agent.py to reference calculator history in feedback when available

**Checkpoint**: All user stories (1, 2, 3) should now be independently functional

---

## Phase 6: User Story 4 - Socratic Tutoring and Error Diagnosis (Priority: P4)

**Goal**: Enhanced error diagnosis with multi-round Socratic questioning for incorrect answers

**Independent Test**: Intentionally answer incorrectly, receive hints, ask for more help, receive Socratic questions, eventually get full solution

### Implementation for User Story 4

- [ ] T055 [US4] Enhance evaluation_node in bloom/tutor_agent.py to classify answer as correct/partial/incorrect with detailed assessment
- [ ] T056 [US4] Enhance diagnosis_node in bloom/tutor_agent.py to identify specific misconception types (e.g., "common denominator forgotten")
- [ ] T057 [US4] Enhance socratic_node in bloom/tutor_agent.py to track hint count and escalate from subtle to explicit guidance
- [ ] T058 [US4] Add state tracking in bloom/tutor_agent.py for hints_given counter in SessionState
- [ ] T059 [US4] Implement "request full answer" detection in bloom/tutor_agent.py that provides step-by-step solution after 3 hints
- [ ] T060 [US4] Update LLM prompts in bloom/tutor_agent.py to include Socratic teaching style and misconception examples from research.md

**Checkpoint**: All user stories should now be complete with enhanced pedagogy

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T061 [P] Create tailwind.config.js with shadcn/ui theme configuration
- [ ] T062 [P] Compile Tailwind CSS: `npx tailwindcss -i bloom/static/css/input.css -o bloom/static/css/output.css --minify`
- [ ] T063 [P] Update base.html to use local Tailwind CSS instead of CDN (optional for production)
- [ ] T064 [P] Add logging configuration in bloom/main.py with INFO level for key events (session start, LLM calls, errors)
- [ ] T065 [P] Create POST /admin/progress/reset endpoint in bloom/routes/admin.py for clearing all progress/sessions (testing utility)
- [ ] T066 [P] Add error handling middleware in bloom/main.py for unhandled exceptions with friendly error pages
- [ ] T067 [P] Update README.md with final environment variable list and troubleshooting section
- [ ] T068 Perform manual smoke test per quickstart.md: load syllabus, complete session, verify progress, test resumption
- [ ] T069 Review constitution compliance: verify no ORMs used, tests optional, single monolith, minimal dependencies
- [ ] T070 Final code cleanup: remove debug prints, ensure consistent code style, verify all TODO comments resolved

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1) → US2 (P2) → US3 (P3) → US4 (P4) (sequential by priority)
  - OR implement in parallel if team has capacity (US1, US2, US3 are mostly independent)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 for session/progress integration, but syllabus browsing is independent
- **User Story 3 (P3)**: Depends on US1 (chat interface exists) - Calculator integrates with chat
- **User Story 4 (P4)**: Enhances US1 - Requires basic tutoring loop to be working

### Within Each User Story

- Models/database functions before routes/endpoints
- Agent nodes before endpoints that use them
- Templates before endpoints that render them
- Core implementation before enhancements

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Within each user story, tasks marked [P] can run in parallel
- Foundational phase parallelism:
  - T006-T007 (database) + T008 (models) + T009-T010 (FastAPI/templates) can run in parallel
  - T011-T012 (agent) depends on T008 (needs models)
- US1 parallelism:
  - T015-T016 (models) + T018-T022 (agent nodes) can start together
  - T029-T030 (templates) can be built in parallel with backend work

---

## Parallel Example: User Story 1

```bash
# Launch all parallel models/agent work for User Story 1:
T015: Create Session model methods
T016: Create Message model methods
T018: Implement exposition_node
T019: Implement questioning_node
T020: Implement evaluation_node
T021: Implement diagnosis_node
T022: Implement socratic_node

# These can all be developed simultaneously (different functions in same file or different files)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (~15 min)
2. Complete Phase 2: Foundational (~2-3 hours - database, agent framework, FastAPI setup)
3. Complete Phase 3: User Story 1 (~4-6 hours - chat tutoring loop)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Can start session ✓
   - Tutor explains concept ✓
   - Tutor asks question ✓
   - Student answers ✓
   - Feedback provided ✓
5. Deploy/demo if ready

**MVP Delivers**: Functional AI tutor that can teach any topic through chat (requires manual topic selection in code or simple CLI)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (~3 hours)
2. Add User Story 1 → Test independently → **MVP Demo Ready!** (~4-6 hours)
3. Add User Story 2 → Test independently → Full syllabus navigation + progress (~3-4 hours)
4. Add User Story 3 → Test independently → Context-aware calculator (~2-3 hours)
5. Add User Story 4 → Test independently → Enhanced Socratic tutoring (~2-3 hours)
6. Polish → Production ready (~1-2 hours)

**Total Effort**: ~15-22 hours for complete implementation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (~3 hours)
2. Once Foundational is done:
   - Developer A: User Story 1 (chat tutoring)
   - Developer B: User Story 2 (syllabus + progress)
   - Developer C: User Story 3 (calculator)
3. After US1-US3 complete, one developer adds US4 enhancements
4. Team does final polish together

---

## Task Distribution by File

### bloom/database.py
- T006, T007 (Foundational)
- T031 (US2)

### bloom/models.py
- T008 (Foundational)
- T015, T016 (US1)
- T032 (US2)
- T046 (US3)

### bloom/tutor_agent.py
- T011, T012 (Foundational)
- T017-T023 (US1)
- T047, T048, T054 (US3)
- T055-T060 (US4)

### bloom/main.py
- T009, T013 (Foundational)
- T064, T066 (Polish)

### bloom/routes/student.py
- T024-T027 (US1)
- T036-T041 (US2)
- T049, T050, T053 (US3)

### bloom/routes/admin.py
- T033-T035 (US2)
- T065 (Polish)

### bloom/templates/
- T010 (base.html - Foundational)
- T029, T030 (US1)
- T042-T045 (US2)
- T051 (US3)

### bloom/static/
- T052 (calculator.js - US3)
- T061-T063 (Tailwind - Polish)

---

## Notes

- [P] tasks = different files or independent functions, no data dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Constitution compliance: No tests required by default, tests optional only if logic breaks repeatedly
- Commit after each task or logical group (constitution: commit every 30-60 min)
- Stop at any user story checkpoint to validate independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Success Metrics

**Task Metrics**:
- Total tasks: 70
- Setup tasks: 5
- Foundational tasks: 9 (blocking)
- User Story 1 (P1): 16 tasks
- User Story 2 (P2): 15 tasks  
- User Story 3 (P3): 9 tasks
- User Story 4 (P4): 6 tasks
- Polish tasks: 10 tasks

**Parallel Opportunities**: 23 tasks marked [P] can run in parallel (33% of tasks)

**Independent Test Coverage**:
- ✓ Each user story has explicit independent test criteria
- ✓ MVP (US1) can be demonstrated without US2-US4
- ✓ Each subsequent story adds value without breaking previous stories

**Constitution Alignment**:
- ✓ No test tasks (tests optional per constitution)
- ✓ Direct SQL (no ORM)
- ✓ Minimal boilerplate (FastAPI + htmx, no React)
- ✓ Focused scope (70 tasks total for complete feature)

---

**Ready for implementation!** Start with Phase 1-2, then tackle User Story 1 for MVP. 🚀

