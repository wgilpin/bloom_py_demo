# Bloom GCSE Mathematics Tutor

**AI-powered tutoring for UK GCSE mathematics using LLM agents**

Bloom is an interactive mathematics tutor that uses LangGraph-powered AI agents to deliver personalized, Socratic tutoring through a chat interface. Students can work through the GCSE curriculum at their own pace, with context-aware tools like an integrated calculator that appears automatically for numerical problems.

## Features

- ✅ **Interactive Chat Tutoring** - AI tutor explains concepts, asks questions, and provides feedback
- ✅ **GCSE Syllabus Navigation** - Browse topics and subtopics, track progress
- ✅ **Context-Aware Calculator** - Appears for numerical problems, hidden for algebra
- ✅ **Progress Tracking** - Track completion across subtopics with persistent data
- ✅ **Session Resumption** - Pick up exactly where you left off
- ✅ **Socratic Teaching** - Guided discovery through hints and questions
- ✅ **Smart Caching** - Lesson expositions cached for instant loading and 90% cost reduction

## Quick Start

### Prerequisites

- Python 3.13+
- API key from one of: OpenAI, Anthropic, Google AI, or xAI

### Installation

```bash
# Install dependencies using uv
uv sync
```

### Configuration

Create a `.env` file from the template:

```bash
# Copy the example file
cp env.example .env

# Edit .env with your API key
# The file includes detailed comments for each variable
```

Or set environment variables directly:

```bash
# Choose your LLM provider (default: openai)
export LLM_PROVIDER="openai"  # Options: openai, anthropic, google, xai

# Set API key for your chosen provider
export OPENAI_API_KEY="sk-your-key-here"           # For OpenAI
export ANTHROPIC_API_KEY="sk-ant-your-key-here"    # For Anthropic
export GOOGLE_API_KEY="your-google-key"            # For Google Gemini
export XAI_API_KEY="xai-your-key"                  # For xAI Grok

# Optional: Customize settings
export LLM_MODEL="gpt-4o-mini"  # Model name (provider-specific)
export COMPLETION_THRESHOLD="3"  # Correct answers for subtopic completion
export DATABASE_PATH="bloom.db"  # SQLite database file
```

### Database Setup (Required Before First Use)

**Load the sample GCSE syllabus into the database:**

```bash
# Initialize database and load sample syllabus
uv run python -m bloom.load_syllabus
```

This will:
- ✓ Create the SQLite database (`bloom.db`)
- ✓ Load 3 topics: Number, Algebra, Geometry
- ✓ Load 10 subtopics with descriptions

**Note:** You must run this command before starting the application for the first time. Without the syllabus data, you'll get "FOREIGN KEY constraint failed" errors when trying to start a tutoring session.

### Run the Application

```bash
# Start the development server
uv run uvicorn bloom.main:app --reload

# Or use FastAPI dev mode
uv run fastapi dev bloom/main.py
```

Open your browser to **http://localhost:8000**

## Using Bloom

### Student Workflow

1. Open **http://localhost:8000**
2. Browse the GCSE mathematics syllabus (topics & subtopics)
3. Click a subtopic to start a tutoring session
4. Chat with the AI tutor:
   - Read concept explanations (first time: ~3s to generate, subsequent: instant from cache)
   - Answer questions
   - Get feedback and hints
   - Use the integrated calculator for numerical problems
5. Track your progress on the home page

**Note**: The first time you or any student accesses a subtopic, it takes ~3 seconds to generate the lesson. After that, all future sessions on that subtopic load instantly thanks to smart caching.

### Session Resumption

If you close the app mid-session, you'll see two options when you return:
- **Resume Session**: Continue exactly where you left off
- **Start Fresh**: Begin a new subtopic

## Tech Stack

- **Backend**: FastAPI (Python 3.13+)
- **Frontend**: htmx + Tailwind CSS + shadcn/ui
- **Agent Framework**: LangGraph (5-state tutoring state machine)
- **LLM**: OpenAI GPT-4o-mini (or Anthropic Claude)
- **Database**: SQLite (local persistence)
- **Deployment**: Single Python process (uvicorn)

