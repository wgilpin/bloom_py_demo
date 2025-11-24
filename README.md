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

## Quick Start

### Prerequisites

- Python 3.13+
- API key from one of: OpenAI, Anthropic, Google AI, or xAI

### Installation

```bash
# Install dependencies
pip install -e .

# Or using uv (faster)
pip install uv
uv pip install -e .
```

### Configuration

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

### Run the Application

```bash
uvicorn bloom.main:app --reload
```

Open your browser to **http://localhost:8000**

### Admin Setup: Load Syllabus

Before students can use Bloom, load the GCSE mathematics syllabus:

1. Navigate to **http://localhost:8000/admin**
2. Click "Upload Syllabus"
3. Select `syllabus_sample.json`
4. Click "Load"

Alternatively, use the API:

```bash
curl -X POST http://localhost:8000/admin/syllabus/upload \
  -F "file=@syllabus_sample.json"
```

## Using Bloom

### Student Workflow

1. Open **http://localhost:8000**
2. Browse the GCSE mathematics syllabus (topics & subtopics)
3. Click a subtopic to start a tutoring session
4. Chat with the AI tutor:
   - Read concept explanations
   - Answer questions
   - Get feedback and hints
   - Use the integrated calculator for numerical problems
5. Track your progress on the home page

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

### "No API key found"

Set `OPENAI_API_KEY` environment variable and restart the app.

### "No syllabus loaded"

Navigate to `/admin` and upload `syllabus_sample.json`.

### "LLM API failure"

Check [status.openai.com](https://status.openai.com/) and click "Retry" in the UI.

### Calculator not appearing

Type your numerical answer directly in chat (calculator is optional).

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

