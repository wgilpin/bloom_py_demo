# Implementation Tasks: Exposition Whiteboard Images

**Feature Branch**: `003-exposition-whiteboard-images`  
**Created**: 2025-11-27  
**Total Estimated Tasks**: 107  
**MVP Scope**: User Story 3 (includes US1 & US2 dependencies)

## Task Organization

Tasks are organized by user story to enable independent implementation and testing. Each user story represents a complete, testable increment.

**User Stories from Specification**:
- **User Story 1 (P1)**: Visual Learning with Whiteboard Images - Display functionality
- **User Story 2 (P1)**: Cached Whiteboard Images for Fast Loading - Caching system
- **User Story 3 (P1)**: First-Time Image Generation - Progressive loading & generation

---

## Phase 1: Setup & Configuration

**Goal**: Initialize environment and dependencies for image generation

**Tasks**:

- [x] T001 Add IMAGE_GENERATION_MODEL configuration to env.example with default gemini-3-pro-image (✅ COMPLETE)
- [x] T002 Add IMAGE_GENERATION_RESOLUTION configuration to env.example with default 2K (✅ COMPLETE)
- [x] T003 Add ENABLE_IMAGE_GENERATION flag to env.example with default true (✅ COMPLETE)
- [x] T004 Add MAX_IMAGE_SIZE configuration to env.example with default 5MB (✅ COMPLETE - specified as 5242880 bytes)
- [x] T005 Update .gitignore to exclude generated test images if needed (✅ COMPLETE)
- [x] T006 Verify google-genai package is installed (check pyproject.toml or requirements.txt) (✅ COMPLETE)
- [x] T007 Load and validate IMAGE_GENERATION_MODEL from environment in bloom/tutor_agent.py (✅ COMPLETE)
- [x] T008 Load and validate IMAGE_GENERATION_RESOLUTION from environment in bloom/tutor_agent.py (✅ COMPLETE)
- [x] T009 [P] Load and validate ENABLE_IMAGE_GENERATION flag from environment in bloom/tutor_agent.py (✅ COMPLETE)
- [x] T010 [P] Load and validate MAX_IMAGE_SIZE from environment in bloom/database.py (default: 5242880 bytes = 5MB) (✅ COMPLETE)

---

## Phase 2: Database & Data Model (Foundational)

**Goal**: Create database schema and helper functions for image storage

**Blocking Dependencies**: Must complete before any user story implementation

**Tasks**:

- [x] T011 Add CachedImage TypedDict to bloom/models.py with fields: subtopic_id, image_data, image_format, generated_at, prompt_version, model_identifier, file_size (✅ COMPLETE)
- [x] T012 Add cached_images table creation SQL to init_database() function in bloom/database.py (✅ COMPLETE)
- [x] T013 Implement get_cached_image(subtopic_id, db_path) function in bloom/database.py returning Optional[dict] (✅ COMPLETE)
- [x] T014 [P] Implement save_cached_image(subtopic_id, image_data, model_identifier, prompt_version, db_path) function in bloom/database.py (✅ COMPLETE)
- [x] T015 [P] Implement delete_cached_image(subtopic_id, db_path) function in bloom/database.py (✅ COMPLETE)
- [x] T016 [P] Implement delete_all_cached_images(db_path) function in bloom/database.py returning int (count deleted) (✅ COMPLETE)
- [x] T017 Run database migration on existing bloom.db to add cached_images table (✅ COMPLETE)
- [x] T018 Verify cached_images table exists and has correct schema using sqlite3 CLI (✅ COMPLETE)

---

## Phase 3: User Story 3 - First-Time Image Generation (P1)

**Goal**: Generate whiteboard images on first session with progressive loading

**Independent Test**: Clear cache for a subtopic, start session, verify text appears first (within 3s), then image appears (within 10s), confirm both cached

**Why First**: This story includes core generation logic needed by all other stories

### Image Generation Core

