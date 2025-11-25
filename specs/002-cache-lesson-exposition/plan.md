# Implementation Plan: Cache Lesson Exposition

**Branch**: `002-cache-lesson-exposition` | **Date**: 2025-11-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-cache-lesson-exposition/spec.md`

## Summary

This feature adds caching for lesson expositions to reduce LLM API costs and improve session start times. Currently, every session generates a new exposition via LLM, even for the same subtopic. This implementation adds a database cache layer that stores expositions by subtopic ID, checks the cache before calling the LLM, and serves cached content when available.

**Technical Approach**: Add a new `cached_expositions` table to the existing SQLite database. Wrap the `exposition_node()` function in `bloom/tutor_agent.py` with cache-check logic. Store exposition content, generation timestamp, and model identifier for each subtopic. No UI changes required—caching is transparent to users.

**Scope**: Demo phase implements only FR-001 through FR-006 (core caching). Requirements FR-007 through FR-011 (validation, logging, admin UI) are marked `[LATER]` for post-demo enhancement.

## Technical Context

**Language/Version**: Python 3.13+ (existing project)
**Primary Dependencies**: 
- Existing: FastAPI, SQLite (sqlite3), LangGraph
- New: None (uses existing dependencies)

**Storage**: SQLite database (`bloom.db`) - add one new table
**Testing**: pytest (optional, per constitution)
**Target Platform**: Web application (existing)
**Project Type**: Enhancement to existing web application
**Performance Goals**: 
- Cache hit: session start < 0.5s (down from ~3s) (SC-001)
- Cache miss (first time): session start ~3s (unchanged) (SC-001)
- API call reduction: ~90% for typical usage (SC-002)

**Constraints**: 
- Must not break existing session flow
- Cache shared across all students (single-user demo)
- Manual cache invalidation only (no auto-expiration for demo)

**Scale/Scope**: 
- ~50-100 subtopics maximum (GCSE math syllabus)
- Each cached exposition: ~2-4KB text + ~50 bytes metadata
- Total cache size: < 500KB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Simplicity First ✓
- **Architecture**: Single table addition to existing SQLite database
- **No new dependencies**: Uses existing sqlite3 connection handling
- **Minimal abstraction**: Simple cache lookup function, no caching library needed

### II. Minimal Boilerplate ✓
- **Direct SQL queries**: INSERT, SELECT with subtopic_id lookup
- **No ORM**: Continues existing pattern of raw SQL via sqlite3
- **No configuration**: Cache behavior always-on (transparent optimization)

### III. Rapid Iteration Over Perfection ✓
- **Demo scope**: Skip validation, logging, admin UI for initial implementation
- **Manual cache clear**: SQL DELETE if needed (no UI required)
- **Tests optional**: Cache logic is straightforward (check cache → use or generate)

### IV. Focused Scope ✓
- **Single purpose**: Cache expositions only (not questions, feedback, or other LLM outputs)
- **No premature features**: Deferring FR-007 through FR-011 (`[LATER]`)
- **Existing flow intact**: Cache is a performance optimization, not a feature change

### V. Pleasing Simplicity (UI/UX) ✓
- **Transparent to users**: No UI changes, expositions appear faster (when cached)
- **No degradation**: First-time generation still works exactly as before
- **Consistent quality**: Cached expositions identical to fresh generations

### Technology Constraints Compliance ✓
- ✓ Uses existing Python 3.13+
- ✓ Uses existing SQLite database
- ✓ No new libraries or dependencies
- ✓ Follows existing code patterns in `bloom/tutor_agent.py` and `bloom/database.py`

### Violations Requiring Justification

None. This feature adds minimal complexity (one table, one cache-check function) and reduces operational costs (fewer LLM calls).

**Gate Status**: ✅ **PASS** - Pure optimization with no new complexity

## Project Structure

### Documentation (this feature)

```text
specs/002-cache-lesson-exposition/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Tech decisions (cache key design, concurrency)
├── data-model.md        # Phase 1: cached_expositions table schema
├── quickstart.md        # Phase 1: Testing the cache (how to verify it works)
└── checklists/          # Requirements checklist (already exists)
    └── requirements.md
