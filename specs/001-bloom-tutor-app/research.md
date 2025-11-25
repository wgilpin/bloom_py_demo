# Research & Technical Decisions: Bloom GCSE Mathematics Tutor

**Date**: 2025-11-24  
**Purpose**: Document technology choices, patterns, and best practices for implementation

## LLM Provider Selection

### Decision: Multi-provider support (OpenAI, Anthropic, Google Gemini, xAI Grok)

**Rationale**:
- **Flexibility**: Different providers have different strengths for educational content
- **Cost optimization**: Allow switching based on budget and performance needs
- **Resilience**: Fallback options if one provider has issues

**Supported Providers**:

1. **OpenAI GPT-4o-mini** (Primary recommendation)
   - Cost-effective: $0.15/$0.60 per 1M tokens
   - Fast response times: 1-2 seconds
   - Strong reasoning for tutoring
   - Official `openai` Python library

2. **Anthropic Claude 3.5 Sonnet** (Premium option)
   - Excellent reasoning, potentially better for education
   - More expensive: $3/$15 per 1M tokens
   - Good at following complex instructions
   - Official `anthropic` Python library

3. **Google Gemini 1.5 Flash** (Alternative)
   - Cost-effective: $0.075/$0.30 per 1M tokens (cheaper than GPT-4o-mini)
   - Fast response times
   - Good multimodal capabilities (future: diagrams)
   - Official `google-generativeai` Python library

4. **xAI Grok** (Experimental)
   - Competitive pricing
   - OpenAI-compatible API
   - Can use `openai` library with different base URL

**Alternatives Considered**:
- **Local models (Llama 3, Mistral)**: Rejected due to complexity (model hosting, GPU requirements) and constitution's "simplicity first" principle

**Implementation Notes**:
- Store API keys in environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`)
- Use async clients for non-blocking requests
- Implement retry logic with exponential backoff (FR-018: LLM failure handling)
- Provider selection via environment variable `LLM_PROVIDER` (default: openai)
- Model selection via environment variable `LLM_MODEL`

**Provider-Specific Implementation**:

```python
# OpenAI
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Anthropic
from anthropic import AsyncAnthropic
client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Google Gemini
import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# xAI Grok (OpenAI-compatible API)
from openai import AsyncOpenAI
client = AsyncOpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)
```

**Model Name Examples**:
- OpenAI: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`
- Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`
- Google: `gemini-1.5-flash`, `gemini-1.5-pro`
- xAI: `grok-beta`

---

## LangGraph for Tutoring Agent

### Decision: Use LangGraph for state machine orchestration

**Rationale**:
- **Built for agent workflows**: Designed specifically for LLM applications with state
- **Graph-based states**: Maps naturally to tutoring flow (exposition → questioning → evaluation → diagnosis → Socratic)
- **State persistence**: Built-in checkpointing aligns with FR-009 (persist session state)
- **Simpler than alternatives**: Less code than hand-rolling state machine with LLM calls
- **Not LangChain**: LangGraph is a standalone library focused on workflows, not the heavy LangChain ecosystem

**Agent State Design**:
```python
class TutorState(TypedDict):
    subtopic_id: int
    current_state: Literal["exposition", "questioning", "evaluation", "diagnosis", "socratic"]
    messages: list[dict]  # Chat history
    questions_correct: int
    questions_attempted: int
    calculator_visible: bool
    last_student_answer: str | None
    calculator_history: list[dict]