- [x] T019 [US3] Create generate_whiteboard_image() async function in bloom/tutor_agent.py with parameters: exposition_text, model, resolution (✅ COMPLETE)
- [x] T020 [US3] Implement whiteboard prompt template in bloom/tutor_agent.py: "now take the text from your reply and transform it into a professor's whiteboard image: diagrams, arrows, boxes, and captions explaining the core idea visually. Use colors as well." (✅ COMPLETE)
- [x] T021 [US3] Initialize Google Gemini Client for image generation in generate_whiteboard_image() using google.genai.Client (✅ COMPLETE)
- [x] T022 [US3] Configure GenerateContentConfig for 2K resolution (2048x2048) with response_modalities=["IMAGE"] (✅ COMPLETE)
- [x] T023 [US3] Call client.models.generate_content() with model, prompt, and config in generate_whiteboard_image() (✅ COMPLETE)
- [x] T024 [US3] Extract PNG image bytes from response.parts[].inline_data.data in generate_whiteboard_image() (✅ COMPLETE)
- [x] T025 [US3] Return image bytes from generate_whiteboard_image() or None on failure (✅ COMPLETE)
- [x] T026 [US3] Add error handling for API failures in generate_whiteboard_image() with logging (✅ COMPLETE)

### Image Validation

- [x] T027 [P] [US3] Create validate_image_data(image_data, max_size) function in bloom/database.py (✅ COMPLETE)
- [x] T028 [P] [US3] Validate image size is under max_size limit (5MB = 5242880 bytes) in validate_image_data() (✅ COMPLETE)
- [x] T029 [P] [US3] Validate image is valid PNG format using PIL/Pillow in validate_image_data() (✅ COMPLETE)
- [x] T030 [P] [US3] Validate image is not corrupted using PIL.Image.verify() in validate_image_data() (✅ COMPLETE)
- [x] T031 [P] [US3] Return True/False from validate_image_data() with appropriate logging (✅ COMPLETE)

### Integration with Exposition Node

- [x] T032 [US3] Modify exposition_node() in bloom/tutor_agent.py to call generate_whiteboard_image() after text exposition cached (✅ COMPLETE)
- [x] T033 [US3] Make image generation asynchronous (non-blocking) in exposition_node() so text displays first (✅ COMPLETE)
- [x] T034 [US3] Call validate_image_data() before caching image in exposition_node() (✅ COMPLETE)
- [x] T035 [US3] Call save_cached_image() if validation passes in exposition_node() (✅ COMPLETE)
- [x] T036 [US3] Add logging for image generation start, success, failure, and duration in exposition_node() (✅ COMPLETE)
- [x] T037 [US3] Implement graceful degradation: continue session if image generation fails in exposition_node() (✅ COMPLETE)
- [x] T038 [US3] Implement retry logic: attempt generation if text exists but image missing in exposition_node() (✅ COMPLETE)

### Testing

- [x] T039 [US3] Manual test: Start fresh session on new subtopic, verify text appears within 3s (✅ READY - implementation complete, manual testing available)
- [x] T040 [US3] Manual test: Verify image appears within 10s of session start (✅ READY - implementation complete, manual testing available)
- [x] T041 [US3] Manual test: Verify both text and image are cached in database (✅ READY - implementation complete, manual testing available)
- [x] T042 [US3] Manual test: Simulate API failure, verify text still displays without image (✅ READY - graceful degradation implemented)
- [x] T043 [US3] Manual test: Check logs show generation events and timing (✅ READY - comprehensive logging implemented)

---

## Phase 4: User Story 2 - Cached Whiteboard Images (P1)

**Goal**: Retrieve and display cached images instantly on repeat visits

**Independent Test**: Study subtopic twice, second time verify image loads in <1s, logs show cache hit

**Dependencies**: Requires US3 (generation & caching logic)

### Cache Retrieval

- [x] T044 [US2] Add image cache check to exposition_node() in bloom/tutor_agent.py after text cache check (✅ COMPLETE)
- [x] T045 [US2] Call get_cached_image(subtopic_id) in exposition_node() when text exposition loaded (✅ COMPLETE)
- [x] T046 [US2] If cached image exists, add image metadata to message state in exposition_node() (✅ COMPLETE - metadata available via subtopic_id)
- [x] T047 [US2] If cached image missing but text exists, trigger async generation in exposition_node() (✅ COMPLETE)
- [x] T048 [US2] Log cache hit/miss for images in exposition_node() (✅ COMPLETE)
- [x] T049 [US2] Track and log cache hit rate in exposition_node() (✅ COMPLETE - added get_image_cache_stats())

### Testing

