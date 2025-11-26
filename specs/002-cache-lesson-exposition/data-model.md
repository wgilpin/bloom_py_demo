# Data Model: Cache Lesson Exposition

**Date**: 2025-11-25  
**Database**: SQLite (`bloom.db`)  
**Related**: Extends existing schema documented in `/specs/001-bloom-tutor-app/data-model.md`

## Overview

This feature adds a single table (`cached_expositions`) to the existing Bloom database schema. The table stores LLM-generated lesson expositions indexed by subtopic ID, enabling fast retrieval and API cost reduction.

All timestamps use ISO8601 format (`YYYY-MM-DDTHH:MM:SS.ffffff`).

---

## Schema Changes

### New Table: `cached_expositions`

Stores generated lesson expositions for reuse across sessions.

```sql
CREATE TABLE IF NOT EXISTS cached_expositions (
    subtopic_id INTEGER PRIMARY KEY,
    exposition_content TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    model_identifier TEXT NOT NULL,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| subtopic_id | INTEGER | PRIMARY KEY, FOREIGN KEY | Unique subtopic ID (links to `subtopics.id`) |
| exposition_content | TEXT | NOT NULL | Full text of the cached exposition (~800-1200 words, ~3-4KB) |
| generated_at | TEXT | NOT NULL | ISO8601 timestamp when exposition was generated |
| model_identifier | TEXT | NOT NULL | LLM model used (e.g., "gpt-4", "claude-3-5-sonnet-20241022") |

**Indexes**: None needed (all lookups by primary key)

**Foreign Key Behavior**:
- `ON DELETE CASCADE`: If a subtopic is removed, its cached exposition is automatically deleted
- Ensures referential integrity with syllabus

**Sample Data**:
```sql
INSERT INTO cached_expositions (subtopic_id, exposition_content, generated_at, model_identifier) VALUES
(101, 
 'Welcome to Operations with Fractions! Let''s explore how to work with fractions step by step...', 
 '2025-11-25T10:30:00.000000',
 'gpt-4'),
(102, 
 'Today we''ll learn about Percentages, a powerful way to express proportions...', 
 '2025-11-25T10:31:15.000000',
 'claude-3-5-sonnet-20241022');
```

---

## Entity Relationship Diagram (Updated)

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
┌──────▼──────────┐       ┌─────────────────────┐       ┌────────────────┐
│   subtopics     ├───────►│ cached_expositions  │       │   progress     │
├─────────────────┤  1:1   ├─────────────────────┤       ├────────────────┤
│ id (PK)         │  NEW   │ subtopic_id (PK,FK) │       │ subtopic_id(PK)│
│ topic_id (FK)   │◄───────┤ exposition_content  │       │ questions_*    │
│ name            │        │ generated_at        │       │ is_complete    │
│ description     │        │ model_identifier    │       │ last_accessed  │
└────────┬────────┘        └─────────────────────┘       └────────────────┘
         │
         │ 1:N
         │
┌────────▼────────────┐
│     sessions        │
├─────────────────────┤
│ id (PK)             │
│ subtopic_id (FK)    │
│ ...                 │
└─────────────────────┘
```

**New Relationship**: `subtopics` → `cached_expositions` (1:1, optional)
- Each subtopic has at most one cached exposition
- Subtopic can exist without cached exposition (cache miss scenario)

---

## Data Access Patterns

### 1. Check for Cached Exposition (Cache Lookup)

**Use Case**: Before generating exposition, check if it's already cached

```sql
SELECT exposition_content, generated_at, model_identifier
FROM cached_expositions
WHERE subtopic_id = ?;
```

**Expected Performance**: < 5ms (primary key lookup)

