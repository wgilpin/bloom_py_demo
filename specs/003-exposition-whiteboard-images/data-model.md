# Data Model: Exposition Whiteboard Images

**Date**: 2025-11-27  
**Database**: SQLite (`bloom.db`)  
**Related**: Extends existing schema documented in `/specs/001-bloom-tutor-app/data-model.md` and `/specs/002-cache-lesson-exposition/data-model.md`

## Overview

This feature adds a single table (`cached_images`) to store whiteboard-style PNG images generated for each subtopic's exposition. The table structure mirrors the existing `cached_expositions` table for consistency.

All timestamps use ISO8601 format (`YYYY-MM-DDTHH:MM:SS.ffffff`).

---

## Schema Changes

### New Table: `cached_images`

Stores generated whiteboard images as binary PNG data for reuse across sessions.

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

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| subtopic_id | INTEGER | PRIMARY KEY, FOREIGN KEY | Unique subtopic ID (links to `subtopics.id`) |
| image_data | BLOB | NOT NULL | Binary PNG image data at 2K resolution (~200KB-1MB per image) |
| image_format | TEXT | NOT NULL, DEFAULT 'PNG' | Always 'PNG' for lossless diagram quality |
| generated_at | TEXT | NOT NULL | ISO8601 timestamp when image was generated |
| prompt_version | TEXT | NOT NULL, DEFAULT 'v1' | Version identifier for prompt template (enables selective invalidation) |
| model_identifier | TEXT | NOT NULL | Gemini model used (e.g., "gemini-3-pro-image" or higher quality models) |
| file_size | INTEGER | NOT NULL | Image size in bytes for monitoring and validation |

**Indexes**: None needed (all lookups by primary key)

**Foreign Key Behavior**:
- `ON DELETE CASCADE`: If a subtopic is removed, its cached image is automatically deleted
- Ensures referential integrity with syllabus structure

**Storage Estimates** (at 2K resolution):
- Typical image: 200KB-1MB (depending on diagram complexity)
- 50 subtopics (typical GCSE math): 10-50MB total
- 100 subtopics (comprehensive): 20-100MB total
- Well within SQLite BLOB limits (up to 2GB per BLOB)

---

## Sample Data

```sql
-- First subtopic with cached image (Nano Banana Pro at 2K resolution)
INSERT INTO cached_images (
    subtopic_id, 
    image_data, 
    image_format, 
    generated_at, 
    prompt_version, 
    model_identifier, 
    file_size
) VALUES (
    101, 
    X'89504E470D0A1A0A0000000D494844...', -- PNG binary data at 2048x2048 (truncated)
    'PNG',
    '2025-11-27T10:30:00.000000',
    'v1',
    'gemini-3-pro-image',
    687432  -- ~670KB for typical 2K diagram
);

-- Another subtopic with more complex diagram
INSERT INTO cached_images (
    subtopic_id, 
    image_data, 
    image_format, 
    generated_at, 
    prompt_version, 
    model_identifier, 
    file_size
) VALUES (
    102, 
    X'89504E470D0A1A0A0000000D494844...', -- PNG binary data at 2048x2048 (truncated)
    'PNG',
    '2025-11-27T11:15:23.456789',
    'v1',
    'gemini-3-pro-image',
    923154  -- ~900KB for complex diagram with lots of detail
);
```

---

## Relationship Diagram

```
┌─────────────────────┐
│      topics         │
│  (existing table)   │
└──────────┬──────────┘
           │
           │ 1:N
           ↓
┌─────────────────────┐
│     subtopics       │
│  (existing table)   │
└──────────┬──────────┘
           │
           ├─────────────────────┐
           │ 1:1                 │ 1:1
           ↓                     ↓
┌──────────────────────┐   ┌───────────────────┐
│ cached_expositions   │   │  cached_images    │
│  (spec 002 table)    │   │  (NEW - spec 003) │
│                      │   │                   │
│ • subtopic_id (PK)   │   │ • subtopic_id (PK)│
│ • exposition_content │   │ • image_data      │
│ • generated_at       │   │ • image_format    │
│ • model_identifier   │   │ • generated_at    │
│                      │   │ • prompt_version  │
│                      │   │ • model_identifier│
│                      │   │ • file_size       │
└──────────────────────┘   └───────────────────┘
```