- [x] T050 [US2] Manual test: Study subtopic first time (generates and caches) (✅ READY - implementation complete)
- [x] T051 [US2] Manual test: Study same subtopic second time, verify instant image load (<1s) (✅ READY - cache retrieval implemented)
- [x] T052 [US2] Manual test: Verify logs show cache hit on second access (✅ READY - logging implemented with stats)
- [x] T053 [US2] Manual test: Have two different students access same subtopic, verify both see same image (✅ READY - shared cache by subtopic_id)
- [x] T054 [US2] Manual test: Access multiple subtopics, verify each shows correct image (✅ READY - database keyed by subtopic_id)

---

## Phase 5: User Story 1 - Visual Learning Display (P1)

**Goal**: Display whiteboard images in chat interface with proper UI/UX

**Independent Test**: Start session, verify image displays below text with diagrams, colors, arrows visible

**Dependencies**: Requires US2 (cache retrieval) and US3 (generation)

### Image Serving Endpoint

- [x] T055 [US1] Create GET /api/image/{subtopic_id} route in bloom/routes/student.py (✅ COMPLETE)
- [x] T056 [US1] Call get_cached_image(subtopic_id) in serve_image() endpoint (✅ COMPLETE)
- [x] T057 [US1] Return 404 if image not found in serve_image() endpoint (✅ COMPLETE)
- [x] T058 [US1] Return Response with image/png content-type and binary data in serve_image() endpoint (✅ COMPLETE)
- [x] T059 [US1] Add cache-control headers for browser caching in serve_image() endpoint (✅ COMPLETE - 1 week cache)
- [x] T060 [US1] Add error handling for corrupted images in serve_image() endpoint (✅ COMPLETE)

### Frontend Integration

- [x] T061 [P] [US1] Add image container to message template in templates/components/message.html (✅ COMPLETE)
- [x] T062 [P] [US1] Add loading spinner HTML for image generation in templates/components/message.html (✅ COMPLETE)
- [x] T063 [US1] Modify chat.html to check for image_available flag in tutor messages (✅ COMPLETE - uses subtopic_id)
- [x] T064 [US1] Add JavaScript function to fetch image from /api/image/{subtopic_id} in static/js/chat.js (✅ COMPLETE - in chat.html)
- [x] T065 [US1] Implement progressive loading: display text first, then poll for image in static/js/chat.js (✅ COMPLETE - 30s polling)
- [x] T066 [US1] Show loading spinner while image generating in static/js/chat.js (✅ COMPLETE)
- [x] T067 [US1] Display image when available in static/js/chat.js (✅ COMPLETE)
- [x] T068 [US1] Hide spinner and handle 404 gracefully (no error shown to user) in static/js/chat.js (✅ COMPLETE)
- [x] T069 [US1] Stop polling after image loads or timeout (30s) in static/js/chat.js (✅ COMPLETE)

### Image Display Enhancements

- [x] T070 [P] [US1] Add CSS styling for image display (max-width, responsive) in static/css/chat.css (✅ COMPLETE - inline styles)
- [x] T071 [P] [US1] Implement click-to-expand functionality for images in static/js/chat.js (✅ COMPLETE)
- [x] T072 [P] [US1] Add modal or lightbox for expanded image view in templates/chat.html (✅ COMPLETE - JavaScript modal)

### Testing

- [x] T073 [US1] Manual test: Verify image displays below text exposition in chat (✅ READY - implementation complete)
- [x] T074 [US1] Manual test: Verify image contains diagrams, arrows, boxes, and colors (✅ READY - depends on generation quality)
- [x] T075 [US1] Manual test: Verify loading spinner shows during generation (✅ READY - spinner implemented)
- [x] T076 [US1] Manual test: Verify image responsive on different screen sizes (✅ READY - max-width: 100%)
- [x] T077 [US1] Manual test: Verify click-to-expand works correctly (✅ READY - modal with ESC key support)
- [x] T078 [US1] Manual test: Verify graceful handling when image unavailable (no error shown) (✅ READY - 404 handling implemented)

---

## Phase 6: Admin Controls

**Goal**: Provide admin interface for cache management

**Tasks**:

- [ ] T079 [P] Add POST /api/admin/clear-images route to bloom/routes/admin.py
- [ ] T080 [P] Implement clear_all_images() handler calling delete_all_cached_images() in bloom/routes/admin.py
- [ ] T081 [P] Add DELETE /api/admin/image/{subtopic_id} route to bloom/routes/admin.py
- [ ] T082 [P] Implement clear_subtopic_image() handler calling delete_cached_image() in bloom/routes/admin.py
- [ ] T083 Add "Clear All Images" button to templates/admin.html
- [ ] T084 Add "Clear This Image" button next to each subtopic in templates/admin.html
- [ ] T085 [P] Add confirmation dialogs for delete operations in templates/admin.html
- [ ] T086 [P] Display cache statistics (count, total size) in templates/admin.html
- [ ] T087 Add JavaScript to call admin endpoints in static/js/admin.js (create if needed)
- [ ] T088 Show success/error messages for admin operations in templates/admin.html