## Project Structure

```
bloom/
├── main.py                    # FastAPI app entry point
├── database.py                # SQLite schema and queries
├── models.py                  # Pydantic data models
├── tutor_agent.py             # LangGraph agent (5 tutoring states)
├── routes/
│   ├── student.py             # Chat, syllabus, calculator endpoints
│   └── admin.py               # Syllabus management
├── templates/                 # htmx HTML templates
│   ├── base.html
│   ├── syllabus.html
│   ├── chat.html
│   └── components/
└── static/
    ├── css/                   # Tailwind CSS
    └── js/                    # Calculator widget
```

## Development

### Hot Reload

```bash
uvicorn bloom.main:app --reload
```

File changes trigger automatic restart.

### Tailwind CSS

**Development** (using CDN):
- No setup needed, Tailwind loaded via `<script>` tag in templates

**Production** (optional compilation):
```bash
npm install -D tailwindcss
npx tailwindcss -i bloom/static/css/input.css -o bloom/static/css/output.css --minify
```

### Database

**View database**:
```bash
sqlite3 bloom.db "SELECT * FROM topics;"
sqlite3 bloom.db "SELECT * FROM progress;"
```

**Reset progress** (for testing):
```bash
curl -X POST http://localhost:8000/admin/progress/reset
```

### Cache Management

**Performance Optimization**: Lesson expositions are automatically cached to reduce LLM API costs by ~90% and improve session start times from ~3 seconds to < 0.5 seconds.

**How it works**:
- **First time** accessing a subtopic: Generates exposition via LLM and caches it
- **Subsequent times**: Retrieves cached exposition instantly (no API call)
- **Cache storage**: Each exposition ~3-4KB, total cache < 500KB for full syllabus

**View cached expositions**:
```bash
sqlite3 bloom.db "SELECT subtopic_id, model_identifier, generated_at FROM cached_expositions;"
```

**View cache statistics**:
```bash
sqlite3 bloom.db "SELECT COUNT(*) as cached_subtopics, SUM(LENGTH(exposition_content)) as total_bytes FROM cached_expositions;"
```

**Clear cache** (force regeneration):
```bash
# Clear all cached expositions
sqlite3 bloom.db "DELETE FROM cached_expositions;"

# Clear specific subtopic
sqlite3 bloom.db "DELETE FROM cached_expositions WHERE subtopic_id = 202;"

# Clear by model (after switching LLM providers)
sqlite3 bloom.db "DELETE FROM cached_expositions WHERE model_identifier = 'gpt-4';"
```

**When to clear cache**:
- After changing `LLM_MODEL` or `LLM_PROVIDER` (to regenerate with new model)
- If you notice quality issues with a cached exposition
- For testing fresh generations

## Architecture

### Tutoring Agent (LangGraph)

Bloom uses a 5-state agent to manage the tutoring flow:

1. **Exposition**: Explain mathematical concepts
2. **Questioning**: Generate appropriate GCSE-level questions
3. **Evaluation**: Assess answer correctness (correct/partial/incorrect)
4. **Diagnosis**: Identify student misconceptions
5. **Socratic**: Ask guiding questions to help discovery

The agent transitions fluidly between states based on conversation context.

### Database Schema

- **topics** - High-level math categories (Number, Algebra, Geometry)
- **subtopics** - Specific learning units (Operations with Fractions, etc.)
- **sessions** - Tutoring sessions with state tracking
- **messages** - Chat conversation history
- **progress** - Per-subtopic completion tracking
- **calculator_history** - Logged calculations for tutor feedback
- **agent_checkpoints** - LangGraph state for session resumption
- **cached_expositions** - Cached lesson expositions for cost reduction and performance