```

**Node Functions**:
1. **exposition_node**: LLM explains concept for current subtopic
2. **questioning_node**: LLM generates appropriate question
3. **evaluation_node**: LLM assesses student answer (correct/partial/incorrect)
4. **diagnosis_node**: LLM identifies misconception type
5. **socratic_node**: LLM asks guiding question

**Transition Logic**:
- From any state → evaluation (when student submits answer)
- evaluation → questioning (if correct, move to next question)
- evaluation → diagnosis (if incorrect)
- diagnosis → socratic (provide hint)
- socratic → evaluation (student tries again after hint)
- Allow direct transitions based on conversation (e.g., student asks question during exposition → socratic response → back to exposition)

**Alternatives Considered**:
- **Manual state machine**: 200+ lines of state management boilerplate, error-prone
- **LangChain**: Too heavy, violates "minimal boilerplate" principle
- **Plain LLM calls**: No state persistence, would need custom session management

---

## FastAPI + htmx Architecture

### Decision: Server-side rendering with htmx for dynamic updates

**Rationale**:
- **No build step**: Templates rendered directly, instant feedback loop
- **Minimal JavaScript**: htmx handles AJAX via HTML attributes (`hx-post`, `hx-get`, `hx-swap`)
- **SEO-friendly**: Full HTML rendering (not critical for demo, but good practice)
- **Simple deployment**: Single Python process serves HTML + API
- **Real-time chat**: `hx-trigger="every 1s"` or WebSockets for polling (start with polling for simplicity)

**Key Patterns**:

**Chat Interface (htmx pattern)**:
```html
<!-- Form submits via htmx, response replaces chat container -->
<form hx-post="/chat/message" hx-target="#chat-messages" hx-swap="beforeend">
    <input type="text" name="message" placeholder="Type your answer...">
    <button type="submit">Send</button>
</form>

<div id="chat-messages" hx-get="/chat/messages" hx-trigger="every 2s">
    <!-- Messages streamed here -->
</div>
```

**Calculator Toggle (htmx pattern)**:
```html
<!-- Server decides visibility based on question type -->
<div id="calculator-container" hx-swap-oob="true">
    {% if calculator_visible %}
    <div class="calculator">
        <!-- Calculator UI -->
    </div>
    {% endif %}
</div>
```

**Syllabus Navigation (htmx pattern)**:
```html
<!-- Click subtopic, load chat session without page reload -->
<div class="subtopic" 
     hx-post="/session/start" 
     hx-vals='{"subtopic_id": {{ subtopic.id }}}'
     hx-target="#main-content" 
     hx-push-url="/chat">
    <h3>{{ subtopic.name }}</h3>
    <p>{{ progress }}% complete</p>
</div>
```

**Alternatives Considered**:
- **React/Vue**: Violates constitution ("no React/Vue unless justified"), adds complexity
- **Alpine.js**: Good alternative but htmx is more declarative for server-driven updates
- **Full page reloads**: Poor UX, violates "responsive interactions" principle

---

## SQLite Schema Design

### Decision: Normalized schema with minimal indexes

**Schema Overview**:

```sql
-- Syllabus structure
CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE subtopics (
    id INTEGER PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    name TEXT NOT NULL,
    description TEXT
);

-- Session management
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    subtopic_id INTEGER NOT NULL REFERENCES subtopics(id),
    state TEXT NOT NULL,  -- 'active', 'completed', 'abandoned'
    created_at TEXT NOT NULL,  -- ISO8601
    updated_at TEXT NOT NULL,
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0
);

-- Conversation history
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,  -- 'student', 'tutor'
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL  -- ISO8601
);