```

### Modified Files (repository root)

```text
bloom/
├── database.py          # ADD: init_cache_table(), get_cached_exposition(), save_cached_exposition()
├── tutor_agent.py       # MODIFY: exposition_node() - wrap with cache logic
└── routes/
    └── student.py       # MODIFY: start_session() - pass model identifier to cache
```

No new files needed. No UI changes needed. No new routes needed.

## Complexity Tracking

**Added Complexity**:
- 1 new database table (`cached_expositions`)
- 3 new database functions (init, get, save cache)
- ~15 lines of cache-check logic in `exposition_node()`

**Reduced Complexity**:
- Eliminates repeated LLM calls for same content (90% reduction)
- Faster debugging (cached expositions always return same result)

**Net Complexity**: Minimal increase, significant operational simplification.

---

## Phase 0: Research

Research tasks completed during this phase:

### 1. Cache Key Design
**Question**: Should we cache by (subtopic_id) or (subtopic_id + model)?

**Decision**: Use `subtopic_id` as primary key, store `model_identifier` separately

**Rationale**:
- Subtopic content should be model-agnostic (same teaching, different phrasing)
- Model identifier stored for auditing and manual invalidation
- Simplifies lookups (no composite key needed)
- For demo, single model is typical; storing identifier future-proofs

**Alternatives considered**:
- Composite key (subtopic_id, model_identifier): Overengineering for demo, would allow caching multiple models per subtopic (not needed)
- Subtopic_id only (no model tracking): Rejected per user requirement

### 2. Concurrent Access Handling
**Question**: What if two students start same uncached subtopic simultaneously?

**Decision**: Accept potential duplicate generation, last write wins

**Rationale**:
- SQLite INSERT OR REPLACE handles last-write-wins automatically
- Extremely rare in single-user demo scenario
- Cost of duplicate generation (one extra LLM call) is acceptable
- Alternative (database locking) adds complexity for negligible benefit

**Alternatives considered**:
- SELECT FOR UPDATE locking: Requires transaction management, overkill for demo
- Unique constraint with error handling: Same outcome as INSERT OR REPLACE, more code

### 3. Cache Invalidation Strategy
**Question**: When/how to clear old cached expositions?

**Decision**: Manual invalidation via SQL DELETE (no automatic expiration for demo)

**Rationale**:
- Exposition content stable over demo lifespan
- Model identifier enables selective deletion by model
- Timestamp enables age-based deletion if needed later
- Automatic expiration (FR-011 `[LATER]`) deferred to production

**Implementation** (for admin reference):
```sql
-- Clear all cache
DELETE FROM cached_expositions;

-- Clear specific subtopic
DELETE FROM cached_expositions WHERE subtopic_id = ?;

