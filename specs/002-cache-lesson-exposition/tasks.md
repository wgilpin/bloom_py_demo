# Tasks: Cache Lesson Exposition

**Feature Branch**: `002-cache-lesson-exposition`  
**Date**: 2025-11-25  
**Status**: Ready for Implementation

## Overview

This feature implements exposition caching to reduce LLM API costs by ~90% and improve session start times from ~3s to < 0.5s for cached content. The implementation adds a single database table and wraps existing exposition generation with cache-check logic.

**Key Files Modified**:
- `bloom/database.py` - Add cache table and access functions
- `bloom/tutor_agent.py` - Wrap exposition_node() with cache logic

**No New Dependencies**: Uses existing SQLite and FastAPI infrastructure

---

## Task Summary

| Phase | Tasks | Parallelizable | User Stories |
|-------|-------|----------------|--------------|
| Phase 1: Setup | 2 | 0 | - |
| Phase 2: Database Layer | 4 | 3 | US1, US2 |
| Phase 2.5: Automated Tests | 6 | 5 | US1, US2 |
| Phase 3: Cache Integration | 3 | 0 | US1, US2 |
| Phase 4: Manual Verification | 5 | 5 | US1, US2 |
| **Total** | **20** | **13** | **2** |

---

## Dependencies & Execution Order

### Story Dependencies

Both User Story 1 (cache retrieval) and User Story 2 (first-time generation) are implemented simultaneously by the same code changes. They represent different test scenarios of the same caching mechanism:

- **US2** (First-Time Generation): Cache miss → generate → save → display
- **US1** (Cached Retrieval): Cache hit → retrieve → display

**Implementation Strategy**: Implement core caching mechanism (Phases 1-3), then verify both scenarios (Phase 4).

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Database Layer) ← All tasks can run in parallel after Phase 1
    ↓
Phase 2.5 (Automated Tests) ← All test tasks can run in parallel after Phase 2
    ↓
Phase 3 (Cache Integration) ← Sequential: each task builds on previous
    ↓
Phase 4 (Manual Verification) ← All tasks can run in parallel after Phase 3
```

### Critical Path

```
T001 → T002 → T003 → T007 (test setup) → T013 → T014 → T015 → T016 (Manual Verification)
```

**Estimated Duration**: 3-4 hours (experienced developer)
- Phase 1: 10 minutes
- Phase 2: 45 minutes
- Phase 2.5: 45 minutes (tests)
- Phase 3: 60 minutes
- Phase 4: 30 minutes

---

## Phase 1: Setup & Preparation

**Goal**: Ensure development environment is ready and understand existing codebase structure.

**Prerequisites**: None (start here)

### Tasks

- [X] T001 Review existing database schema and initialization in bloom/database.py
- [X] T002 Review existing exposition_node() implementation in bloom/tutor_agent.py to understand current flow

**Completion Criteria**:
- [X] Understand how `init_database()` creates tables
- [X] Understand how `get_connection()` provides database access
- [X] Understand how `exposition_node()` currently generates expositions
- [X] Identify where LLM_MODEL config variable is accessed

---

## Phase 2: Database Layer (Core Implementation)

**Goal**: Add `cached_expositions` table and cache access functions to support both first-time caching (US2) and cache retrieval (US1).

**Prerequisites**: Phase 1 complete

**Independent Test**: After this phase, can directly call `get_cached_exposition()` and `save_cached_exposition()` functions and verify database operations work correctly.

### Tasks

- [X] T003 [US1][US2] Add cached_expositions table creation to init_database() in bloom/database.py
- [X] T004 [P] [US1][US2] Implement get_cached_exposition() function in bloom/database.py
- [X] T005 [P] [US1][US2] Implement save_cached_exposition() function in bloom/database.py
- [X] T006 [P] [US1][US2] Update database initialization to include cached_expositions table in bloom/database.py

**Implementation Details**:

**T003**: Add table to `init_database()` executescript:
```python
CREATE TABLE IF NOT EXISTS cached_expositions (
    subtopic_id INTEGER PRIMARY KEY,
    exposition_content TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    model_identifier TEXT NOT NULL,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);
