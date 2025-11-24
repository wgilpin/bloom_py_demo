# Data Model: Bloom GCSE Mathematics Tutor

**Date**: 2025-11-24  
**Database**: SQLite (`bloom.db`)

## Overview

The data model supports:
- **Syllabus management**: Two-level hierarchy (topics → subtopics)
- **Session persistence**: Full conversation state for resumption
- **Progress tracking**: Per-subtopic metrics with completion criteria
- **Agent state**: LangGraph checkpoints for stateful tutoring

All timestamps use ISO8601 format (`YYYY-MM-DDTHH:MM:SS.ffffff`).

---

## Entity Relationship Diagram

```
┌─────────────┐
│   topics    │
├─────────────┤
│ id (PK)     │
│ name        │
│ description │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────────┐         ┌────────────────┐
│   subtopics     ├────────►│   progress     │
├─────────────────┤   1:1   ├────────────────┤
│ id (PK)         │         │ subtopic_id(PK)│
│ topic_id (FK)   │         │ questions_*    │
│ name            │         │ is_complete    │
│ description     │         │ last_accessed  │
└────────┬────────┘         └────────────────┘
         │
         │ 1:N
         │
┌────────▼────────────┐
│     sessions        │
├─────────────────────┤
│ id (PK)             │
│ subtopic_id (FK)    │
│ state               │
│ created_at          │
│ updated_at          │
│ questions_*         │
└────────┬────────────┘
         │
    ┌────┴─────┬──────────────┬──────────────────┐
    │          │              │                  │
    │ 1:N      │ 1:N          │ 1:1              │
    │          │              │                  │
┌───▼────────┐ ┌──▼─────────────────┐  ┌────────▼──────────────┐
│  messages  │ │ calculator_history │  │  agent_checkpoints    │
├────────────┤ ├────────────────────┤  ├───────────────────────┤
│ id (PK)    │ │ id (PK)            │  │ session_id (PK, FK)   │
│ session_id │ │ session_id (FK)    │  │ state_data (JSON)     │
│ role       │ │ expression         │  └───────────────────────┘
│ content    │ │ result             │
│ timestamp  │ │ timestamp          │
└────────────┘ └────────────────────┘
```

---

## Table Schemas

### `topics`

Represents high-level GCSE math categories (e.g., "Number", "Algebra").

```sql
CREATE TABLE topics (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique topic identifier (from JSON) |
| name | TEXT | NOT NULL, UNIQUE | Topic name (e.g., "Algebra") |
| description | TEXT | | Brief description of topic |

**Indexes**: None (primary key auto-indexed by SQLite)

**Sample Data**:
```sql
INSERT INTO topics (id, name, description) VALUES
(1, 'Number', 'Number operations, fractions, percentages, ratio, and proportion'),
(2, 'Algebra', 'Algebraic expressions, equations, graphs, and sequences'),
(3, 'Geometry', 'Properties of shapes, angles, circles, and transformations');
```

---

### `subtopics`

Represents specific learning units within topics (e.g., "Operations with Fractions").

```sql
CREATE TABLE subtopics (
    id INTEGER PRIMARY KEY,
    topic_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE INDEX idx_subtopics_topic_id ON subtopics(topic_id);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique subtopic identifier (from JSON) |
| topic_id | INTEGER | NOT NULL, FOREIGN KEY | Parent topic ID |
| name | TEXT | NOT NULL | Subtopic name |
| description | TEXT | | Brief description |

**Indexes**: 
- `idx_subtopics_topic_id`: For efficient topic → subtopic queries

**Sample Data**:
```sql
INSERT INTO subtopics (id, topic_id, name, description) VALUES
(101, 1, 'Operations with Fractions', 'Adding, subtracting, multiplying, dividing fractions'),
(102, 1, 'Percentages', 'Calculating percentages, increase/decrease'),
(201, 2, 'Solving Linear Equations', 'Solving equations of the form ax + b = c');
```

---

### `sessions`

Represents a tutoring session focused on one subtopic.

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subtopic_id INTEGER NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('active', 'completed', 'abandoned')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    questions_attempted INTEGER NOT NULL DEFAULT 0,
    questions_correct INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_state ON sessions(state);
CREATE INDEX idx_sessions_subtopic ON sessions(subtopic_id);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique session ID |
| subtopic_id | INTEGER | NOT NULL, FOREIGN KEY | Which subtopic this session covers |
| state | TEXT | NOT NULL, CHECK | `active`, `completed`, or `abandoned` |
| created_at | TEXT | NOT NULL | ISO8601 timestamp of session start |
| updated_at | TEXT | NOT NULL | ISO8601 timestamp of last activity |
| questions_attempted | INTEGER | DEFAULT 0 | Count of questions student has seen |
| questions_correct | INTEGER | DEFAULT 0 | Count of correct answers |

**State Transitions**:
- **active**: Session in progress
- **completed**: Student finished (manually or after completion threshold)
- **abandoned**: Student started new session without completing old one

**Indexes**:
- `idx_sessions_state`: For finding active sessions (resumption check)
- `idx_sessions_subtopic`: For progress aggregation queries

---

### `messages`

Stores conversation history for each session.

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'tutor')),
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_session ON messages(session_id);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique message ID |
| session_id | INTEGER | NOT NULL, FOREIGN KEY | Which session this message belongs to |
| role | TEXT | NOT NULL, CHECK | `student` or `tutor` |
| content | TEXT | NOT NULL | Message text |
| timestamp | TEXT | NOT NULL | ISO8601 timestamp |