**Python Implementation**:
```python
def get_cached_exposition(subtopic_id: int, db_path: str = "bloom.db") -> Optional[dict]:
    """Retrieve cached exposition for a subtopic.
    
    Args:
        subtopic_id: Subtopic ID to look up
        db_path: Path to database file
        
    Returns:
        Dict with keys {exposition_content, generated_at, model_identifier} or None if not cached
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT exposition_content, generated_at, model_identifier
        FROM cached_expositions
        WHERE subtopic_id = ?
    """, (subtopic_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "exposition_content": row["exposition_content"],
            "generated_at": row["generated_at"],
            "model_identifier": row["model_identifier"],
        }
    return None
```

---

### 2. Save Generated Exposition (Cache Write)

**Use Case**: After LLM generates new exposition, save it for future reuse

```sql
INSERT OR REPLACE INTO cached_expositions 
(subtopic_id, exposition_content, generated_at, model_identifier)
VALUES (?, ?, ?, ?);
```

**Expected Performance**: < 10ms (single INSERT with small payload ~3KB)

**Python Implementation**:
```python
def save_cached_exposition(
    subtopic_id: int,
    content: str,
    model_identifier: str,
    db_path: str = "bloom.db"
) -> None:
    """Save generated exposition to cache.
    
    Args:
        subtopic_id: Subtopic ID this exposition belongs to
        content: Full text of the exposition
        model_identifier: LLM model used (e.g., "gpt-4")
        db_path: Path to database file
    """
    from datetime import datetime
    
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO cached_expositions 
        (subtopic_id, exposition_content, generated_at, model_identifier)
        VALUES (?, ?, ?, ?)
    """, (subtopic_id, content, datetime.utcnow().isoformat(), model_identifier))
    
    conn.commit()
    conn.close()
```

**Note**: `INSERT OR REPLACE` handles both first-time caching and updates to existing cache entries (e.g., manual refresh).

---

### 3. Admin Cache Management (Manual Operations)

**Clear All Cache**:
```sql
DELETE FROM cached_expositions;
```

**Clear Specific Subtopic**:
```sql
DELETE FROM cached_expositions WHERE subtopic_id = ?;
```

**Clear by Model** (e.g., after switching from GPT-4 to Claude):
```sql
DELETE FROM cached_expositions WHERE model_identifier = 'gpt-4';
```

**Clear Old Entries** (example for future use):
```sql
DELETE FROM cached_expositions WHERE generated_at < '2025-01-01';
```

**List Cached Subtopics** (diagnostic query):
```sql
SELECT 
    ce.subtopic_id,
    st.name AS subtopic_name,
    ce.model_identifier,
    ce.generated_at,
    LENGTH(ce.exposition_content) AS content_size_bytes
FROM cached_expositions ce
JOIN subtopics st ON st.id = ce.subtopic_id
ORDER BY ce.generated_at DESC;
```

---

## Database Initialization

Add the new table creation to `bloom/database.py`:

```python
def init_database(db_path: str = "bloom.db") -> None:
    """Initialize database schema if not exists."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.executescript("""
        -- Existing tables (topics, subtopics, sessions, etc.)
        ...
        
        -- NEW: Cached expositions for API cost reduction
        CREATE TABLE IF NOT EXISTS cached_expositions (
            subtopic_id INTEGER PRIMARY KEY,
            exposition_content TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            model_identifier TEXT NOT NULL,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        );
    """)
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {db_path}")
```

---

## Migration Strategy

### For Existing Deployments

**Step 1**: Add table to existing database (idempotent via `IF NOT EXISTS`)
```bash
python -c "from bloom.database import init_database; init_database()"
```

**Step 2**: No data migration needed (cache starts empty, fills on first use)

**Step 3**: Verify table created
```bash
sqlite3 bloom.db ".schema cached_expositions"
```

### Rollback Strategy

If caching causes issues, the feature can be disabled without data loss:

**Option 1**: Drop table
```sql
DROP TABLE IF EXISTS cached_expositions;
```

**Option 2**: Keep table but bypass cache (modify code to always generate new)
```python
# In exposition_node(), comment out cache check
# cached = get_cached_exposition(subtopic_id)  # DISABLED
cached = None  # Force cache miss
```

---

## Performance Considerations

### Storage Estimates