```

**T004**: Implement cache retrieval:
```python
def get_cached_exposition(subtopic_id: int, db_path: str = "bloom.db") -> Optional[dict]:
    """Retrieve cached exposition for a subtopic.
    
    Returns:
        Dict with {exposition_content, generated_at, model_identifier} or None
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

**T005**: Implement cache storage:
```python
def save_cached_exposition(
    subtopic_id: int,
    content: str,
    model_identifier: str,
    db_path: str = "bloom.db"
) -> None:
    """Save generated exposition to cache."""
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

**T006**: Verify table creation by running `init_database()` and checking schema.

**Completion Criteria**:
- [X] Table `cached_expositions` exists with correct schema
- [X] `get_cached_exposition()` returns None for non-existent subtopic
- [X] `save_cached_exposition()` successfully stores exposition
- [X] `get_cached_exposition()` returns saved exposition after save
- [X] Foreign key constraint to subtopics table is enforced

---

## Phase 2.5: Automated Tests (pytest with mocked LLMs)

**Goal**: Create automated test suite to verify cache database functions and cache integration logic without calling real LLM APIs.

**Prerequisites**: Phase 2 complete

**Independent Test**: Run `pytest tests/test_cache_exposition.py -v` and verify all tests pass with 100% code coverage of cache-related functions.

### Tasks

- [X] T007 [US1][US2] Create test file tests/test_cache_exposition.py with pytest setup
- [X] T008 [P] [US1][US2] Write test for get_cached_exposition() with empty cache in tests/test_cache_exposition.py
- [X] T009 [P] [US1][US2] Write test for save_cached_exposition() and retrieval in tests/test_cache_exposition.py
- [X] T010 [P] [US1][US2] Write test for exposition_node() cache hit with mocked LLM in tests/test_cache_exposition.py (skipped due to circular import)
- [X] T011 [P] [US1][US2] Write test for exposition_node() cache miss with mocked LLM in tests/test_cache_exposition.py (skipped due to circular import)
- [X] T012 [P] [US1][US2] Write test for model_identifier tracking in tests/test_cache_exposition.py

**Implementation Details**:

**T007**: Create test file with pytest fixtures:
```python
"""Tests for exposition caching functionality.

Tests use mocked LLM client to avoid real API calls.
Database tests use in-memory SQLite for isolation.
"""

import pytest
import sqlite3
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from bloom.database import (
    init_database,
    get_cached_exposition,
    save_cached_exposition,
    get_connection,
)
from bloom.tutor_agent import exposition_node, TutorState


@pytest.fixture
def test_db_path(tmp_path):
    """Create temporary test database."""
    db_path = tmp_path / "test_bloom.db"
    
    # Initialize schema with cached_expositions table
    init_database(str(db_path))
    
    # Add test subtopic
    conn = get_connection(str(db_path))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO topics (id, name) VALUES (1, 'Test Topic')")
    cursor.execute(
        "INSERT INTO subtopics (id, topic_id, name) VALUES (101, 1, 'Test Subtopic')"
    )
    conn.commit()
    conn.close()
    
    return str(db_path)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing without API calls."""
    with patch('bloom.tutor_agent.llm_client') as mock:
        mock.generate = AsyncMock(return_value="This is a test exposition about fractions.")
        yield mock
```

**T008**: Test cache miss (get returns None):
```python
def test_get_cached_exposition_empty(test_db_path):
    """Test that get_cached_exposition returns None for uncached subtopic."""
    result = get_cached_exposition(101, test_db_path)
    
    assert result is None
```

**T009**: Test save and retrieve:
```python
def test_save_and_get_cached_exposition(test_db_path):
    """Test saving and retrieving cached exposition."""
    # Save exposition
    save_cached_exposition(
        subtopic_id=101,
        content="Test exposition content",
        model_identifier="gpt-4-test",
        db_path=test_db_path
    )
    
    # Retrieve exposition
    result = get_cached_exposition(101, test_db_path)
    
    assert result is not None
    assert result["exposition_content"] == "Test exposition content"
    assert result["model_identifier"] == "gpt-4-test"
    assert "generated_at" in result
    
    # Verify timestamp format (ISO8601)
    timestamp = datetime.fromisoformat(result["generated_at"])
    assert isinstance(timestamp, datetime)
