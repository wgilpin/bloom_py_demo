# Quickstart Guide: Bloom GCSE Mathematics Tutor

**Last Updated**: 2025-11-24

This guide gets Bloom running locally in under 5 minutes.

---

## Prerequisites

- **Python 3.13+** installed
- **Git** (for cloning repo)
- **OpenAI API key** or **Anthropic API key** (get from [platform.openai.com](https://platform.openai.com/) or [console.anthropic.com](https://console.anthropic.com/))

**Optional**:
- Node.js (if compiling Tailwind CSS locally instead of using CDN)

---

## Quick Start (3 steps)

### 1. Install Dependencies

```bash
# Clone repository (if not already)
git clone <repo-url>
cd tutor_min_py

# Install Python dependencies
pip install fastapi uvicorn[standard] langgraph openai anthropic pydantic
```

**Alternative** (using `uv` for faster installs):
```bash
pip install uv
uv pip install fastapi uvicorn[standard] langgraph openai anthropic pydantic
```

---

### 2. Set Environment Variables

```bash
# Set your LLM API key
export OPENAI_API_KEY="sk-your-key-here"

# Optional: Anthropic Claude (if using instead of OpenAI)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Optional: Customize settings
export LLM_MODEL="gpt-4o-mini"  # Default
export COMPLETION_THRESHOLD="3"  # Questions correct to mark subtopic complete
export DATABASE_PATH="bloom.db"  # SQLite database file
```

**Windows (PowerShell)**:
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
```

**Windows (CMD)**:
```cmd
set OPENAI_API_KEY=sk-your-key-here
```

---

### 3. Run the Application

```bash
# From project root
uvicorn bloom.main:app --reload
```

Open browser: **http://localhost:8000**

🎉 **You're done!** The app will:
- Initialize the SQLite database automatically
- Show a prompt to load a syllabus (admin step)

---

## Admin Setup: Load Syllabus

Before students can use Bloom, an admin must load the GCSE syllabus.

### Option 1: Web UI (Simplest)

1. Navigate to **http://localhost:8000/admin**
2. Click "Upload Syllabus"
3. Select `syllabus_sample.json` (provided in repo)
4. Click "Load"
5. Verify success message: "Loaded 3 topics, 12 subtopics"

### Option 2: CLI (For automation)

```bash
curl -X POST http://localhost:8000/admin/syllabus/upload \
  -F "file=@syllabus_sample.json"
```

### Option 3: Python Script

```python
import requests

with open("syllabus_sample.json", "rb") as f:
    response = requests.post(
        "http://localhost:8000/admin/syllabus/upload",
        files={"file": f}
    )
print(response.json())
```

---

## Using Bloom (Student Workflow)

### First Visit

1. Open **http://localhost:8000**
2. See GCSE math syllabus with topics (Number, Algebra, Geometry, etc.)
3. Click a subtopic (e.g., "Operations with Fractions")
4. Start tutoring session

### Chat Interface

- Tutor explains the concept (exposition)
- Tutor asks a question
- Type your answer in the chat box
- Get feedback and progress to next question

### Calculator

- Appears automatically for numerical questions
- Click number buttons or type expression
- Press `=` to calculate
- Result recorded for tutor feedback

### Progress Tracking

- Return to home page (top-left logo/link)
- See progress indicators on each subtopic
- ✓ Green checkmark = subtopic complete (3-5 correct answers)
- 📊 Yellow progress bar = in progress

### Session Resumption

- Close app mid-session
- Reopen: Prompt appears with two options
  - **Resume Session**: Continue exactly where you left off
  - **Start Fresh**: Begin a new subtopic

---

## Troubleshooting

### "No API key found"

**Problem**: Missing `OPENAI_API_KEY` environment variable

**Solution**:
```bash
export OPENAI_API_KEY="sk-your-key-here"
# Then restart: uvicorn bloom.main:app --reload
```

---

### "No syllabus loaded"

**Problem**: Database is empty

**Solution**: Go to `/admin` and upload `syllabus_sample.json`

---

### "LLM API failure" in chat

**Problem**: OpenAI/Anthropic API is down or rate-limited

**Solution**:
1. Check API status: [status.openai.com](https://status.openai.com/)
2. Click "Retry" button in UI
3. If persistent, wait 30 seconds and try again

---

### Calculator not appearing

**Problem**: LLM might be classifying question incorrectly

**Workaround**: Type your numerical answer directly in chat (calculator not required)

**Debug**: Check logs for classification:
```bash
# Logs will show: "Calculator visibility: NUMERICAL / NON_NUMERICAL"
```

---

### Database corruption

**Problem**: SQLite file corrupted (rare)

**Solution**: Delete and restart
```bash
rm bloom.db
uvicorn bloom.main:app --reload
# Database will be recreated; reload syllabus
```

---

## Development Workflow

### Hot Reload (Recommended)

```bash
uvicorn bloom.main:app --reload
```

**Benefit**: File changes trigger automatic restart (no manual restart needed)

---

### Tailwind CSS (Optional)

**Using CDN (Default)**:
- No setup needed
- Tailwind loaded via `<script>` tag in templates

**Compiling Locally** (for production):
```bash
# Install Tailwind
npm install -D tailwindcss

# Watch mode (rebuilds on CSS changes)
npx tailwindcss -i bloom/static/css/input.css -o bloom/static/css/output.css --watch

# Production build (minified)
npx tailwindcss -i bloom/static/css/input.css -o bloom/static/css/output.css --minify
```

Update `base.html` to use compiled CSS:
```html
<link rel="stylesheet" href="/static/css/output.css">
```

---

### Running Tests (Optional)

Tests are optional per constitution. If written:

```bash
# Install pytest
pip install pytest

# Run tests
pytest tests/

# Run specific test
pytest tests/test_syllabus_validation.py
```

---

## Project Structure Quick Reference

```
tutor_min_py/
├── bloom/                    # Main application
│   ├── main.py              # FastAPI app entry
│   ├── database.py          # SQLite connection
│   ├── models.py            # Data models
│   ├── tutor_agent.py       # LangGraph agent
│   ├── routes/
│   │   ├── student.py       # Student endpoints
│   │   └── admin.py         # Admin endpoints
│   ├── templates/           # HTML templates (htmx)
│   │   ├── base.html
│   │   ├── syllabus.html
│   │   ├── chat.html
│   │   └── components/
│   └── static/
│       ├── css/
│       └── js/
├── bloom.db                  # SQLite database (created at runtime)
├── syllabus_sample.json      # Example GCSE syllabus
├── pyproject.toml            # Python dependencies
└── README.md                 # Project overview
```

---

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key |
| `ANTHROPIC_API_KEY` | *(optional)* | Anthropic API key (if using Claude) |
| `LLM_MODEL` | `gpt-4o-mini` | Model to use |
| `DATABASE_PATH` | `bloom.db` | SQLite database file path |
| `COMPLETION_THRESHOLD` | `3` | Correct answers needed for subtopic completion |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

### LLM Model Options

**OpenAI**:
- `gpt-4o-mini` (recommended for demo: fast + cheap)
- `gpt-4o` (more capable, slower, expensive)
- `gpt-4-turbo` (alternative)

**Anthropic**:
- `claude-3-5-sonnet-20241022` (excellent reasoning)
- `claude-3-haiku-20240307` (fast, cheap)

To switch models:
```bash
export LLM_MODEL="claude-3-5-sonnet-20241022"
export ANTHROPIC_API_KEY="sk-ant-..."
```

Then update `bloom/tutor_agent.py` to use Anthropic client instead of OpenAI.

---

## Sample Syllabus Format

See `syllabus_sample.json` for full example. Structure:

```json
{
  "title": "GCSE Mathematics (AQA)",
  "topics": [
    {
      "id": 1,
      "name": "Number",
      "description": "Number operations, fractions, percentages",
      "subtopics": [
        {
          "id": 101,
          "name": "Operations with Fractions",
          "description": "Adding, subtracting, multiplying, dividing fractions"
        }
      ]
    }
  ]
}
```

**Validation Rules**:
- Topics must have unique IDs
- Each topic must have at least 1 subtopic
- Subtopics must have unique IDs across entire syllabus
- Names are required, descriptions optional

---

## Performance Tuning

### LLM Response Speed

- **Model choice**: `gpt-4o-mini` is fastest (1-2 sec)
- **Streaming**: Enable in `tutor_agent.py` for perceived speed
- **Caching**: Recent calculator classifications cached (avoid redundant LLM calls)

### Database

- SQLite is extremely fast for demo scale (< 1000 messages)
- No optimization needed unless sessions exceed 50+ messages

---

## Deployment (Optional)

For local demo, no deployment needed. For sharing:

### Simple Production (Single Command)

```bash
# Install gunicorn
pip install gunicorn

# Run with 1 worker (SQLite limitation)
gunicorn bloom.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Cloud Options (Future)

- **Fly.io**: `fly launch` (single command deploy)
- **Railway**: Connect GitHub repo, auto-deploy
- **Render**: Point to repo, select "Web Service"

All require:
- `Procfile` or start command: `uvicorn bloom.main:app`
- Environment variables set in platform UI

---

## Next Steps

1. ✅ Run app locally (`uvicorn bloom.main:app --reload`)
2. ✅ Load sample syllabus via `/admin`
3. ✅ Test tutoring session (try fractions subtopic)
4. 📖 Read full [implementation plan](./plan.md)
5. 🛠️ Customize syllabus JSON for different topics
6. 🎨 Modify templates in `bloom/templates/` for UI changes

---

## Getting Help

- **OpenAPI Docs**: http://localhost:8000/docs (FastAPI auto-generated)
- **Database Schema**: See [data-model.md](./data-model.md)
- **API Reference**: See [contracts/api.yaml](./contracts/api.yaml)
- **Constitution**: Review [.specify/memory/constitution.md](../../.specify/memory/constitution.md) for design principles

---

## Common Commands Cheat Sheet

```bash
# Start app
uvicorn bloom.main:app --reload

# Load syllabus (curl)
curl -X POST http://localhost:8000/admin/syllabus/upload -F "file=@syllabus_sample.json"

# Reset all progress (for testing)
curl -X POST http://localhost:8000/admin/progress/reset

# View database
sqlite3 bloom.db "SELECT * FROM topics;"
sqlite3 bloom.db "SELECT * FROM progress;"

# Check active sessions
sqlite3 bloom.db "SELECT * FROM sessions WHERE state='active';"

# Tail logs
# (logs print to terminal where uvicorn is running)
```

---

**Happy tutoring! 🎓✨**