**Key Points**:
- One subtopic → One cached exposition (optional)
- One subtopic → One cached image (optional)
- Both cached content types reference the same subtopic
- Images can exist independently if text cached but image generation failed (triggers retry)
- Text expositions can exist without images (graceful degradation)

---

## Query Patterns

### Retrieve Cached Image

```sql
-- Get full image record
SELECT * FROM cached_images WHERE subtopic_id = ?;

-- Get only image data for serving
SELECT image_data, image_format FROM cached_images WHERE subtopic_id = ?;

-- Check if image exists (before generation attempt)
SELECT COUNT(*) FROM cached_images WHERE subtopic_id = ?;
```

### Save New Image

```sql
-- Insert or replace (upsert pattern)
INSERT OR REPLACE INTO cached_images (
    subtopic_id, image_data, image_format, generated_at, 
    prompt_version, model_identifier, file_size
) VALUES (?, ?, 'PNG', ?, 'v1', ?, ?);
```

### Admin Operations

```sql
-- Clear all images
DELETE FROM cached_images;

-- Clear specific subtopic image
DELETE FROM cached_images WHERE subtopic_id = ?;

-- Clear images by model (when switching providers)
DELETE FROM cached_images WHERE model_identifier = ?;

-- Clear images by prompt version (when updating prompt)
DELETE FROM cached_images WHERE prompt_version = ?;

-- Get cache statistics
SELECT 
    COUNT(*) as total_images,
    SUM(file_size) as total_size_bytes,
    AVG(file_size) as avg_size_bytes,
    MIN(generated_at) as oldest_image,
    MAX(generated_at) as newest_image
FROM cached_images;
```

### Monitoring Queries

```sql
-- Find subtopics with text but no image (needs generation)
SELECT s.id, s.name 
FROM subtopics s
INNER JOIN cached_expositions ce ON s.id = ce.subtopic_id
LEFT JOIN cached_images ci ON s.id = ci.subtopic_id
WHERE ci.subtopic_id IS NULL;

-- Find large images (potential optimization targets)
SELECT subtopic_id, file_size 
FROM cached_images 
WHERE file_size > 1000000  -- > 1MB
ORDER BY file_size DESC;

-- Find recently generated images
SELECT subtopic_id, generated_at, model_identifier 
FROM cached_images 
ORDER BY generated_at DESC 
LIMIT 10;
```

---

## Migration Strategy

### For New Installations

Table is created automatically by `init_database()` function in `bloom/database.py`.

### For Existing Installations

**Migration Code** (add to `init_database()`):

```python
def init_database(db_path: str = "bloom.db") -> None:
    """Initialize database schema if not exists."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # ... existing table creation code ...
    
    # NEW: Add cached_images table (spec 003)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cached_images (
            subtopic_id INTEGER PRIMARY KEY,
            image_data BLOB NOT NULL,
            image_format TEXT NOT NULL DEFAULT 'PNG',
            generated_at TEXT NOT NULL,
            prompt_version TEXT NOT NULL DEFAULT 'v1',
            model_identifier TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            FOREIGN KEY (subtopic_id) REFERENCES subtopics(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
```

**Migration Test**:
```python
# Test on copy of production database
import shutil
shutil.copy('bloom.db', 'bloom.db.test')

from bloom.database import init_database
init_database('bloom.db.test')

# Verify table exists
import sqlite3
conn = sqlite3.connect('bloom.db.test')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cached_images'")
assert cursor.fetchone() is not None, "Migration failed"
```

**Rollback**: No changes to existing tables - safe to deploy

---

## Data Integrity

### Constraints Enforced

1. **Referential Integrity**: `FOREIGN KEY` ensures images only exist for valid subtopics
2. **Non-Null Data**: All critical fields (image_data, timestamps) cannot be NULL
3. **Format Consistency**: image_format defaults to 'PNG' and should always be 'PNG'
4. **Size Validation**: Enforced at application level before INSERT (max 2MB)

### Validation Rules (Application Level)

```python
def validate_image_before_save(image_data: bytes, model: str) -> bool:
    """
    Validate image data before caching.
    
    Rules:
    - Must be valid PNG format
    - Size must be under MAX_IMAGE_SIZE (2MB)
    - Must be parseable as image
    
    Returns:
        True if valid, False otherwise
    """
    from PIL import Image
    import io
    
    # Check size
    if len(image_data) > MAX_IMAGE_SIZE:
        return False
    
    # Check format
    try:
        img = Image.open(io.BytesIO(image_data))
        if img.format != 'PNG':
            return False
        img.verify()  # Check integrity
        return True
    except Exception:
        return False
```

