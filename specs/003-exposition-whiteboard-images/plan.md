# Technical Implementation Plan: Exposition Whiteboard Images

**Feature Branch**: `003-exposition-whiteboard-images`  
**Created**: 2025-11-27  
**Status**: Ready for Implementation  
**Technology**: Google Gemini Image Generation API (Nano Banana / Nano Banana Pro)

## Overview

This plan details the implementation of whiteboard-style image generation alongside text expositions using Google's Gemini image generation capabilities. The feature integrates with the existing exposition caching system (spec 002) to provide visual learning aids for mathematical concepts.

**Reference**: [Google Gemini Image Generation API Documentation](https://ai.google.dev/gemini-api/docs/image-generation)

## Technology Stack

### Image Generation Service

**Selected Service**: Google Gemini Image Generation API (aka "Nano Banana")

**Model Selection** (configured via `.env`):
- **Primary**: `gemini-3-pro-image` (Nano Banana Pro) at **2K resolution** (2048x2048)
- **Resolution**: 2K provides 4x the detail of 1K with the same token cost (1210 tokens)
- **Note**: Only Nano Banana Pro or higher quality models will be used, never the basic Nano Banana (gemini-2.5-flash-image)

**Rationale**:
- Native integration with Google AI SDK (already available if using Google for LLM)
- Excellent text rendering capabilities (critical for mathematical diagrams)
- PNG format output (lossless, ideal for diagrams with sharp lines)
- Cost-effective token-based pricing
- Built-in SynthID watermarking
- Supports conversational refinement (future enhancement opportunity)
- **Using Nano Banana Pro (gemini-3-pro-image)** for higher quality:
  - Includes "thinking" process for better composition and layout
  - Supports up to 4K resolution (future enhancement)
  - Better mathematical notation rendering
  - More accurate color usage and diagram clarity

### Integration Points

1. **Existing Systems**:
   - `bloom/database.py` - Extend with new table for image storage
   - `bloom/tutor_agent.py` - Modify `exposition_node()` to generate images
   - `bloom/models.py` - Add image data structures
   - `bloom/routes/student.py` - Add image serving endpoint

2. **New Components**:
   - Image generation client wrapper
   - Image validation utilities
   - Image storage/retrieval functions
   - Image serving endpoint

## Architecture

### Data Flow

```
Session Start
    ↓
Check for cached text exposition
    ↓
├─ Cache HIT (text exists)
│   ├─ Display text immediately
│   └─ Check for cached image
│       ├─ Image EXISTS → Retrieve & display instantly
│       └─ Image MISSING → Generate image asynchronously → Cache & display
│
└─ Cache MISS (no text)
    ├─ Generate text exposition → Cache → Display
    └─ Generate image (async) → Cache → Display
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Student Interface                         │
│  (chat.html + JavaScript for progressive image loading)     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│               Student Routes (student.py)                    │
│  • start_session()  • get_progress()  • serve_image() [NEW] │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────┐
│              Tutor Agent (tutor_agent.py)                    │
│  • exposition_node() [MODIFIED]                              │
│  • generate_whiteboard_image() [NEW]                         │
└────────────────┬────────────────────────────────────────────┘
                 │
       ┌─────────┴──────────┐
       ↓                    ↓
┌──────────────────┐   ┌───────────────────────────┐
│ Gemini Text LLM  │   │ Gemini Image Generation   │
│ (existing)       │   │ (google.genai.Client)     │
└──────────────────┘   └───────────────────────────┘
                                    │
                                    ↓
                          ┌──────────────────────┐
                          │ Database (bloom.db)  │
                          │ • cached_expositions │
                          │ • cached_images [NEW]│
                          └──────────────────────┘
```

## Database Schema

### New Table: `cached_images`

```sql
CREATE TABLE IF NOT EXISTS cached_images (
    subtopic_id INTEGER PRIMARY KEY,
    image_data BLOB NOT NULL,
    image_format TEXT NOT NULL DEFAULT 'PNG',
    generated_at TEXT NOT NULL,
    prompt_version TEXT NOT NULL DEFAULT 'v1',
    model_identifier TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
);
```

**Column Descriptions**:

| Column | Type | Description |
|--------|------|-------------|
| subtopic_id | INTEGER | Primary key, references `subtopics(id)` |
| image_data | BLOB | Binary PNG image data |
| image_format | TEXT | Always 'PNG' (per clarification) |
| generated_at | TEXT | ISO8601 timestamp of generation |
| prompt_version | TEXT | Version identifier for prompt template (e.g., 'v1') |
| model_identifier | TEXT | Model used (e.g., 'gemini-3-pro-image') |
| file_size | INTEGER | Size in bytes for monitoring |

**Indexes**: None needed (all lookups by primary key)

**Foreign Key Behavior**: `ON DELETE CASCADE` - if subtopic deleted, image is automatically removed

## Implementation Phases

### Phase 1: Database & Core Infrastructure (Priority: HIGH)

**Tasks**:
1. **Database Migration**
   - Add `cached_images` table to `init_database()` function
   - Create database helper functions:
     - `get_cached_image(subtopic_id: int) -> Optional[dict]`
     - `save_cached_image(subtopic_id: int, image_data: bytes, model_identifier: str, prompt_version: str) -> None`
     - `delete_cached_image(subtopic_id: int) -> None`
     - `delete_all_cached_images() -> int`
   - Add migration logic to handle existing databases

2. **Environment Configuration**
   - Add to `env.example`:
     ```
     # Image Generation (OPTIONAL)
     # Model for whiteboard image generation
     # Use Nano Banana Pro or higher for quality educational diagrams
     # Default: gemini-3-pro-image
     IMAGE_GENERATION_MODEL=gemini-3-pro-image
     
     # Image resolution for generation (1K, 2K, or 4K)
     # 2K (2048x2048) provides excellent quality at same cost as 1K
     # Default: 2K
     IMAGE_GENERATION_RESOLUTION=2K
     
     # Enable/disable image generation (for testing/fallback)
     # Default: true
     ENABLE_IMAGE_GENERATION=true
     ```
   - Use existing `GOOGLE_API_KEY` from current setup

3. **Data Models**
   - Add to `bloom/models.py`:
     ```python
     class CachedImage(TypedDict):
         subtopic_id: int
         image_data: bytes
         image_format: str
         generated_at: str
         prompt_version: str
         model_identifier: str
         file_size: int
     ```

**Acceptance Criteria**:
- Database table created successfully on fresh installations
- Existing databases migrate without errors
- Helper functions can store and retrieve image binary data
- Configuration loads from `.env` with sensible defaults

**Files Modified**:
- `bloom/database.py` (add table, migration, helper functions)
- `bloom/models.py` (add data models)
- `env.example` (add IMAGE_GENERATION_MODEL configuration)

---

### Phase 2: Image Generation Integration (Priority: HIGH)

**Tasks**:
1. **Google Gemini Image Client**
   - Install dependency: `google-genai` (check if already present for LLM)
   - Create image generation wrapper in `tutor_agent.py`:
     ```python
     async def generate_whiteboard_image(
         exposition_text: str,
         model: str = "gemini-3-pro-image",
         resolution: str = "2K"
     ) -> Optional[bytes]:
         """
         Generate whiteboard-style image from exposition text at 2K resolution.
         
         Args:
             exposition_text: The full text exposition content
             model: Gemini image model to use
             resolution: Image resolution (1K, 2K, or 4K) - defaults to 2K
             
         Returns:
             PNG image bytes, or None if generation fails
         """
         # Resolution configuration included in generation config
     ```

2. **Prompt Engineering**
   - Implement whiteboard prompt template (per specification):
     ```python
     WHITEBOARD_PROMPT_TEMPLATE = """now take the text from your reply and transform it into a professor's whiteboard image: diagrams, arrows, boxes, and captions explaining the core idea visually. Use colors as well.
     
     Text to visualize:
     {exposition_text}
     """
     ```
   - Test with various mathematical concepts (fractions, algebra, geometry)
   - Iterate on prompt if image quality insufficient

3. **Modify `exposition_node()`**
   - After caching text exposition, attempt image generation
   - Handle generation asynchronously (non-blocking)
   - Implement retry logic (per clarification: retry on every session start if missing)
   - Log all generation attempts, successes, and failures

4. **Image Validation**
   - Implement validation function (per clarification: technical only):
     ```python
     def validate_image_data(image_data: bytes) -> bool:
         """
         Validate image meets technical requirements.
         
         Checks:
         - Not corrupted (can be parsed as valid image)
         - Size under limit (e.g., 2MB)
         - Format is PNG
         """
     ```
   - Use PIL/Pillow for format validation
   - Reject and log invalid images without caching

**Acceptance Criteria**:
- Image generation successfully creates PNG files from text
- Generated images contain diagrams, colors, and visual elements
- Failed generations don't block text exposition display
- Invalid images are detected and rejected
- All generation events are logged

**Files Modified**:
- `bloom/tutor_agent.py` (add image generation, modify exposition_node)
- `requirements.txt` or `pyproject.toml` (ensure google-genai installed)

---

### Phase 3: Image Serving & Display (Priority: HIGH)

**Tasks**:
1. **Image Serving Endpoint**
   - Add route to `bloom/routes/student.py`:
     ```python
     @router.get("/api/image/{subtopic_id}")
     async def serve_image(subtopic_id: int):
         """
         Serve cached whiteboard image for a subtopic.
         
         Returns:
             Response with image/png content-type and binary data,
             or 404 if image not found
         """
     ```
   - Set appropriate cache headers for browser caching
   - Handle missing images gracefully (404)

2. **Frontend Integration**
   - Modify `templates/chat.html` to display images:
     - Add `<img>` placeholder in message template
     - Implement progressive loading (show text first, then image)
     - Add loading spinner for image generation
     - Handle missing images gracefully (no error display to user)
     - Implement click-to-expand functionality with modal/lightbox for detailed viewing

3. **JavaScript for Progressive Loading**
   - Poll `/api/image/{subtopic_id}` after text exposition loads
   - Display image when available
   - Show loading indicator during generation
   - Stop polling after successful load or timeout

4. **Message Format Enhancement**
   - Update message structure to include optional `image_url` field
   - Modify `components/message.html` to render images when present

**Acceptance Criteria**:
- Images display correctly in the chat interface
- Text appears before images (progressive loading)
- Loading indicators show during image generation
- Missing images don't break the UI
- Browser caches images appropriately
- Click-to-expand functionality allows detailed image viewing

**Files Modified**:
- `bloom/routes/student.py` (add image serving endpoint)
- `templates/chat.html` (add image display)
- `templates/components/message.html` (support image rendering)
- `static/js/chat.js` (add progressive loading logic)

---

### Phase 4: Admin Controls (Priority: MEDIUM)

**Tasks**:
1. **Admin Routes**
   - Add to `bloom/routes/admin.py`:
     ```python
     @router.post("/api/admin/clear-images")
     async def clear_all_images():
         """Clear all cached images."""
     
     @router.delete("/api/admin/image/{subtopic_id}")
     async def clear_subtopic_image(subtopic_id: int):
         """Clear image for specific subtopic."""
     ```

2. **Admin UI**
   - Add buttons to `templates/admin.html`:
     - "Clear All Images" button
     - "Clear This Image" button next to each subtopic
   - Show cache statistics (# images cached, total size)
   - Confirmation dialogs for destructive operations

**Acceptance Criteria**:
- Admins can clear all images via UI
- Admins can clear individual subtopic images
- Cache statistics display accurately
- Cleared images regenerate on next session access

**Files Modified**:
- `bloom/routes/admin.py` (add image management endpoints)
- `templates/admin.html` (add image cache controls)

---

### Phase 5: Monitoring & Observability (Priority: LOW)

**Tasks**:
1. **Logging Enhancement**
   - Log image generation events:
     - Cache hits/misses
     - Generation start/completion/failure
     - Generation duration
     - Image file sizes
     - Model used

2. **Metrics Tracking**
   - Track in database or logs:
     - Total images cached
     - Cache hit rate
     - Average generation time
     - Generation failure rate
     - Total storage used

3. **Error Handling**
   - Graceful degradation for all failure modes
   - Detailed error logging for debugging
   - User-facing errors hidden (per requirements)

**Acceptance Criteria**:
- All image operations logged at appropriate levels
- Cache performance metrics available for review
- Errors don't propagate to users
- Debugging information captured in logs

**Files Modified**:
- `bloom/tutor_agent.py` (enhance logging)
- `bloom/routes/admin.py` (add metrics display)

## Testing Strategy

### Unit Tests

**File**: `tests/test_whiteboard_images.py`

Tests to implement:
1. `test_generate_image_success()` - Image generation returns valid PNG
2. `test_generate_image_failure()` - Handles API failures gracefully
3. `test_validate_image_valid()` - Accepts valid PNG under size limit
4. `test_validate_image_corrupted()` - Rejects corrupted image data
5. `test_validate_image_too_large()` - Rejects oversized images
6. `test_cache_image()` - Stores image in database correctly
7. `test_retrieve_cached_image()` - Retrieves cached image successfully
8. `test_cache_miss()` - Returns None for non-existent image
9. `test_delete_image()` - Removes image from cache
10. `test_delete_all_images()` - Clears entire image cache

### Integration Tests

**File**: `tests/test_exposition_with_images.py`

Tests to implement:
1. `test_first_session_generates_text_and_image()` - Both generated and cached
2. `test_second_session_uses_cached_image()` - Cache hit for image
3. `test_text_cached_image_missing()` - Regenerates image only
4. `test_image_generation_failure_shows_text()` - Graceful degradation
5. `test_image_serves_via_endpoint()` - HTTP endpoint returns image
6. `test_progressive_loading_flow()` - Text before image

### Manual Testing Checklist

- [ ] Select subtopic for first time - text and image both generate
- [ ] Select same subtopic again - both load instantly from cache
- [ ] Verify image contains diagrams, colors, arrows, boxes
- [ ] Verify text appears before image (progressive loading)
- [ ] Test with slow network - loading indicator appears
- [ ] Simulate image API failure - text still displays
- [ ] Clear image cache - next session regenerates
- [ ] Clear specific subtopic image - only that one regenerates
- [ ] Test with 5+ different mathematical concepts
- [ ] Verify images are pedagogically useful
- [ ] Check browser developer tools - images cached properly
- [ ] Verify no errors displayed to students for failed generations

### Performance Testing

- Measure image generation time (target: <10 seconds)
- Measure cached image load time (target: <1 second)
- Verify database size with 50-100 cached images
- Test concurrent first-time access (no duplicate generations)

## Error Handling & Edge Cases

### Graceful Degradation

1. **Image Generation Fails**
   - Log error with details
   - Continue session with text only
   - Retry on next session start
   - No error message to student

2. **API Rate Limiting**
   - Implement exponential backoff for retries
   - Fall back to text-only mode
   - Log rate limit events

3. **Invalid API Key**
   - Detect and log configuration error
   - Disable image generation feature
   - Continue with text-only mode

4. **Corrupted Cached Image**
   - Detect during retrieval
   - Delete corrupted cache entry
   - Regenerate on current session
   - Log corruption event

5. **Database Storage Full**
   - Catch storage errors
   - Log critical error
   - Provide admin alert
   - Continue with text-only

### Configuration Management

**Feature Flags**:
```python
ENABLE_IMAGE_GENERATION = os.getenv('ENABLE_IMAGE_GENERATION', 'true').lower() == 'true'
IMAGE_GENERATION_MODEL = os.getenv('IMAGE_GENERATION_MODEL', 'gemini-3-pro-image')
IMAGE_GENERATION_RESOLUTION = os.getenv('IMAGE_GENERATION_RESOLUTION', '2K')
IMAGE_GENERATION_TIMEOUT = int(os.getenv('IMAGE_GENERATION_TIMEOUT', '30'))  # seconds
MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', '5242880'))  # 5MB in bytes (for 2K resolution images)
```

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing complete
- [ ] Database migration tested on copy of production DB
- [ ] `.env` updated with IMAGE_GENERATION_MODEL
- [ ] Google API key configured and tested
- [ ] Admin controls tested
- [ ] Rollback plan documented

### Deployment Steps

1. **Backup Database**
   ```bash
   cp bloom.db bloom.db.backup.$(date +%Y%m%d)
   ```

2. **Update Code**
   ```bash
   git pull origin 003-exposition-whiteboard-images
   ```

3. **Install Dependencies**
   ```bash
   uv sync
   ```

4. **Run Database Migration**
   ```bash
   python -c "from bloom.database import init_database; init_database()"
   ```

5. **Update Environment**
   ```bash
   # Add to .env:
   IMAGE_GENERATION_MODEL=gemini-3-pro-image
   IMAGE_GENERATION_RESOLUTION=2K
   ENABLE_IMAGE_GENERATION=true
   ```

6. **Restart Application**
   ```bash
   ./start.sh
   ```

7. **Smoke Test**
   - Start a session on a new subtopic
   - Verify text and image both generate
   - Start session again, verify instant loading
   - Check logs for errors

### Rollback Plan

If issues arise:

1. **Disable Feature**
   ```bash
   # In .env:
   ENABLE_IMAGE_GENERATION=false
   ```
   Restart application - feature disabled, text-only mode

2. **Full Rollback**
   ```bash
   git checkout main
   ./start.sh
   ```
   Previous functionality restored (images ignored)

## Cost Analysis

### Google Gemini Image Pricing

**Per Image Generation** (as of 2025-11-27):
- **gemini-3-pro-image** (Nano Banana Pro): ~$0.04-$0.06 per image (1210-2000 tokens depending on resolution)
  - 1K resolution (1024x1024): 1210 tokens = ~$0.036
  - 2K resolution (2048x2048): 1210 tokens = ~$0.036
  - 4K resolution (4096x4096): 2000 tokens = ~$0.060

### Cost Savings from Caching

**Scenario**: 50 subtopics, 100 students

**Without Caching**:
- 50 subtopics × 100 students = 5,000 image generations
- 5,000 × $0.04 = **$200.00**

**With Caching**:
- 50 subtopics × 1 generation = 50 image generations
- 50 × $0.04 = **$2.00**

**Savings**: $198.00 (99% cost reduction)

**Note**: Using Nano Banana Pro at 1K or 2K resolution keeps costs at ~$0.04 per image. 4K resolution would be ~$0.06 per image (50% more), but still provides 99% savings with caching.

### Storage Costs

- Average image size at 2K resolution: ~500-700KB  
- 50 subtopics: ~25-35MB total
- 100 subtopics: ~50-70MB total
- Storage negligible for demo application

## Security & Privacy

### Data Privacy

- Images generated from educational text (no student PII)
- Images shared across all students (no personalization)
- SynthID watermark included automatically by Google

### API Key Security

- Store GOOGLE_API_KEY in `.env` (not committed)
- Use existing API key management from LLM integration
- Validate key on application startup

### Input Validation

- Validate subtopic_id in all endpoints
- Sanitize any user input (though exposition text is LLM-generated)
- Limit image file size to prevent DoS

## Success Metrics

### Quantitative Metrics

- **Cache Hit Rate**: Target >90% after initial generation period
- **Image Load Time**: <1 second for cached 2K images, <10 seconds for generation
- **Generation Success Rate**: >95%
- **Storage Efficiency**: ~50-70MB for 100 subtopics at 2K resolution

### Qualitative Metrics

- **Image Quality**: 80% rated "clearly illustrates concept" (manual review)
- **Student Satisfaction**: 20% improvement in surveys (if conducted)
- **Educational Value**: Images reinforce text explanations effectively

### Monitoring Dashboard (Future Enhancement)

Potential admin dashboard metrics:
- Total images cached
- Cache hit/miss ratio
- Average generation time
- Total storage used
- Generation failure rate
- Most recently generated images

## Future Enhancements

### Phase 2+ Features (Out of Scope for MVP)

**Note**: Click-to-expand functionality has been moved INTO current scope (Phase 5) for enhanced UX.

1. **Conversational Image Refinement**
   - Allow students to request modifications ("make the diagram bigger", "add more color")
   - Use Gemini's multi-turn conversation capability
   - Cache multiple versions per subtopic

2. **4K Resolution & Advanced Zoom**
   - Upgrade from 2K to 4K resolution for ultra-detailed diagrams
   - Implement zoom/pan controls within expanded view
   - Conditional rendering based on student's device capabilities

3. **Accessibility Features**
   - Alt text generation for images
   - Text descriptions of visual elements
   - Screen reader support

4. **A/B Testing**
   - Compare learning outcomes with/without images
   - Test different prompt templates
   - Optimize for engagement and comprehension

5. **Image Editing**
   - Text-and-image-to-image for modifications
   - Style transfer between subtopics
   - Consistent visual branding

## References

- [Google Gemini Image Generation API](https://ai.google.dev/gemini-api/docs/image-generation)
- [Feature Specification](./spec.md)
- [Clarifications Session 2025-11-27](./spec.md#clarifications)
- [Existing Exposition Caching (Spec 002)](../002-cache-lesson-exposition/spec.md)
- [Original Bloom App Spec (Spec 001)](../001-bloom-tutor-app/spec.md)

## Appendix

### Example API Call

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

prompt = f"""now take the text from your reply and transform it into a professor's whiteboard image: diagrams, arrows, boxes, and captions explaining the core idea visually. Use colors as well.

Text to visualize:
{exposition_text}
"""

# Configure for 2K resolution (2048x2048)
config = types.GenerateContentConfig(
    response_modalities=["IMAGE"],
    # Note: Gemini 3 Pro defaults to appropriate resolution based on model
    # For 2K: images will be generated at 2048x2048 (1:1 aspect ratio)
)

response = client.models.generate_content(
    model=os.getenv('IMAGE_GENERATION_MODEL', 'gemini-3-pro-image'),
    contents=[prompt],
    config=config,
)

for part in response.parts:
    if part.inline_data is not None:
        image_data = part.inline_data.data  # PNG bytes at 2K resolution
        # Save to database...
```

### Database Query Examples

```python
# Save image
conn = get_connection()
conn.execute("""
    INSERT OR REPLACE INTO cached_images 
    (subtopic_id, image_data, image_format, generated_at, prompt_version, model_identifier, file_size)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (subtopic_id, image_data, 'PNG', datetime.utcnow().isoformat(), 'v1', model, len(image_data)))
conn.commit()

# Retrieve image
cursor = conn.execute("SELECT * FROM cached_images WHERE subtopic_id = ?", (subtopic_id,))
row = cursor.fetchone()
if row:
    return dict(row)

# Delete specific image
conn.execute("DELETE FROM cached_images WHERE subtopic_id = ?", (subtopic_id,))
conn.commit()

# Delete all images
cursor = conn.execute("DELETE FROM cached_images")
count = cursor.rowcount
conn.commit()
return count
```

---

**Plan Status**: ✅ COMPLETE  
**Ready for Implementation**: YES  
**Estimated Effort**: 3-5 days (1 developer)  
**Risk Level**: LOW (well-defined API, existing caching patterns to follow)

---

## Quality Validation

**Analysis Date**: 2025-11-27  
**Analysis Command**: `/speckit.analyze`  
**Result**: ✅ HIGH QUALITY - All critical issues resolved

**Fixes Applied**:
- MAX_IMAGE_SIZE clarified to 5242880 bytes (5MB) for 2K resolution images
- Model identifier examples updated to use gemini-3-pro-image (Nano Banana Pro)
- Consistency with spec.md and tasks.md verified

**Constitution Compliance**: 100% - Aligns with all core principles (simplicity, minimal boilerplate, rapid iteration)