See [specs/001-bloom-tutor-app/data-model.md](specs/001-bloom-tutor-app/data-model.md) for full schema.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider: `openai`, `anthropic`, `google`, or `xai` |
| `OPENAI_API_KEY` | *(required if provider=openai)* | OpenAI API key |
| `ANTHROPIC_API_KEY` | *(required if provider=anthropic)* | Anthropic API key |
| `GOOGLE_API_KEY` | *(required if provider=google)* | Google AI API key |
| `XAI_API_KEY` | *(required if provider=xai)* | xAI API key |
| `LLM_MODEL` | `gpt-4o-mini` | Model name (provider-specific) |
| `DATABASE_PATH` | `bloom.db` | SQLite database file path |
| `COMPLETION_THRESHOLD` | `3` | Correct answers for subtopic completion |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

### LLM Models

**OpenAI** (`LLM_PROVIDER=openai`):
- `gpt-4o-mini` ✓ Recommended (fast, affordable)
- `gpt-4o` (more capable, expensive)
- `gpt-4-turbo` (alternative)

**Anthropic** (`LLM_PROVIDER=anthropic`):
- `claude-3-5-sonnet-20241022` (excellent reasoning)
- `claude-3-haiku-20240307` (fast, affordable)

**Google Gemini** (`LLM_PROVIDER=google`):
- `gemini-1.5-flash` ✓ Recommended (very affordable)
- `gemini-1.5-pro` (more capable)

**xAI Grok** (`LLM_PROVIDER=xai`):
- `grok-beta` (competitive pricing)

**Example - Switch to Google Gemini**:
```bash
export LLM_PROVIDER="google"
export GOOGLE_API_KEY="your-google-key"
export LLM_MODEL="gemini-1.5-flash"
```

## Troubleshooting

### "FOREIGN KEY constraint failed" when starting a session

**Problem:** The database doesn't have syllabus data loaded yet.

**Solution:** Run the database setup command:

```bash
uv run python -m bloom.load_syllabus
```

This must be done before using the app for the first time.

### "No API key found" or API key warnings

**Problem:** Missing or incorrect API key for your chosen LLM provider.

**Solution:** 
1. Check your `.env` file or environment variables
2. Ensure `LLM_PROVIDER` matches your API key (e.g., if `LLM_PROVIDER=google`, you need `GOOGLE_API_KEY`)
3. Restart the server after changing environment variables

### "LLM API failure" or timeout errors

**Problem:** LLM service unavailable or rate limited.

**Solution:**
1. Check the provider's status page:
   - OpenAI: [status.openai.com](https://status.openai.com/)
   - Anthropic: [status.anthropic.com](https://status.anthropic.com/)
   - Google: [status.cloud.google.com](https://status.cloud.google.com/)
2. Click the "🔄 Retry" button in the chat interface
3. Wait a moment and try again

### Calculator not appearing

**Problem:** Calculator only shows for numerical problems (by design).

**Solution:** This is expected behavior! Type your numerical answer directly in chat - the calculator is optional. It appears automatically for questions requiring calculation (e.g., "Calculate 3/4 + 2/5") but hides for algebraic questions (e.g., "Simplify 2x + 3x").

### Port already in use (Address already in use)

**Problem:** Another process is using port 8000.

**Solution:**
```bash
# Use a different port
uv run uvicorn bloom.main:app --reload --port 8001

# Or find and kill the process using port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

## Documentation

- [Feature Specification](specs/001-bloom-tutor-app/spec.md)
- [Implementation Plan](specs/001-bloom-tutor-app/plan.md)
- [Data Model](specs/001-bloom-tutor-app/data-model.md)
- [API Contracts](specs/001-bloom-tutor-app/contracts/api.yaml)
- [Research Decisions](specs/001-bloom-tutor-app/research.md)
- [Quickstart Guide](specs/001-bloom-tutor-app/quickstart.md)

## License

MIT

## Contributing

This is a demo project focused on rapid development. See [.specify/memory/constitution.md](.specify/memory/constitution.md) for design principles.