**Query Pattern** (load chat history):
```sql
SELECT role, content, timestamp 
FROM messages 
WHERE session_id = ? 
ORDER BY timestamp ASC;
```

**Indexes**:
- `idx_messages_session`: For efficient chat history loading

---

### `calculator_history`

Logs calculator operations for tutoring feedback.

```sql
CREATE TABLE calculator_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    expression TEXT NOT NULL,
    result TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_calculator_session ON calculator_history(session_id);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique history entry ID |
| session_id | INTEGER | NOT NULL, FOREIGN KEY | Which session |
| expression | TEXT | NOT NULL | What the student typed (e.g., "3/4 + 2/5") |
| result | TEXT | NOT NULL | Computed result (e.g., "1.35") or "Error" |
| timestamp | TEXT | NOT NULL | ISO8601 timestamp |

**Query Pattern** (tutor feedback on approach):
```sql
SELECT expression, result 
FROM calculator_history 
WHERE session_id = ? 
ORDER BY timestamp DESC 
LIMIT 5;
```

**Indexes**:
- `idx_calculator_session`: For recent calculation queries

---

### `progress`

Tracks per-subtopic progress and completion status.

```sql
CREATE TABLE progress (
    subtopic_id INTEGER PRIMARY KEY,
    questions_attempted INTEGER NOT NULL DEFAULT 0,
    questions_correct INTEGER NOT NULL DEFAULT 0,
    is_complete BOOLEAN NOT NULL DEFAULT 0,
    last_accessed TEXT,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| subtopic_id | INTEGER | PRIMARY KEY, FOREIGN KEY | Which subtopic |
| questions_attempted | INTEGER | DEFAULT 0 | Total questions attempted across all sessions |
| questions_correct | INTEGER | DEFAULT 0 | Total correct answers |
| is_complete | BOOLEAN | DEFAULT 0 | `1` if >= 3-5 correct answers (configurable threshold) |
| last_accessed | TEXT | | ISO8601 timestamp of last session on this subtopic |

**Completion Logic**:
```python
# After each answer evaluation
if questions_correct >= COMPLETION_THRESHOLD:  # 3-5 from config
    is_complete = 1
```

**Aggregation Query** (topic-level progress):
```sql
SELECT 
    t.id AS topic_id,
    t.name AS topic_name,
    COUNT(DISTINCT st.id) AS total_subtopics,
    SUM(p.is_complete) AS completed_subtopics,
    CAST(SUM(p.is_complete) AS FLOAT) / COUNT(DISTINCT st.id) * 100 AS completion_percent
FROM topics t
JOIN subtopics st ON st.topic_id = t.id
LEFT JOIN progress p ON p.subtopic_id = st.id
GROUP BY t.id;
```

---

### `agent_checkpoints`

Stores LangGraph agent state for session resumption.

```sql
CREATE TABLE agent_checkpoints (
    session_id INTEGER PRIMARY KEY,
    state_data TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| session_id | INTEGER | PRIMARY KEY, FOREIGN KEY | Which session |
| state_data | TEXT | NOT NULL | JSON blob of LangGraph state |

**State Data Structure** (JSON example):
```json
{
  "subtopic_id": 101,
  "current_state": "questioning",
  "messages": [...],
  "questions_correct": 2,
  "questions_attempted": 3,
  "calculator_visible": true,
  "last_student_answer": "1.35",
  "calculator_history": [
    {"expression": "3/4", "result": "0.75"},
    {"expression": "2/5", "result": "0.4"},
    {"expression": "0.75 + 0.4", "result": "1.15"}
  ]
}
```

**Usage**:
```python
# Save checkpoint
import json
checkpoint_data = json.dumps(state_dict)
cursor.execute("INSERT OR REPLACE INTO agent_checkpoints (session_id, state_data) VALUES (?, ?)", 
               (session_id, checkpoint_data))

# Restore checkpoint
cursor.execute("SELECT state_data FROM agent_checkpoints WHERE session_id = ?", (session_id,))
state_dict = json.loads(cursor.fetchone()[0])
```

---

## Data Access Patterns

### 1. Load Syllabus for Student View

```sql
SELECT 
    t.id AS topic_id,
    t.name AS topic_name,
    st.id AS subtopic_id,
    st.name AS subtopic_name,
    COALESCE(p.questions_correct, 0) AS correct,
    COALESCE(p.questions_attempted, 0) AS attempted,
    COALESCE(p.is_complete, 0) AS is_complete
FROM topics t
JOIN subtopics st ON st.topic_id = t.id
LEFT JOIN progress p ON p.subtopic_id = st.id
ORDER BY t.id, st.id;
```

### 2. Check for Active Session (Resumption)

```sql
SELECT id, subtopic_id, created_at
FROM sessions
WHERE state = 'active'
ORDER BY updated_at DESC
LIMIT 1;
```

### 3. Start New Session

```python
cursor.execute("""
    INSERT INTO sessions (subtopic_id, state, created_at, updated_at)
    VALUES (?, 'active', ?, ?)
""", (subtopic_id, now(), now()))
session_id = cursor.lastrowid
```

### 4. Update Progress After Answer

```python
# Update session counters
cursor.execute("""
    UPDATE sessions 
    SET questions_attempted = questions_attempted + 1,
        questions_correct = questions_correct + ?,
        updated_at = ?
    WHERE id = ?
""", (1 if is_correct else 0, now(), session_id))

# Update global progress
cursor.execute("""
    INSERT INTO progress (subtopic_id, questions_attempted, questions_correct, is_complete, last_accessed)
    VALUES (?, 1, ?, ?, ?)
    ON CONFLICT(subtopic_id) DO UPDATE SET
        questions_attempted = questions_attempted + 1,
        questions_correct = questions_correct + ?,
        is_complete = CASE WHEN questions_correct >= ? THEN 1 ELSE 0 END,
        last_accessed = ?
""", (subtopic_id, 1 if is_correct else 0, is_correct, now(), 
      1 if is_correct else 0, COMPLETION_THRESHOLD, now()))
```

### 5. Load Chat History for Session

```sql
SELECT role, content, timestamp
FROM messages
WHERE session_id = ?
ORDER BY timestamp ASC;
```

---

## Initialization Script

```python
import sqlite3
from pathlib import Path

def init_database(db_path: str = "bloom.db"):
    """Initialize database schema if not exists."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Create tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );
        
        CREATE TABLE IF NOT EXISTS subtopics (
            id INTEGER PRIMARY KEY,
            topic_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_subtopics_topic_id ON subtopics(topic_id);
        
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id INTEGER NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('active', 'completed', 'abandoned')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            questions_attempted INTEGER NOT NULL DEFAULT 0,
            questions_correct INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(state);
        CREATE INDEX IF NOT EXISTS idx_sessions_subtopic ON sessions(subtopic_id);
        
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'tutor')),
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
        
        CREATE TABLE IF NOT EXISTS calculator_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            expression TEXT NOT NULL,
            result TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_calculator_session ON calculator_history(session_id);
        
        CREATE TABLE IF NOT EXISTS progress (
            subtopic_id INTEGER PRIMARY KEY,
            questions_attempted INTEGER NOT NULL DEFAULT 0,
            questions_correct INTEGER NOT NULL DEFAULT 0,
            is_complete BOOLEAN NOT NULL DEFAULT 0,
            last_accessed TEXT,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS agent_checkpoints (
            session_id INTEGER PRIMARY KEY,
            state_data TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")
```

---

## Validation Rules

### Domain Constraints

1. **Progress Consistency**: `questions_correct` <= `questions_attempted` (enforced in application logic)
2. **Completion Threshold**: `is_complete = 1` IFF `questions_correct >= COMPLETION_THRESHOLD` (default 3)
3. **Session State**: Only one `active` session recommended per student (soft constraint)
4. **Timestamps**: All timestamps in ISO8601 format, UTC preferred

### Referential Integrity

- Foreign keys enforced via `PRAGMA foreign_keys = ON`
- CASCADE deletes: Removing a topic deletes its subtopics, sessions, and related data

---

## Migration Strategy

**Initial Load** (from syllabus JSON):
1. Clear existing topics/subtopics (if reloading)
2. Insert topics from JSON
3. Insert subtopics from JSON
4. **Preserve existing progress**: Do NOT delete `progress` table on reload

**Schema Evolution** (future):
- Use Alembic or manual migration scripts
- For demo, drop and recreate database is acceptable

---

## Performance Considerations

### Query Optimization

- **Indexes**: Cover most common queries (session lookups, message loading, progress aggregation)
- **No N+1 queries**: Use JOINs to load topic → subtopic → progress in single query
- **Pagination**: Not needed for demo scale (< 100 subtopics)

### Storage Estimates

- **Topics**: ~10 rows × 200 bytes = 2 KB
- **Subtopics**: ~50 rows × 300 bytes = 15 KB
- **Sessions**: ~20 rows × 200 bytes = 4 KB
- **Messages**: ~500 rows × 500 bytes = 250 KB (largest table)
- **Total**: < 1 MB for demo usage

SQLite handles this scale trivially (supports databases up to 281 TB).

---

## Security & Privacy

### Data Sensitivity

- **No PII**: No names, emails, or identifiable information stored
- **Local-only**: Database file remains on user's machine (no server sync)
- **LLM Data**: Conversation sent to LLM provider (OpenAI/Anthropic) per their ToS

### Admin Access

- Admin can load new syllabus (replaces topics/subtopics)
- Admin cannot access student conversation history (out of scope for demo)
- For production: Add admin authentication, encrypt sensitive fields

---

## Testing Considerations

### Test Data Setup

```python
def seed_test_data():
    """Insert sample syllabus for testing."""
    conn = sqlite3.connect("bloom_test.db")
    cursor = conn.cursor()
    
    # Sample topics
    cursor.executemany("INSERT INTO topics (id, name, description) VALUES (?, ?, ?)", [
        (1, "Number", "Number operations"),
        (2, "Algebra", "Equations and expressions")
    ])
    
    # Sample subtopics
    cursor.executemany("INSERT INTO subtopics (id, topic_id, name, description) VALUES (?, ?, ?, ?)", [
        (101, 1, "Fractions", "Adding/subtracting fractions"),
        (102, 1, "Percentages", "Percentage calculations"),
        (201, 2, "Linear Equations", "Solving ax + b = c")
    ])
    
    conn.commit()
    conn.close()
```

### Assertions (if writing tests)

- Verify foreign key constraints trigger on invalid inserts
- Check progress updates correctly after answer evaluation
- Ensure session resumption loads correct agent state

---

## Summary

This data model supports all spec requirements:
- ✓ FR-001/002: Syllabus storage (topics + subtopics)
- ✓ FR-008: Progress tracking per subtopic
- ✓ FR-009: Persistence via SQLite
- ✓ FR-012: Calculator history logging
- ✓ FR-020: Session resumption via agent_checkpoints

Design prioritizes simplicity (normalized schema, minimal indexes) and aligns with constitution's "no ORM" constraint (raw SQL via sqlite3).

