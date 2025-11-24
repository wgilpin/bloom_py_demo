# Implementation Plan: Bloom GCSE Mathematics Tutor

**Branch**: `001-bloom-tutor-app` | **Date**: 2025-11-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bloom-tutor-app/spec.md`

## Summary

Bloom is an AI-powered GCSE mathematics tutor that uses LLM agents to deliver personalized, Socratic tutoring through a chat interface. The system loads a UK GCSE mathematics syllabus (JSON), tracks student progress across topics/subtopics, and provides context-aware tools (like a calculator for numerical problems). Core features include chat-based tutoring with adaptive state transitions, progress persistence, session resumption, and admin syllabus management.

**Technical Approach**: FastAPI backend with htmx-powered frontend, LangGraph for tutoring agent state management, SQLite for persistence, and shadcn/Tailwind CSS for UI. The system uses a stateful agent architecture to manage tutoring states (exposition, questioning, evaluation, error diagnosis, Socratic guidance) with LLM-powered responses.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: 
- FastAPI (async web framework)
- htmx (frontend interactivity without JavaScript complexity)
- LangGraph (LLM agent workflow and state management)
- SQLite (local persistence via Python's sqlite3)
- Tailwind CSS + shadcn/ui (component styling)
- LLM SDKs (OpenAI/Anthropic/Google Gemini/xAI Grok)

**Storage**: SQLite database (local file: `bloom.db`)
**Testing**: pytest (optional, per constitution - only for repeatedly broken logic)
**Target Platform**: Web application (cross-platform via browser)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 
- Tutor response latency < 3 seconds (SC-005)
- Full tutoring session (3 questions) < 10 minutes (SC-001)
**Constraints**: 
- Single-user demo (no authentication/multi-tenancy)
- Local-only deployment (no cloud dependencies)
- Calculator appears/hides contextually (100% accuracy target, SC-006)
**Scale/Scope**: 
- ~10 topics × 2-5 subtopics = 20-50 subtopics total
- Single concurrent session
- Conversation history limited to current session (no infinite scroll)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Simplicity First ✓
- **Architecture**: Single monolithic application (FastAPI + htmx), no microservices
- **Dependencies**: All chosen libraries align with constitution (FastAPI preferred, htmx explicitly mentioned)
- **No premature abstraction**: Direct SQL via sqlite3 (no ORM), functions over classes where possible

### II. Minimal Boilerplate ✓
- **htmx**: Eliminates JavaScript boilerplate, uses HTML attributes for interactivity
- **FastAPI**: Minimal setup, automatic OpenAPI docs, async built-in
- **No config files**: Environment variables only (LLM API key, optional tuning params)
- **Direct approach**: No repository pattern, no service layer abstraction until needed

### III. Rapid Iteration Over Perfection ✓
- **Tests optional**: Constitution explicitly allows skipping tests for demo
- **Simple deployment**: Single Python process, SQLite file, no orchestration
- **htmx benefits**: Immediate visual feedback without build step

### IV. Focused Scope ✓
- **LangGraph**: Justified for tutoring state machine (exposition → question → evaluation → diagnosis)
- **Calculator**: Scoped to basic arithmetic (no graphing/scientific functions)
- **Admin**: Simple endpoint or CLI script (defer complexity)

### V. Pleasing Simplicity (UI/UX) ✓
- **shadcn + Tailwind**: Modern, clean components without heavy framework
- **htmx**: Responsive interactions without SPA complexity
- **Two-click navigation**: Syllabus → Topic → Subtopic (SC-003 requirement)

### Technology Constraints Compliance ✓
- ✓ Python 3.13+
- ✓ FastAPI (constitution: "FastAPI or Flask—whichever ships fastest")
- ✓ htmx (constitution: "Alpine.js/htmx for interactivity")
- ✓ SQLite (constitution: "Start with JSON files or SQLite")
- ⚠ **LangGraph consideration**: Constitution says "no LangChain unless chaining proven necessary"
  - **Justification**: LangGraph is not LangChain—it's a lightweight state machine for agent workflows
  - **Need**: Tutoring requires explicit state management (5 states: exposition, questioning, evaluation, diagnosis, Socratic)
  - **Alternative rejected**: Manual state management would require custom state machine code (more boilerplate)
  - **Decision**: Use LangGraph for state orchestration; it reduces complexity vs. hand-rolling state logic

### Violations Requiring Justification

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| LangGraph (similar to LangChain) | Tutoring state machine with 5 states + LLM calls needs orchestration | Hand-rolled state machine would be ~200 lines of boilerplate; LangGraph provides built-in state persistence and node-based flow |
| shadcn/ui (component library) | Pre-built accessible components save development time for calculator, progress indicators, chat UI | Building from scratch would violate "rapid iteration"; shadcn is just Tailwind + copy-paste components (no npm dependency bloat) |

**Gate Status**: ✅ **PASS** - Violations justified; overall architecture aligns with simplicity principles

## Project Structure

### Documentation (this feature)

```text
specs/001-bloom-tutor-app/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Tech decisions and patterns
├── data-model.md        # Phase 1: Database schema and entities
├── quickstart.md        # Phase 1: Local setup and run guide
├── contracts/           # Phase 1: API endpoints
│   └── api.yaml         # OpenAPI spec
└── checklists/          # Requirements checklist (already exists)
    └── requirements.md