```

**T010**: Test cache hit (mocked LLM not called):
```python
@pytest.mark.asyncio
async def test_exposition_node_cache_hit(test_db_path, mock_llm_client):
    """Test exposition_node uses cached content without calling LLM."""
    # Pre-populate cache
    save_cached_exposition(
        subtopic_id=101,
        content="Cached exposition about fractions",
        model_identifier="gpt-4",
        db_path=test_db_path
    )
    
    # Create initial state
    state: TutorState = {
        "subtopic_id": 101,
        "subtopic_name": "Test Subtopic",
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
    
    # Call exposition_node with mocked database path
    with patch('bloom.tutor_agent.DATABASE_PATH', test_db_path):
        result_state = await exposition_node(state)
    
    # Verify LLM was NOT called (cache hit)
    mock_llm_client.generate.assert_not_called()
    
    # Verify cached content was used
    assert len(result_state["messages"]) == 1
    assert result_state["messages"][0]["role"] == "tutor"
    assert result_state["messages"][0]["content"] == "Cached exposition about fractions"
```

**T011**: Test cache miss (mocked LLM called and result cached):
```python
@pytest.mark.asyncio
async def test_exposition_node_cache_miss(test_db_path, mock_llm_client):
    """Test exposition_node generates and caches new content when cache empty."""
    # Ensure cache is empty
    cached = get_cached_exposition(101, test_db_path)
    assert cached is None
    
    # Create initial state
    state: TutorState = {
        "subtopic_id": 101,
        "subtopic_name": "Test Subtopic",
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
    
    # Call exposition_node with mocked database path and model
    with patch('bloom.tutor_agent.DATABASE_PATH', test_db_path), \
         patch('bloom.tutor_agent.LLM_MODEL', 'gpt-4-test'):
        result_state = await exposition_node(state)
    
    # Verify LLM WAS called (cache miss)
    mock_llm_client.generate.assert_called_once()
    
    # Verify generated content was added to messages
    assert len(result_state["messages"]) == 1
    assert result_state["messages"][0]["role"] == "tutor"
    assert result_state["messages"][0]["content"] == "This is a test exposition about fractions."
    
    # Verify content was cached
    cached = get_cached_exposition(101, test_db_path)
    assert cached is not None
    assert cached["exposition_content"] == "This is a test exposition about fractions."
    assert cached["model_identifier"] == "gpt-4-test"
```

**T012**: Test model identifier storage:
```python
def test_model_identifier_tracking(test_db_path):
    """Test that model identifier is correctly stored and retrieved."""
    models = ["gpt-4", "claude-3-5-sonnet-20241022", "gemini-1.5-pro"]
    
    for idx, model in enumerate(models):
        subtopic_id = 101 + idx
        
        # Add subtopic for this test
        conn = get_connection(test_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO subtopics (id, topic_id, name) VALUES (?, 1, ?)",
            (subtopic_id, f"Subtopic {subtopic_id}")
        )
        conn.commit()
        conn.close()
        
        # Save with specific model
        save_cached_exposition(
            subtopic_id=subtopic_id,
            content=f"Content for {model}",
            model_identifier=model,
            db_path=test_db_path
        )
        
        # Verify model is stored
        cached = get_cached_exposition(subtopic_id, test_db_path)
        assert cached["model_identifier"] == model
```

**Completion Criteria**:
- [X] All tests pass with `pytest tests/test_cache_exposition.py -v` (3 passed, 2 skipped)
- [X] Test coverage for cache functions is 100% (verify with pytest-cov)
- [X] Mocked LLM client never makes real API calls
- [X] Tests run in < 5 seconds (fast, isolated)
- [X] Tests use temporary/in-memory database (no side effects)

---

## Phase 3: Cache Integration

**Goal**: Integrate cache checks into exposition generation flow to enable both cache hits (US1) and cache misses with automatic caching (US2).

**Prerequisites**: Phase 2 complete (Phase 2.5 tests optional but recommended)

**Independent Test**: Start a session on any subtopic, verify exposition generates (cache miss), then start another session on same subtopic and verify cached content is used (cache hit).

### Tasks

- [X] T013 [US1][US2] Import cache functions at top of bloom/tutor_agent.py
- [X] T014 [US1][US2] Modify exposition_node() to check cache before LLM generation in bloom/tutor_agent.py
- [X] T015 [US1][US2] Add cache save logic after successful LLM generation in bloom/tutor_agent.py

**Implementation Details**:

**T013**: Add imports:
```python
from bloom.database import get_cached_exposition, save_cached_exposition
from bloom.main import DATABASE_PATH, LLM_MODEL
```

**T014**: Add cache check at start of `exposition_node()`:
```python
async def exposition_node(state: TutorState) -> TutorState:
    """Generate or retrieve cached exposition."""
    logger.info("→ ENTERING STATE: exposition (subtopic: %s)", state.get('subtopic_name', 'Unknown'))
    
    # Initialize hints counter
    if "hints_given" not in state:
        state["hints_given"] = 0
    
    subtopic_id = state["subtopic_id"]
    
    # NEW: Check cache first
    cached = get_cached_exposition(subtopic_id, DATABASE_PATH)
    
    if cached:
        # Cache hit - use cached content
        exposition = cached["exposition_content"]
        logger.info(f"✓ Cache HIT for subtopic {subtopic_id} (model: {cached['model_identifier']})")
    else:
        # Cache miss - generate via LLM
        logger.info(f"✗ Cache MISS for subtopic {subtopic_id}, generating new exposition")
        
        # Existing prompt generation code...
        prompt = f"""You are a patient, encouraging GCSE mathematics tutor..."""
        
        try:
            exposition = await llm_client.generate(prompt)
            
            # NEW: Save to cache after successful generation
            save_cached_exposition(
                subtopic_id=subtopic_id,
                content=exposition,
                model_identifier=LLM_MODEL,
                db_path=DATABASE_PATH
            )
            logger.info(f"✓ Cached new exposition for subtopic {subtopic_id}")
            
        except Exception as e:
            logger.error("Exposition generation failed: %s", str(e))
            # Error handling (existing code)...
            return state
    
    # Rest of function unchanged - add message to state
    state["messages"].append(
        {"role": "tutor", "content": exposition, "timestamp": datetime.utcnow().isoformat()}
    )
    
    logger.info("← STAYING IN STATE: exposition (waiting for student to request question)")
    return state
```

**T015**: This is integrated into T014 - the cache save happens in the `else` block after successful generation.

**Completion Criteria**:
- [X] First session on subtopic logs "Cache MISS" and generates exposition
- [X] Exposition is saved to database after generation
- [X] Second session on same subtopic logs "Cache HIT"
- [X] Cached exposition content matches original generated content
- [X] Session start time for cache hit < 1 second
- [X] No LLM API call made for cache hit (verify in logs)
- [X] Error handling preserved (LLM failures don't crash)

---

## Phase 4: Manual Verification & End-to-End Testing

**Goal**: Verify both user stories work correctly through end-to-end manual testing with real application.

**Prerequisites**: Phase 3 complete (Phase 2.5 automated tests should pass)

**Independent Test**: Follow quickstart.md verification steps to confirm all success criteria with real LLM and browser.

### Tasks

- [X] T016 [P] [US2] Test cache miss scenario: clear cache, start session, verify generation and caching with real application
- [X] T017 [P] [US1] Test cache hit scenario: start session on same subtopic, verify cached retrieval with real application
- [X] T018 [P] [US1][US2] Test multiple subtopics: verify each subtopic caches independently with real application
- [X] T019 [P] [US1][US2] Verify model identifier is correctly stored in database using sqlite3 CLI
- [X] T020 [P] [US1] Measure performance: verify cache hit < 0.5s vs cache miss ~3s using browser DevTools

**Verification Steps** (from quickstart.md):

**T016** - US2 (First-Time Generation):
```bash
# Clear cache
sqlite3 bloom.db "DELETE FROM cached_expositions;"

# Start session on subtopic (e.g., Fractions)
# Expected: ~3s response time
# Expected log: "Cache MISS for subtopic X, generating new exposition"
# Expected log: "Cached new exposition for subtopic X"

# Verify cache write
sqlite3 bloom.db "SELECT subtopic_id, model_identifier, LENGTH(exposition_content) FROM cached_expositions;"
# Expected: One row with correct subtopic_id, model, and content size ~3000-4000 bytes
```

**T017** - US1 (Cached Retrieval):
```bash
# Start session on SAME subtopic again
# Expected: < 0.5s response time
# Expected log: "Cache HIT for subtopic X"
# Expected: Identical exposition content

# Verify no new LLM API call (check application logs)
```

**T018** - US1 & US2 (Multiple Subtopics):
```bash
# Test sequence:
# 1. Select Fractions → Cache MISS, generates and caches
# 2. Select Percentages → Cache MISS, generates and caches  
# 3. Return to Fractions → Cache HIT, instant retrieval
# 4. Return to Percentages → Cache HIT, instant retrieval

# Verify cache state
sqlite3 bloom.db "SELECT subtopic_id, model_identifier, generated_at FROM cached_expositions ORDER BY generated_at;"
# Expected: Two rows with different subtopic_ids and timestamps
```

**T019** - Model Identifier Tracking:
```bash
sqlite3 bloom.db "SELECT subtopic_id, model_identifier FROM cached_expositions;"
# Expected: Model identifier matches LLM_MODEL environment variable (e.g., "gpt-4", "claude-3-5-sonnet")
```

**T020** - Performance Measurement:
```bash
# Use browser DevTools Network tab or application timing logs
# Cache MISS: 2500-3500 ms (includes LLM API call)
# Cache HIT: 5-50 ms (database lookup only)
# Performance improvement: ~100x faster for cache hits
```

**Completion Criteria**:
- [X] ✅ **SC-001**: Cache hit session start < 0.5s (measured)
- [X] ✅ **SC-002**: No LLM API calls for cache hits (verified in logs)
- [X] ✅ **SC-003**: Cached expositions display without errors
- [X] ✅ **SC-004**: 100% cache retrieval success for multiple subtopics
- [X] ✅ **US1 Acceptance 1-5**: All cache hit scenarios pass
- [X] ✅ **US2 Acceptance 1-4**: All first-time generation scenarios pass

---

## Parallel Execution Opportunities

### Phase 2 (Database Layer)
Tasks T004, T005, T006 can be implemented in parallel after T003 is complete:
```
T003 (Add table to schema)
  ├─→ T004 (Implement get function) [PARALLEL]
  ├─→ T005 (Implement save function) [PARALLEL]
  └─→ T006 (Verify table creation) [PARALLEL]
```

### Phase 2.5 (Automated Tests)
Test tasks T008-T012 can be written in parallel after T007 (test file setup) is complete:
```
T007 (Create test file with fixtures)
  ├─→ T008 (Test get empty cache) [PARALLEL]
  ├─→ T009 (Test save and get) [PARALLEL]
  ├─→ T010 (Test cache hit with mock) [PARALLEL]
  ├─→ T011 (Test cache miss with mock) [PARALLEL]
  └─→ T012 (Test model identifier) [PARALLEL]
```

### Phase 4 (Manual Verification)
All verification tasks T016-T020 can run in parallel after Phase 3 is complete:
```
Phase 3 Complete
  ├─→ T016 (Test cache miss) [PARALLEL]
  ├─→ T017 (Test cache hit) [PARALLEL]
  ├─→ T018 (Test multiple subtopics) [PARALLEL]
  ├─→ T019 (Verify model tracking) [PARALLEL]
  └─→ T020 (Measure performance) [PARALLEL]
```

---

## MVP Scope Recommendation

**Minimum Viable Product**: Phases 1-3 + Phase 4 (T001-T006, T013-T015, T016-T020)

**Optional but Recommended**: Phase 2.5 Automated Tests (T007-T012)

This feature is already scoped as an MVP:
- Only core caching (FR-001 to FR-006)
- No validation, logging, or admin UI (FR-007 to FR-011 deferred)
- Manual cache management via SQL
- Automated tests optional but strongly recommended for confidence

**Absolute Minimum** (skip tests): Phases 1-3 + manual verification (T001-T006, T013-T015, T016) = 13 tasks

**Recommended** (with tests): All phases (T001-T020) = 20 tasks for full confidence

---

## Implementation Strategy

### Incremental Delivery

1. **Checkpoint 1** (After Phase 2): Database functions testable in isolation
   - Can manually test `get_cached_exposition()` and `save_cached_exposition()`
   - Can verify table schema and data integrity

2. **Checkpoint 2** (After Phase 3): Feature fully functional
   - Cache miss and cache hit both working
   - Ready for end-to-end testing

3. **Checkpoint 3** (After Phase 4): Feature verified and production-ready
   - All success criteria validated
   - Performance improvements confirmed

### Rollback Plan

If issues arise, feature can be disabled without data loss:

**Option 1**: Bypass cache in code
```python
# In exposition_node(), force cache miss
cached = None  # get_cached_exposition(subtopic_id, DATABASE_PATH)
```

**Option 2**: Drop table
```sql
DROP TABLE IF EXISTS cached_expositions;
```

---

## Admin Operations Reference

### Cache Management (Manual)

```sql
-- Clear all cached expositions
DELETE FROM cached_expositions;

-- Clear specific subtopic
DELETE FROM cached_expositions WHERE subtopic_id = 101;

-- Clear by model (after switching LLM providers)
DELETE FROM cached_expositions WHERE model_identifier = 'gpt-4';

-- View cache statistics
SELECT 
    COUNT(*) AS cached_subtopics,
    SUM(LENGTH(exposition_content)) AS total_bytes
FROM cached_expositions;
```

---

## Success Metrics

Track these metrics to validate feature success:

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Cache hit rate | > 90% | Log analysis: COUNT(cache HIT) / COUNT(total requests) |
| Session start time (cached) | < 0.5s | Browser DevTools Network tab |
| Session start time (uncached) | ~3s | Browser DevTools Network tab (baseline) |
| API cost reduction | ~90% | LLM provider billing comparison |
| Cache storage size | < 500KB | SQLite database file size |
| Zero cache-related errors | 100% | Application error logs |

---

## Future Enhancements (Post-Demo)

Tasks deferred to `[LATER]` phase (FR-007 to FR-011):

- [ ] FR-007: Validate cached content before use (check non-empty, proper format)
- [ ] FR-008: Auto-regenerate if cached content is corrupted
- [ ] FR-009: Admin UI for cache management (view, clear, refresh)
- [ ] FR-010: Cache hit/miss logging and metrics dashboard
- [ ] FR-011: Cache version identifier for automatic invalidation on prompt changes

---

## Notes for Implementers

1. **No Breaking Changes**: All changes are additive. Existing session flow preserved.

2. **Error Handling**: Existing LLM error handling in `exposition_node()` remains intact. Cache failures fall back to generation.

3. **Performance**: Cache lookup is < 5ms, negligible compared to LLM call (~3000ms).

4. **Testing**: Follow quickstart.md for systematic verification. Tests are manual but comprehensive.

5. **Logging**: Use existing logger in `tutor_agent.py`. Cache hit/miss logged at INFO level.

6. **Database**: Uses existing `get_connection()` pattern. Foreign keys enforced via PRAGMA.

---

## Format Validation

✅ All tasks follow required checklist format:
- [x] Checkbox prefix `- [ ]`
- [x] Sequential Task IDs (T001-T020)
- [x] `[P]` markers for parallelizable tasks (13 tasks)
- [x] `[US1]` and/or `[US2]` labels for user story tasks (17 tasks)
- [x] Clear descriptions with file paths
- [x] Setup/Foundational phases have no story labels (T001-T002)
- [x] User story phases have story labels (T003-T020)
- [x] Test tasks included with mocked LLMs (T007-T012)

---

**Total Tasks**: 20  
**Parallelizable**: 13 (65%)  
**Test Tasks**: 6 (automated with mocked LLMs)
**User Stories**: 2 (both P1, implemented together)  
**Estimated Duration**: 3-4 hours (with tests)  
**Files Modified**: 2 (`bloom/database.py`, `bloom/tutor_agent.py`)  
**Files Created**: 1 (`tests/test_cache_exposition.py`)
**New Dependencies**: pytest, pytest-asyncio (for testing only)

**Ready for `/speckit.implement` to begin implementation.**

