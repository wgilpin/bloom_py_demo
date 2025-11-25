# Research: Cache Lesson Exposition

**Date**: 2025-11-25  
**Status**: Completed

## Overview

This document consolidates research findings for implementing exposition caching in the Bloom tutoring system. The goal is to reduce API costs and improve session start times by caching LLM-generated lesson expositions.

---

## 1. Cache Key Design

### Research Question
What should be the primary key for the cache? Options:
- A. `subtopic_id` only
- B. `(subtopic_id, model_identifier)` composite key
- C. `(subtopic_id, model_identifier, cache_version)` composite key

### Analysis

**Option A: subtopic_id only**
- ✓ Simplest implementation
- ✓ Single cached exposition per subtopic (consistent experience)
- ✗ Cannot cache multiple models simultaneously
- ✗ Model changes require cache clear

**Option B: (subtopic_id, model_identifier)**
- ✓ Supports multiple models simultaneously
- ✓ Model switching doesn't lose cache
- ✗ More complex queries
- ✗ Overkill for single-model demo

**Option C: (subtopic_id, model, version)**
- ✗ Overengineering for demo scope
- ✗ Version management adds complexity

### Decision

**Choose Option A with model_identifier stored separately** (not as part of key)

**Rationale**:
- Primary key: `subtopic_id` (simple lookups)
- Store `model_identifier` as data column (for auditing/manual invalidation)
- Demo typically uses single model
- Admin can manually delete by model if needed: `DELETE FROM cached_expositions WHERE model_identifier = 'gpt-4'`

**SQL Pattern**:
```sql
CREATE TABLE cached_expositions (
    subtopic_id INTEGER PRIMARY KEY,
    model_identifier TEXT NOT NULL,
    ...
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);

-- Simple lookup
SELECT exposition_content FROM cached_expositions WHERE subtopic_id = ?;

-- Model-specific invalidation (admin operation)
DELETE FROM cached_expositions WHERE model_identifier = 'gpt-4';
```

---

## 2. Concurrent Access Handling

### Research Question
What happens if two students start sessions on the same uncached subtopic simultaneously?

### Scenario Analysis

**Scenario**: Two concurrent requests hit `exposition_node()` for subtopic 101 (not yet cached)

**Possible Outcomes**:
1. **Race condition**: Both threads call LLM API
2. **Last write wins**: Second response overwrites first in cache
3. **Database locking**: Use `SELECT FOR UPDATE` or transactions

### Analysis

**Option 1: Accept race condition (no locking)**
- ✓ Simple implementation
- ✓ SQLite INSERT OR REPLACE handles conflicts automatically
- ✗ Wastes one LLM API call (rare occurrence)
- ✗ Students might see different expositions (very briefly)

**Option 2: Database-level locking**
- ✓ Prevents duplicate generation
- ✗ Requires transaction management
- ✗ Potential deadlocks
- ✗ Complexity for rare edge case

**Option 3: Application-level locking (asyncio Lock)**
- ✓ Prevents duplicate API calls
- ✗ Doesn't work across multiple processes
- ✗ Single-user demo unlikely to hit this case

### Decision

**Accept race condition with last-write-wins**

**Rationale**:
- Demo is single-user (concurrent access extremely rare)
- Cost of duplicate generation: ~1 LLM call (~$0.001) - acceptable
- SQLite `INSERT OR REPLACE` automatically handles conflicts
- No locking code needed (simpler implementation)

**Implementation**:
```python
# No locking needed
if not cached:
    exposition = await llm_client.generate(prompt)
    save_cached_exposition(...)  # Uses INSERT OR REPLACE
```

---

## 3. Cache Invalidation Strategy

### Research Question
When and how should cached expositions be invalidated?

### Invalidation Triggers

1. **Model change** (e.g., GPT-4 → Claude): Quality/style may differ
2. **Prompt change**: Different exposition structure
3. **Content errors**: Factual mistakes in cached exposition
4. **Manual refresh**: Admin wants to improve exposition