```

### Source Code (repository root)

```text
bloom/
├── main.py                    # FastAPI app entry point
├── database.py                # SQLite connection and schema initialization
├── models.py                  # Data models (Syllabus, Topic, Subtopic, Session, Progress, Message)
├── tutor_agent.py             # LangGraph agent definition (tutoring state machine)
├── routes/
│   ├── __init__.py
│   ├── student.py             # Student-facing routes (chat, syllabus, calculator)
│   └── admin.py               # Admin routes (syllabus loading, validation)
├── static/
│   ├── css/
│   │   └── output.css         # Tailwind compiled CSS
│   └── js/
│       └── calculator.js      # Calculator widget logic (minimal)
└── templates/
    ├── base.html              # Base template with htmx
    ├── syllabus.html          # Topic/subtopic browser
    ├── chat.html              # Chat interface with tutor
    └── components/
        ├── calculator.html    # Calculator widget (htmx partial)
        ├── message.html       # Chat message component
        └── progress.html      # Progress indicator

tests/                         # Optional (per constitution)
└── test_syllabus_validation.py  # If validation breaks repeatedly

README.md                      # Setup and run instructions
pyproject.toml                 # Dependencies (uv/pip)
bloom.db                       # SQLite database (created at runtime)
syllabus_sample.json           # Example GCSE syllabus
tailwind.config.js             # Tailwind configuration
```

**Structure Decision**: Web application structure chosen. Backend (FastAPI) and frontend (htmx templates) are integrated into a single `bloom/` directory for simplicity. No separate frontend build step—htmx templates served directly by FastAPI. Tailwind CSS compiled once during development.

## Complexity Tracking

No additional complexity beyond justified items above. LangGraph and shadcn/ui both reduce overall complexity vs. alternatives.

---

## Phase 1 Design Artifacts: Constitution Re-Check

**Post-Design Evaluation** (after data model, contracts, and research complete):

### Architecture Review ✓

**Data Model** ([data-model.md](./data-model.md)):
- ✓ Normalized SQLite schema, no ORM (raw SQL via sqlite3)
- ✓ Minimal indexes (only for common queries)
- ✓ Foreign keys with CASCADE for referential integrity
- ✓ Simple JSON checkpointing for agent state

**API Contracts** ([contracts/api.yaml](./contracts/api.yaml)):
- ✓ RESTful endpoints, server-side rendering with htmx
- ✓ HTML responses (not JSON SPA), minimal JavaScript
- ✓ OpenAPI spec documents 15 endpoints total (reasonable for demo scope)

**Research Decisions** ([research.md](./research.md)):
- ✓ OpenAI GPT-4o-mini chosen (fast, cheap, aligns with constitution)
- ✓ LangGraph justified (state machine reduces boilerplate vs. manual implementation)
- ✓ htmx patterns shown (no build step, declarative)
- ✓ Calculator: minimal JS with server-side classification

### Principles Compliance ✓

**I. Simplicity First**:
- ✓ Single monolithic app (no microservices)
- ✓ Direct SQL queries (no ORM abstraction layer)
- ✓ Minimal dependencies (6 core packages)

**II. Minimal Boilerplate**:
- ✓ htmx eliminates React/Vue boilerplate
- ✓ FastAPI auto-generates OpenAPI docs
- ✓ No config files (environment variables only)
- ✓ Tailwind via CDN (no build step in dev)

**III. Rapid Iteration Over Perfection**:
- ✓ No tests required (per constitution)
- ✓ Hot reload with uvicorn --reload
- ✓ SQLite (no database setup ceremony)

**IV. Focused Scope**:
- ✓ 15 endpoints (covers all spec requirements, no feature bloat)
- ✓ Single-user demo (no multi-tenancy complexity)
- ✓ Basic calculator (no scientific functions)

**V. Pleasing Simplicity (UI/UX)**:
- ✓ shadcn components (accessible, copy-paste)
- ✓ Tailwind (utility-first, no heavy CSS framework)
- ✓ Server-driven htmx (responsive without SPA overhead)

### Constitution Violations: None Detected ✅

All design decisions align with constitution principles. LangGraph and shadcn/ui remain justified as complexity-reducing choices.

---

## Final Gate Status: ✅ APPROVED FOR IMPLEMENTATION

Ready to proceed to `/speckit.tasks` for task breakdown.