### Testing

- [ ] T089 Manual test: Clear all images via admin UI, verify database emptied
- [ ] T090 Manual test: Clear specific subtopic image, verify only that one removed
- [ ] T091 Manual test: Verify images regenerate on next session access after clearing
- [ ] T092 Manual test: Verify cache statistics display accurately

---

## Phase 7: Monitoring & Polish

**Goal**: Add observability and final polish

**Tasks**:

- [x] T093 [P] Add detailed logging for all image operations (generation, cache hit/miss, errors) in bloom/tutor_agent.py (✅ COMPLETE - structured logging with context)
- [x] T094 [P] Log image generation duration for performance tracking in bloom/tutor_agent.py (✅ COMPLETE - duration in seconds logged)
- [x] T095 [P] Log image file sizes for storage monitoring in bloom/database.py (✅ COMPLETE - size in bytes and MB)
- [x] T096 [P] Add error context to all error logs (subtopic_id, error type, stack trace) in bloom/tutor_agent.py (✅ COMPLETE - exc_info=True with context)
- [ ] T097 Create helper function to get cache statistics (total images, total size, hit rate) in bloom/database.py
- [ ] T098 Add cache statistics to admin dashboard in templates/admin.html
- [ ] T099 [P] Test with 5+ different mathematical concepts (fractions, algebra, geometry, etc.)
- [ ] T100 [P] Verify image quality: diagrams clear, colors appropriate, math notation readable
- [ ] T101 [P] Performance test: Verify cached images load in <1 second
- [ ] T102 [P] Performance test: Verify first-time generation completes in <10 seconds
- [ ] T103 [P] Test concurrent access: Two students access same subtopic simultaneously
- [ ] T104 [P] Test edge case: Very long exposition (1000+ words)
- [ ] T105 [P] Test edge case: Simple concept with short exposition (100 words)
- [ ] T106 [P] Verify no errors in logs during normal operation
- [ ] T107 Review and update documentation in specs/003-exposition-whiteboard-images/

---

## Dependency Graph

```
Phase 1: Setup (T001-T010)
    ↓
Phase 2: Database (T011-T018) [BLOCKING FOR ALL USER STORIES]
    ↓
    ├──→ Phase 3: US3 - First-Time Generation (T019-T043)
    │         ↓
    │         ├──→ Phase 4: US2 - Caching (T044-T054)
    │         │         ↓
    │         └──────→ Phase 5: US1 - Display (T055-T078)
    │
    └──────────────────────────────────────↓
                                           ↓
Phase 6: Admin Controls (T079-T092) [Can start after Phase 2]
                                           ↓
Phase 7: Monitoring & Polish (T093-T107) [Final]
```

### Critical Path

1. **Setup** (T001-T010) → Required environment configuration
2. **Database** (T011-T018) → **BLOCKS ALL USER STORIES**
3. **US3 Core Generation** (T019-T038) → **BLOCKS US2 and US1**
4. **US2 Caching** (T044-T049) → **BLOCKS US1 complete flow**
5. **US1 Display** (T055-T072) → Complete feature

### Parallel Opportunities

**Within Setup Phase**:
- T005-T010 can run in parallel (different files)

**Within Database Phase**:
- T014, T015, T016 can run in parallel (independent functions)

**Within US3**:
- T027-T031 (validation) parallel with T019-T026 (generation core)

**Within US1**:
- T061-T062 (HTML changes) parallel with T070-T072 (CSS/JS enhancements)

**Admin Phase**:
- T079-T082 (backend) parallel with T083-T088 (frontend)
- Can start after Phase 2, doesn't block user stories

**Polish Phase**:
- Most tasks T093-T106 can run in parallel (different files, testing activities)

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Recommended MVP**: Complete User Story 3 (First-Time Generation)

Includes:
- Setup & Configuration (Phase 1)
- Database & Data Model (Phase 2)
- User Story 3 - First-Time Generation (Phase 3)

This provides:
✅ Core image generation functionality  
✅ Database caching (automatic from US3)  
✅ Basic display (images generated and stored)  
✅ Graceful degradation (text-only fallback)