| Metric | Value |
|--------|-------|
| Subtopics in GCSE math syllabus | ~50-100 |
| Avg exposition size (text) | ~3-4 KB |
| Metadata overhead per row | ~50 bytes |
| **Total cache size (100 subtopics)** | **~300-400 KB** |

**Conclusion**: Storage overhead is negligible (< 0.5 MB for full syllabus cache).

### Query Performance

| Operation | Method | Expected Latency |
|-----------|--------|------------------|
| Cache lookup | Primary key SELECT | < 5 ms |
| Cache write | INSERT OR REPLACE | < 10 ms |
| Cache clear | DELETE | < 50 ms |

**Conclusion**: Cache operations add negligible latency compared to LLM API calls (~3000 ms).

### Cache Hit Ratio Projections

**Scenario**: 100 students, 10 subtopics each, over 1 day

| Metric | No Cache | With Cache (90% hit rate) |
|--------|----------|---------------------------|
| Total requests | 1000 | 1000 |
| LLM API calls | 1000 | 100 (first unique subtopics) |
| Cached retrievals | 0 | 900 |
| Avg session start time | ~3s | ~0.5s (90% of time) |
| API cost (est.) | $1.00 | $0.10 |

**Conclusion**: Cache provides 10x cost reduction and 6x speed improvement for typical usage.

---

## Validation Rules

### Domain Constraints

1. **Content Non-Empty**: `exposition_content` MUST NOT be empty string (enforced by NOT NULL + application logic)
2. **Timestamp Format**: `generated_at` MUST be valid ISO8601 (enforced by application, not database)
3. **Model Identifier**: MUST match pattern from LLM_MODEL config (no validation for demo, trust config)
4. **Subtopic Exists**: `subtopic_id` MUST reference existing subtopic (enforced by FOREIGN KEY)

### Referential Integrity

- Foreign key to `subtopics` enforced via `PRAGMA foreign_keys = ON`
- Deleting a subtopic cascades to delete its cached exposition
- Deleting a topic cascades to delete subtopics and their cached expositions

---

## Security & Privacy

### Data Sensitivity

- **No PII**: Cached expositions contain only educational content (no student data)
- **LLM Content**: Same privacy considerations as original LLM API usage
- **Local Storage**: Cache stored in local SQLite database (no external sync)

### Cache Poisoning Risk

- **Low Risk**: Only application code writes to cache (no user input)
- **Mitigation**: If corruption suspected, admin can delete and regenerate

---

## Testing Considerations

### Test Database Setup

```python
def test_cached_expositions():
    """Test cache storage and retrieval."""
    TEST_DB = "bloom_test.db"
    
    # Initialize schema
    init_database(TEST_DB)
    
    # Seed test subtopic
    conn = get_connection(TEST_DB)
    conn.execute("INSERT INTO topics (id, name) VALUES (1, 'Test Topic')")
    conn.execute("INSERT INTO subtopics (id, topic_id, name) VALUES (101, 1, 'Test Subtopic')")
    conn.commit()
    conn.close()
    
    # Test cache write
    save_cached_exposition(101, "Test exposition content", "gpt-4", TEST_DB)
    
    # Test cache read
    cached = get_cached_exposition(101, TEST_DB)
    assert cached is not None
    assert cached["exposition_content"] == "Test exposition content"
    assert cached["model_identifier"] == "gpt-4"
    
    # Test cache miss
    cached = get_cached_exposition(999, TEST_DB)
    assert cached is None
```

---

## Summary

This data model extends the existing Bloom schema with minimal changes:

- ✅ **1 new table** (`cached_expositions`)
- ✅ **3 new functions** (init, get, save)
- ✅ **< 500KB storage** for full syllabus
- ✅ **< 10ms latency** per cache operation
- ✅ **90% cost reduction** for typical usage
- ✅ **Foreign key integrity** maintained
- ✅ **Simple migration** (idempotent table creation)

Design aligns with constitution's simplicity principles: no ORM, direct SQL, minimal abstraction.