### Options Evaluated

**A. No automatic invalidation (manual only)**
- ✓ Simple (no background jobs, no TTL logic)
- ✓ Appropriate for stable demo
- ✗ Stale cache if prompts change

**B. Timestamp-based TTL (e.g., 30 days)**
- ✗ Unnecessary for demo (expositions don't expire)
- ✗ Requires periodic cleanup job

**C. Cache version identifier**
- ✓ Explicit invalidation on logic changes
- ✗ Requires version management (deferred to FR-011 `[LATER]`)

### Decision

**Manual invalidation via SQL DELETE (Option A for demo)**

**Rationale**:
- Demo expositions are stable (no frequent prompt changes)
- Model identifier enables selective deletion
- Timestamp supports future age-based policies
- Automatic expiration (FR-011) deferred to production

**Admin Operations** (documentation in quickstart.md):
```sql
-- Clear all cache
DELETE FROM cached_expositions;

-- Clear specific subtopic (e.g., found error in content)
DELETE FROM cached_expositions WHERE subtopic_id = 101;

-- Clear by model (after switching providers)
DELETE FROM cached_expositions WHERE model_identifier LIKE 'gpt-4%';

-- Clear old entries (example for future use)
DELETE FROM cached_expositions WHERE generated_at < '2025-01-01';
```

---

## 4. Error Handling Strategy

### Research Question
How should we handle potential cache corruption or invalid data?

### Error Scenarios

1. **Empty content**: `exposition_content IS NULL OR = ''`
2. **Database corruption**: SQLite file damaged
3. **Schema mismatch**: Code expects field that doesn't exist

### Options Evaluated

**A. Validate before use (FR-007)**
- ✓ Defensive programming
- ✗ Adds code complexity
- ✗ Rare edge case in SQLite

**B. Trust the cache (demo approach)**
- ✓ Simple implementation
- ✓ SQLite corruption extremely rare
- ✗ No automatic recovery if issue occurs

**C. Validate and auto-regenerate (FR-007 + FR-008)**
- ✗ Production-grade, overkill for demo

### Decision

**Trust the cache (Option B for demo)**

**Rationale**:
- SQLite database corruption is extremely rare
- INSERT logic ensures content is non-null (Python string always valid)
- Easy manual recovery: `DELETE FROM cached_expositions WHERE subtopic_id = ?`
- Validation (FR-007) and auto-regeneration (FR-008) deferred to `[LATER]`

**Error Handling** (existing pattern):
```python
cached = get_cached_exposition(subtopic_id)
if cached:
    return cached["exposition_content"]  # Trust it's valid
else:
    # Generate new (handles all errors in existing LLM wrapper)
```

---

## 5. Model Identifier Format

### Research Question
What format should `model_identifier` use?

### Options

1. **Short name**: `"gpt-4"`, `"claude-3.5"`, `"gemini"`
2. **Full version**: `"gpt-4-turbo-2024-04-09"`, `"claude-3-5-sonnet-20241022"`
3. **Provider:model**: `"openai:gpt-4"`, `"anthropic:claude-3.5"`

### Decision

**Use LLM_MODEL from config (full version when available)**

**Rationale**:
- Aligns with existing `LLM_MODEL` config variable
- Full version (if available) enables precise tracking
- Provider usually evident from model name (e.g., "gpt" = OpenAI)
- Consistent with how models are already specified in `.env`

**Example Values**:
```python
LLM_MODEL = "gpt-4"                           # → store "gpt-4"
LLM_MODEL = "claude-3-5-sonnet-20241022"      # → store "claude-3-5-sonnet-20241022"
LLM_MODEL = "gemini-1.5-pro"                  # → store "gemini-1.5-pro"
```

---

## 6. Cache Performance Characteristics

### Research Question
What are the expected performance impacts?

### Measurements

**Cache Miss (first time generation)**:
- LLM API call: ~2-3 seconds
- Database INSERT: ~1-5 ms (negligible)
- **Total**: ~3 seconds (unchanged from current)

**Cache Hit (subsequent requests)**:
- Database SELECT: ~1-5 ms
- No LLM API call
- **Total**: < 10 ms (from ~3000 ms)

**Performance Gain**: ~300x faster for cached expositions

### Cost Analysis

**Current (no cache)**:
- 100 students × 5 subtopics each = 500 exposition generations
- 500 × ~1000 tokens × $0.001/1K tokens = **$0.50**

**With cache (90% hit rate)**:
- First 50 unique subtopics: 50 generations = $0.05
- Next 450 requests: cached (free)
- **Total: $0.05 (90% reduction)**

### Scale Estimates

| Metric | Value |
|--------|-------|
| Max subtopics (GCSE math) | ~100 |
| Avg exposition size | 800 tokens (~3KB) |
| Max cache size (100 subtopics) | ~300KB |
| SQLite overhead | ~50 bytes/row |
| Total database growth | < 500KB |

**Conclusion**: Performance improvement is significant (300x faster), cost reduction is substantial (90%), storage overhead is negligible (< 500KB).

---

## 7. Testing Strategy

### Verification Approach

**Manual Testing** (per constitution - no test framework required):

1. **Cache Miss Test**:
   ```bash
   # Clear cache
   sqlite3 bloom.db "DELETE FROM cached_expositions;"
   
   # Start session on subtopic 101
   # Expected: ~3s response, logs show "Cache MISS"
   ```

2. **Cache Hit Test**:
   ```bash
   # Start another session on subtopic 101 (without clearing)
   # Expected: < 0.5s response, logs show "Cache HIT"
   ```

3. **Content Consistency Test**:
   ```bash
   # Record exposition from cache hit
   # Compare with database: SELECT exposition_content FROM cached_expositions WHERE subtopic_id = 101
   # Expected: Exact match
   ```

4. **Model Identifier Test**:
   ```bash
   # Check database after generation
   sqlite3 bloom.db "SELECT model_identifier FROM cached_expositions WHERE subtopic_id = 101;"
   # Expected: Shows current LLM_MODEL value
   ```

**Automated Tests** (optional, if implemented):
```python
def test_exposition_cache_hit():
    """Verify cache returns stored exposition."""
    # Seed cache with known exposition
    save_cached_exposition(101, "Test exposition", "gpt-4", "bloom_test.db")
    
    # Retrieve
    cached = get_cached_exposition(101, "bloom_test.db")
    
    assert cached is not None
    assert cached["exposition_content"] == "Test exposition"
    assert cached["model_identifier"] == "gpt-4"

def test_exposition_cache_miss():
    """Verify cache miss returns None."""
    # Clear cache
    conn = get_connection("bloom_test.db")
    conn.execute("DELETE FROM cached_expositions WHERE subtopic_id = 999")
    conn.commit()
    
    # Try to retrieve non-existent
    cached = get_cached_exposition(999, "bloom_test.db")
    
    assert cached is None
```

---

## Summary

| Decision Point | Choice | Rationale |
|----------------|--------|-----------|
| Cache key | `subtopic_id` (PK), store model separately | Simple lookups, model stored for auditing |
| Concurrency | Accept race, last-write-wins | Rare in single-user demo, SQLite handles conflicts |
| Invalidation | Manual SQL DELETE only | Stable demo, no automatic expiration needed |
| Validation | Trust cache (skip FR-007) | SQLite corruption rare, easy manual recovery |
| Model format | Use `LLM_MODEL` from config | Consistent with existing configuration |
| Testing | Manual verification + optional pytest | Per constitution, tests optional for demo |

**Key Takeaway**: All research decisions prioritize simplicity and demo scope, deferring production-grade features (validation, logging, admin UI) to `[LATER]` phase.