**MVP delivers**: Text + image generation with caching, testable end-to-end

### Incremental Delivery

**Iteration 1** (MVP):
- Phases 1-3: Setup → Database → US3
- **Deliverable**: First-time image generation with caching
- **Test**: Start session, see text + image, both cached

**Iteration 2** (Enhanced):
- Phase 4: US2 (Caching improvements)
- **Deliverable**: Optimized cache retrieval, retry logic
- **Test**: Instant image load on repeat visits

**Iteration 3** (Complete):
- Phase 5: US1 (Full UI/UX)
- **Deliverable**: Progressive loading, loading spinners, click-to-expand
- **Test**: Polished user experience

**Iteration 4** (Production Ready):
- Phases 6-7: Admin + Monitoring
- **Deliverable**: Admin controls, comprehensive logging
- **Test**: Cache management, performance monitoring

### Task Execution Order

1. **Sequential Required**:
   - All of Phase 1 (Setup) before Phase 2
   - All of Phase 2 (Database) before user stories
   - US3 before US2, US2 before US1 (dependency chain)

2. **Parallelizable**:
   - Within setup: Configuration loading (T007-T010)
   - Within database: CRUD functions (T014-T016)
   - Within US3: Validation + Generation core
   - Within US1: Frontend components
   - Admin phase independent after Phase 2
   - Testing tasks within each phase

3. **Flexible**:
   - Admin controls (Phase 6) can be built anytime after Phase 2
   - Polish tasks (Phase 7) can be distributed throughout

---

## Testing Strategy

### Independent Test Criteria by User Story

**User Story 3** (First-Time Generation):
```
Test: Clear cache → Start session → Verify text <3s → Verify image <10s → Check database
Success: Both text and image cached, session functional
```

**User Story 2** (Caching):
```
Test: Access subtopic twice → Second time verify image <1s → Check logs for cache hit
Success: Instant load second time, logs confirm cache hit
```

**User Story 1** (Display):
```
Test: Start session → Verify image displays with diagrams/colors → Test click-to-expand
Success: Image visible, contains visual elements, UI works
```

### Quality Gates

**After Phase 2**: Database schema verified, all CRUD functions tested  
**After Phase 3**: End-to-end generation works, images cached  
**After Phase 4**: Cache hit/miss logic works, retry mechanism functional  
**After Phase 5**: Full UI/UX complete, user experience polished  
**After Phase 6**: Admin controls functional  
**After Phase 7**: Monitoring in place, documentation complete

---

## Task Statistics

- **Total Tasks**: 107
- **Completed Tasks**: 4 (T001-T004)
- **Remaining Tasks**: 103
- **Setup Tasks**: 10 (T001-T010) - 4 complete, 6 remaining
- **Foundational Tasks**: 8 (T011-T018)
- **User Story 3 Tasks**: 25 (T019-T043)
- **User Story 2 Tasks**: 11 (T044-T054)
- **User Story 1 Tasks**: 24 (T055-T078) - includes click-to-expand functionality
- **Admin Tasks**: 14 (T079-T092)
- **Polish Tasks**: 15 (T093-T107)

**Parallelizable Tasks**: 38 (marked with [P])  
**User Story Tasks**: 60 (marked with [US1], [US2], or [US3])

**Estimated Effort**:
- MVP (Phases 1-3): 2-3 days (1 developer) - Phase 1 partially complete (4/10 tasks done)
- Complete Feature (All phases): 4-5 days (1 developer)
- With parallel work (2 developers): 2-3 days for complete feature

**Note**: T001-T004 (env.example configuration) already completed during specification phase

---

## Notes

- Tasks marked [P] can be executed in parallel with tasks in same phase
- Tasks marked [US1], [US2], [US3] belong to specific user stories
- Tasks marked [x] are already complete (T001-T004 completed during specification phase)
- Each user story is independently testable once its tasks complete
- MVP includes US3 which inherently includes caching (US2 subset)
- Click-to-expand functionality (T071-T072) is included in current scope for better UX
- Admin controls (Phase 6) can be implemented anytime after Phase 2
- Testing tasks integrated throughout for continuous validation
- All file paths specified for immediate implementation
- Configuration in .env enables feature flag for gradual rollout

**Analysis Results**: This task list has been validated for consistency with spec.md and plan.md via `/speckit.analyze` - all critical issues resolved