-- Clear by model (e.g., after switching from GPT-4 to Claude)
DELETE FROM cached_expositions WHERE model_identifier = 'gpt-4';
```

### 4. Error Handling Philosophy
**Question**: What if cached content is empty/corrupted?

**Decision**: Trust the cache for demo; skip validation (FR-007 deferred)

**Rationale**:
- Database corruption extremely rare in SQLite
- Validation adds code complexity
- Easy recovery: clear cache entry, regenerate
- Production can add validation later (FR-007, FR-008)

---

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for full schema.

**Summary**: One new table `cached_expositions` with columns:
- `subtopic_id` (PK, FK to subtopics)
- `exposition_content` (TEXT, the cached exposition)
- `generated_at` (TEXT, ISO8601 timestamp)
- `model_identifier` (TEXT, e.g., "gpt-4", "claude-3-5-sonnet-20241022")

No indexes needed (lookups always by primary key).

### API Contracts

**No new API endpoints needed.** Caching is internal optimization.

Existing flow unchanged:
1. Student clicks subtopic → POST `/session/start`
2. `start_session()` calls `exposition_node()`
3. **NEW**: `exposition_node()` checks cache before LLM call
4. Response rendered in chat interface (existing template)

### Implementation Pattern

```python
async def exposition_node(state: TutorState) -> TutorState:
    """Generate or retrieve cached exposition."""
    subtopic_id = state["subtopic_id"]
    
    # NEW: Check cache first
    cached = get_cached_exposition(subtopic_id, DATABASE_PATH)
    
    if cached:
        # Cache hit - use cached content
        exposition = cached["exposition_content"]
        logger.info(f"Cache HIT for subtopic {subtopic_id}")
    else:
        # Cache miss - generate via LLM
        prompt = f"""..."""  # existing prompt
        exposition = await llm_client.generate(prompt)
        
        # Save to cache
        save_cached_exposition(
            subtopic_id=subtopic_id,
            content=exposition,
            model_identifier=LLM_MODEL,  # from config
            db_path=DATABASE_PATH
        )
        logger.info(f"Cache MISS for subtopic {subtopic_id}, generated and cached")
    
    # Rest of function unchanged
    state["messages"].append(...)
    return state
```

### Quickstart

See [quickstart.md](./quickstart.md) for testing instructions.

**Verification Steps**:
1. Clear cache: `DELETE FROM cached_expositions;`
2. Start session on subtopic → check logs for "Cache MISS"
3. Exit and restart session on same subtopic → check logs for "Cache HIT"
4. Verify start time < 0.5s (cached) vs ~3s (uncached)

---

## Phase 1 Design Artifacts: Constitution Re-Check

**Post-Design Evaluation** (after data model and implementation pattern defined):

### Architecture Review ✓

**Data Model** ([data-model.md](./data-model.md)):
- ✓ Single table, normalized schema
- ✓ No ORM (raw SQL via sqlite3, existing pattern)
- ✓ No indexes needed (PK lookups only)
- ✓ Foreign key to subtopics with CASCADE

**Implementation Pattern**:
- ✓ 3 simple functions (init table, get cache, save cache)
- ✓ ~15 lines of cache-check logic in existing function
- ✓ No new dependencies or libraries
- ✓ Preserves existing error handling

### Principles Compliance ✓

**I. Simplicity First**:
- ✓ One table, three functions (minimal footprint)
- ✓ No caching library (direct SQL)
- ✓ No configuration (always-on optimization)

**II. Minimal Boilerplate**:
- ✓ Direct INSERT/SELECT queries
- ✓ No abstraction layers
- ✓ Reuses existing database connection pattern

**III. Rapid Iteration Over Perfection**:
- ✓ Skipping validation/logging/admin UI for demo
- ✓ Manual cache management (SQL DELETE)
- ✓ Tests optional (straightforward logic)

**IV. Focused Scope**:
- ✓ Caches expositions only (not questions/feedback)
- ✓ Demo scope (FR-001 to FR-006)
- ✓ Deferred FR-007 to FR-011 (`[LATER]`)

**V. Pleasing Simplicity (UI/UX)**:
- ✓ Transparent to users (no UI changes)
- ✓ Faster session starts (when cached)
- ✓ No degradation (fallback to LLM works as before)

### Constitution Violations: None ✅

All design decisions align with constitution principles. Implementation is minimal, focused, and uses existing patterns.

---

## Final Gate Status: ✅ APPROVED FOR IMPLEMENTATION

**Summary**:
- ✓ Single table addition to existing database
- ✓ Three new database functions
- ✓ ~15 lines of cache logic in existing exposition node
- ✓ No UI changes, no new dependencies
- ✓ 90% API cost reduction for typical usage
- ✓ Sub-0.5s session starts for cached expositions

Ready to proceed to `/speckit.tasks` for task breakdown.