---

## Performance Considerations

### Query Optimization

- **Primary key lookups**: O(log n) - very fast even with thousands of images
- **BLOB storage**: SQLite handles BLOBs efficiently up to 2GB
- **No indexes needed**: All queries use primary key

### Storage Optimization

- **Compression**: PNG format already uses lossless compression
- **Size limits**: 2MB maximum prevents database bloat
- **Cascade deletes**: Automatic cleanup when subtopics removed

### Caching Strategy

- **Read-through cache**: Check database, generate if missing
- **Write-through cache**: Save immediately after generation
- **No TTL**: Images valid indefinitely until manually invalidated

---

## Backup & Recovery

### Backup Strategy

Images are part of the main `bloom.db` file:

```bash
# Full database backup (includes images)
cp bloom.db bloom.db.backup.$(date +%Y%m%d)

# SQLite backup command (online backup)
sqlite3 bloom.db ".backup bloom.db.backup"
```

### Recovery Scenarios

1. **Corrupted Image in Database**
   - Delete specific image: `DELETE FROM cached_images WHERE subtopic_id = ?`
   - System regenerates on next session access

2. **Full Database Corruption**
   - Restore from backup
   - Worst case: Delete `cached_images` table, images regenerate on demand

3. **Accidental Deletion**
   - Restore from backup
   - Or let system regenerate (50 images × $0.04 = $2.00)

---

## Monitoring & Maintenance

### Health Checks

```sql
-- Check for orphaned images (subtopic deleted but image remains)
-- Should be none due to CASCADE, but verify
SELECT ci.subtopic_id 
FROM cached_images ci
LEFT JOIN subtopics s ON ci.subtopic_id = s.id
WHERE s.id IS NULL;

-- Check total cache size
SELECT 
    COUNT(*) as image_count,
    ROUND(SUM(file_size) / 1024.0 / 1024.0, 2) as total_mb
FROM cached_images;

-- Check for unusually large images
SELECT subtopic_id, ROUND(file_size / 1024.0, 2) as size_kb
FROM cached_images
WHERE file_size > 1048576  -- > 1MB
ORDER BY file_size DESC;
```

### Maintenance Tasks

1. **Regular Monitoring**: Check cache hit rate via logs
2. **Quarterly Review**: Verify image quality hasn't degraded
3. **Version Updates**: When prompt changes, clear old images:
   ```sql
   DELETE FROM cached_images WHERE prompt_version = 'v1';
   -- New images regenerate with 'v2'
   ```

---

## Comparison with Text Caching

| Aspect | Text Expositions (spec 002) | Whiteboard Images (spec 003) |
|--------|----------------------------|------------------------------|
| **Storage Type** | TEXT (~3-4KB) | BLOB (~100-500KB) |
| **Primary Key** | subtopic_id | subtopic_id |
| **Generation Time** | ~3 seconds | ~5-10 seconds |
| **Cost per Generation** | ~$0.001 | ~$0.04 |
| **Format** | UTF-8 text | PNG binary |
| **Versioning** | model_identifier | model_identifier + prompt_version |
| **Validation** | Text length | PNG format + size limit |
| **Serving** | Direct in HTML | HTTP endpoint with MIME type |

---

## Future Considerations

### Potential Schema Enhancements (Out of Scope for MVP)

1. **Multiple Images per Subtopic**
   - Change PK to `(subtopic_id, image_version)`
   - Support different prompts or resolutions

2. **Image Metadata**
   - Add columns: `width`, `height`, `resolution`
   - Track generation parameters

3. **Thumbnail Support**
   - Add `thumbnail_data` BLOB column
   - Generate small preview for admin UI

4. **Alt Text for Accessibility**
   - Add `alt_text` TEXT column
   - Generate descriptions for screen readers

5. **Image Stats Table**
   - Separate table for analytics
   - Track views, load times, user ratings

---

**Schema Status**: ✅ COMPLETE  
**Ready for Implementation**: YES  
**Database Impact**: LOW (single new table, no existing table modifications)