-- Calculator history
CREATE TABLE calculator_history (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    expression TEXT NOT NULL,
    result TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

-- Progress tracking
CREATE TABLE progress (
    subtopic_id INTEGER PRIMARY KEY REFERENCES subtopics(id),
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    is_complete BOOLEAN DEFAULT 0,  -- TRUE if >= 3 correct answers
    last_accessed TEXT  -- ISO8601
);

-- LangGraph state checkpoints
CREATE TABLE agent_checkpoints (
    session_id INTEGER PRIMARY KEY REFERENCES sessions(id),
    state_data TEXT NOT NULL  -- JSON blob
);
```

**Rationale**:
- **Normalized**: Reduces redundancy, easier to aggregate progress
- **Foreign keys**: Ensure referential integrity
- **ISO8601 timestamps**: Python's `datetime.fromisoformat()` handles these natively
- **Minimal indexes**: SQLite auto-indexes PRIMARY KEY; add others only if queries slow
- **agent_checkpoints**: Stores LangGraph state as JSON for session resumption (FR-020)

**Alternatives Considered**:
- **Denormalized (JSON blobs)**: Faster writes but harder to query progress aggregations
- **Separate tables for each state**: Over-engineered for demo scale

---

## Calculator Implementation

### Decision: Simple HTML/CSS calculator with basic JavaScript evaluation

**Approach**:
- **UI**: shadcn Button components styled as calculator grid
- **Logic**: Minimal JavaScript for button clicks and `eval()` (sanitized input)
- **Server logging**: Each calculation POSTed to `/calculator/log` endpoint
- **Visibility**: Server sets `calculator_visible` flag in htmx response based on LLM assessment of question type

**Safety**:
- Sanitize input: Allow only digits, operators (`+`, `-`, `*`, `/`, `^`), parentheses, decimal point
- Reject any non-math characters before `eval()`
- Return "Error" for division by zero or invalid expressions

**Visibility Decision Logic**:
```python
def should_show_calculator(question_text: str, llm_client) -> bool:
    """
    Ask LLM to classify question type.
    Prompt: "Is this question numerical (requires calculation) or non-numerical (algebra, proof, concept)? 
             Question: {question_text}
             Answer with only: NUMERICAL or NON_NUMERICAL"
    """
    # Cache recent decisions to avoid redundant LLM calls
    # Default to VISIBLE if unclear (better UX than hiding when needed)
```

**Alternatives Considered**:
- **Regex keyword matching**: Brittle; misses edge cases like "Verify your answer" (mixed type)
- **Always visible**: Clutters UI for algebraic questions (violates UX principle)
- **User toggle**: Adds complexity; context-aware is better UX per constitution

---

## Syllabus JSON Format

### Decision: Simple nested structure with validation schema

**Format**:
```json
{
  "title": "GCSE Mathematics (AQA)",
  "topics": [
    {
      "id": 1,
      "name": "Number",
      "description": "Number operations, fractions, percentages, ratio, and proportion",
      "subtopics": [
        {
          "id": 101,
          "name": "Operations with Fractions",
          "description": "Adding, subtracting, multiplying, and dividing fractions"
        },
        {
          "id": 102,
          "name": "Percentages",
          "description": "Calculating percentages, percentage increase/decrease"
        }
      ]
    },
    {
      "id": 2,
      "name": "Algebra",
      "description": "Algebraic expressions, equations, graphs, and sequences",
      "subtopics": [
        {
          "id": 201,
          "name": "Solving Linear Equations",
          "description": "Solving equations of the form ax + b = c"
        }
      ]
    }
  ]
}
```

**Validation Rules** (Pydantic schema):
- `title`: Required string
- `topics`: Required list, at least 1 topic
  - `id`: Required positive integer, unique across topics
  - `name`: Required non-empty string
  - `description`: Optional string
  - `subtopics`: Required list, at least 1 subtopic
    - `id`: Required positive integer, unique across all subtopics
    - `name`: Required non-empty string
    - `description`: Optional string

**Validation on Load** (FR-019):
```python
from pydantic import BaseModel, validator

class SubtopicSchema(BaseModel):
    id: int
    name: str
    description: str = ""
    
    @validator('id')
    def id_positive(cls, v):
        if v <= 0:
            raise ValueError("Subtopic ID must be positive")
        return v

class TopicSchema(BaseModel):
    id: int
    name: str
    description: str = ""
    subtopics: list[SubtopicSchema]
    
    @validator('subtopics')
    def subtopics_not_empty(cls, v):
        if not v:
            raise ValueError("Topic must have at least one subtopic")
        return v

class SyllabusSchema(BaseModel):
    title: str
    topics: list[TopicSchema]
    
    @validator('topics')
    def topics_not_empty(cls, v):
        if not v:
            raise ValueError("Syllabus must have at least one topic")
        # Check unique IDs
        topic_ids = [t.id for t in v]
        if len(topic_ids) != len(set(topic_ids)):
            raise ValueError("Duplicate topic IDs found")
        subtopic_ids = [s.id for t in v for s in t.subtopics]
        if len(subtopic_ids) != len(set(subtopic_ids)):
            raise ValueError("Duplicate subtopic IDs found")
        return v
```

**Error Messages** (FR-019):
- Pydantic validation errors automatically include field path: `"topics[2].subtopics[0].id: field required"`
- Wrap in user-friendly format: `"Error loading syllabus: Missing 'id' field in Topic 3, Subtopic 1"`

---

## UI Component Library: shadcn + Tailwind

### Decision: shadcn/ui components with Tailwind CSS

**Rationale**:
- **Copy-paste, not npm package**: shadcn components are just Tailwind + HTML, no runtime dependency
- **Accessible by default**: Components follow WAI-ARIA guidelines
- **Customizable**: Full control over component code (copy into `templates/components/`)
- **Fast iteration**: No build step for Tailwind in dev mode (use CDN); compile for production

**Components Needed**:
1. **Button**: Calculator keys, submit, retry
2. **Card**: Topic/subtopic containers, message bubbles
3. **Progress**: Subtopic completion indicators
4. **Badge**: Question count, completion status
5. **Alert**: Error messages (LLM failure, validation errors)

**Tailwind Setup**:
- Dev: Use CDN `<script src="https://cdn.tailwindcss.com"></script>` in base template
- Prod: Compile with `npx tailwindcss -i input.css -o static/css/output.css --minify` (optional)

**Alternatives Considered**:
- **Bootstrap**: Heavier, jQuery dependency (rejected per constitution)
- **Vanilla CSS**: Slower development, no pre-built accessibility features
- **DaisyUI**: Tailwind plugin, similar to shadcn but less control

---

## Session Resumption Strategy

### Decision: Checkpoint-based resumption with explicit user choice

**Approach** (FR-020):
1. **On app open**: Query `sessions` table for most recent `active` session
2. **If active session exists**: Show modal with two buttons
   - "Resume Session" → Load session, restore agent state from `agent_checkpoints`, render chat with history
   - "Start Fresh" → Mark old session as `abandoned`, create new session
3. **If no active session**: Go directly to syllabus selection

**Agent State Restoration**:
- LangGraph supports checkpointing: `graph.invoke(state, config={"checkpoint": checkpoint_data})`
- Store checkpoint as JSON in `agent_checkpoints.state_data`
- Restore on resume: deserialize JSON, pass to LangGraph

**Conversation History**:
- Load all `messages` for session from database
- Render in chat UI (scroll to bottom)
- Continue from last message

**Alternatives Considered**:
- **Always resume**: No user choice; annoying if student wants fresh start
- **Always fresh**: Loses progress; violates FR-020 requirement
- **Timeout-based**: Resume if < 1 hour old, else fresh; adds complexity (decision fatigue)

### In-Session Navigation: "+ New Chat" Button

**Requirement**: FR-021 - Students need ability to end current session and start a new topic without navigating away first

**Implementation**:
- Green "+ New Chat" button in chat interface header
- Confirmation dialog: "End this session and start a new topic? Your progress will be saved."
- On confirm: calls `/session/abandon` endpoint → redirects to homepage/syllabus
- Progress preserved (session marked as "abandoned", not deleted)

**UX Benefits**:
- Reduces friction when student wants to switch topics mid-session
- Clear visual affordance (green = new/create action)
- Confirmation prevents accidental termination
- Always visible in header (no need to hunt for exit)

---

## LLM Prompt Engineering

### Tutor Persona Prompt

```
You are a patient, encouraging GCSE mathematics tutor helping a student learn [SUBTOPIC_NAME].

Your teaching style:
- Start with clear explanations before asking questions
- When the student answers correctly, give brief praise and move forward
- When the student answers incorrectly, DON'T give the answer immediately
- Instead, ask a Socratic question to guide their thinking
- If they're still stuck after 2-3 hints, provide a step-by-step explanation
- Adapt your language to be friendly and age-appropriate (14-16 years old)
- Use examples and real-world connections when helpful

Current state: [STATE_NAME]
Conversation so far: [HISTORY]
Student's last answer: [ANSWER]

[STATE-SPECIFIC INSTRUCTION]
```

**State-Specific Instructions**:
- **exposition**: "Explain the concept of [SUBTOPIC]. Make it engaging and use an example."
- **questioning**: "Ask a question to test understanding of [SUBTOPIC]. Make it appropriate for GCSE level."
- **evaluation**: "Evaluate this answer: [ANSWER]. Respond with JSON: {correct: bool, feedback: str}"
- **diagnosis**: "The student got this wrong. Identify their misconception and provide a gentle hint."
- **socratic**: "Ask a guiding question to help them discover the right approach."

### Calculator Visibility Prompt

```
Classify this math question as NUMERICAL or NON_NUMERICAL.

NUMERICAL: Requires actual number computation (e.g., "Calculate 3/4 + 2/5", "What is 15% of 240?")
NON_NUMERICAL: Algebraic manipulation, proofs, concepts (e.g., "Simplify 2x + 3x", "Explain Pythagoras' theorem")

Question: [QUESTION_TEXT]

Answer with only one word: NUMERICAL or NON_NUMERICAL
```

---

## Deployment & Environment

### Decision: Local-first with simple production path

**Development**:
```bash
# Install dependencies
pip install fastapi uvicorn[standard] langraph openai pydantic

# Run Tailwind watcher (optional, or use CDN)
npx tailwindcss -i input.css -o static/css/output.css --watch

# Run FastAPI
uvicorn bloom.main:app --reload
```

**Production** (optional for demo):
```bash
# Use gunicorn with uvicorn workers
gunicorn bloom.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Environment Variables**:
- `OPENAI_API_KEY`: Required (no default)
- `DATABASE_PATH`: Optional (default: `bloom.db`)
- `LLM_MODEL`: Optional (default: `gpt-4o-mini`)
- `COMPLETION_THRESHOLD`: Optional (default: `3` correct answers for subtopic completion)

**Alternatives Considered**:
- **Docker**: Adds complexity; constitution says "avoid until deployment" (defer for now)
- **Cloud deployment**: Not needed for single-user demo; keep local

---

## Best Practices & Patterns

### Error Handling

**LLM API Failures** (FR-018):
```python
async def call_llm_with_retry(prompt: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await openai_client.chat.completions.create(...)
            return response
        except (APIError, Timeout) as e:
            if attempt == max_retries - 1:
                # Show friendly error in UI
                return {"error": "I'm having trouble connecting. Please try again."}
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

**Database Errors**:
- Wrap all DB operations in try/except
- Log errors (Python `logging` module)
- Return user-friendly messages in UI

### Performance Optimization

1. **Connection pooling**: Not needed (SQLite single-user)
2. **LLM streaming**: Use `stream=True` for perceived performance
3. **Caching**: Cache recent calculator visibility decisions (avoid redundant LLM calls)
4. **Lazy loading**: Load messages in chunks if history > 50 messages (unlikely for demo)

### Logging

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bloom")

# Log key events
logger.info(f"Session started: subtopic={subtopic_id}")
logger.info(f"Question asked: {question_text}")
logger.info(f"Answer evaluated: correct={is_correct}")
logger.error(f"LLM API failed: {error}")
```

---

## Summary of Key Decisions

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| LLM Provider | OpenAI GPT-4o-mini | Cost-effective, fast, good tutoring capabilities |
| Agent Framework | LangGraph | State machine built-in, less boilerplate than manual |
| Web Framework | FastAPI | Fast, async, minimal setup |
| Frontend | htmx + Tailwind | No build step, minimal JS, server-driven |
| Database | SQLite | Local, no setup, python stdlib |
| UI Components | shadcn/ui | Copy-paste, accessible, Tailwind-based |
| Calculator Logic | Minimal JS + server logging | Simple, server monitors for feedback |
| Session Resumption | Checkpoint + user choice | Balances UX with persistence requirement |
| Deployment | Local Python process | Simplest for demo; extend later if needed |

All decisions align with constitution's "simplicity first" and "rapid iteration" principles.

