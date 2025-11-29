# Feature Specification: Exposition Whiteboard Images

**Feature Branch**: `003-exposition-whiteboard-images`  
**Created**: 2025-11-27  
**Status**: Draft  
**Input**: User description: "When we produce and cache the exposition for a topic / sub-topic, We should also generate an image using google Nano Banana Pro API using a specific whiteboard prompt that I have: 'now take the text from your reply and transform it into a professor's whiteboard image: diagrams, arrows, boxes, and captions explaining the core idea visually. Use colors as well.'"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visual Learning with Whiteboard Images (Priority: P1)

A student starts a tutoring session on a subtopic. After the text exposition loads, a whiteboard-style visual diagram appears showing the same concept with diagrams, arrows, boxes, and colorful captions. This visual representation reinforces the text explanation and helps visual learners grasp concepts more effectively.

**Why this priority**: Visual representations significantly improve learning retention and comprehension, especially for mathematical concepts. Different students have different learning styles, and providing both text and visual explanations accommodates visual learners while reinforcing understanding for all students.

**Independent Test**: Select a subtopic (e.g., "Fractions"), verify that both the text exposition and a whiteboard-style image appear in the chat. The image should contain diagrams, arrows, boxes, and colored text/elements that visually explain the concept from the exposition. Verify the image loads within 5 seconds of the text appearing.

**Acceptance Scenarios**:

1. **Given** a student starts a session on a subtopic, **When** the exposition text is displayed, **Then** a whiteboard-style image visualizing the concept is also displayed immediately below the text
2. **Given** a whiteboard image is generated, **When** a student views it, **Then** the image contains diagrams, arrows, boxes, and captions that match the content of the text exposition
3. **Given** a whiteboard image is displayed, **When** the student examines it, **Then** the image uses multiple colors to enhance visual clarity and distinguish different elements
4. **Given** the exposition explains a mathematical concept, **When** the whiteboard image is generated, **Then** the visual includes relevant mathematical notation, equations, or examples from the text
5. **Given** a student has a slow internet connection, **When** the image loads, **Then** a loading indicator appears until the image is fully displayed
6. **Given** image generation fails, **When** the error occurs, **Then** the text exposition still displays normally without the image, and no error message is shown to the student (graceful degradation)

---

### User Story 2 - Cached Whiteboard Images for Fast Loading (Priority: P1)

A student revisits a subtopic they or another student has studied before. The whiteboard image loads instantly alongside the text exposition, providing immediate visual and textual learning materials without delays.

**Why this priority**: Just like cached text expositions, cached whiteboard images reduce operational costs and improve performance. Image generation is typically slower and more resource-intensive than text generation, making caching even more critical for this feature.

**Independent Test**: Study a subtopic for the first time, note the whiteboard image. Exit and re-enter the same subtopic. Verify the identical whiteboard image appears instantly without regeneration. Check logs to confirm the image was retrieved from cache.

**Acceptance Scenarios**:

1. **Given** a subtopic has never been studied before, **When** the first student starts a session, **Then** both the text exposition and whiteboard image are generated and stored for reuse
2. **Given** a whiteboard image has been previously stored, **When** any student starts a session on that subtopic, **Then** the stored image is retrieved and displayed instantly
3. **Given** two students study the same subtopic, **When** both view the session, **Then** both see the identical whiteboard image
4. **Given** stored images for multiple subtopics exist, **When** a student switches between subtopics, **Then** each subtopic displays its correct corresponding whiteboard image
5. **Given** a stored image exists, **When** the image is displayed, **Then** the load time is under 1 second (compared to 5-10 seconds for initial generation)

---

### User Story 3 - First-Time Image Generation (Priority: P1)

When a subtopic is studied for the first time, the system generates both the text exposition and the whiteboard image. The text appears first (within 3 seconds), followed by the whiteboard image (within 5-10 seconds), providing progressive enhancement of the learning experience.

**Why this priority**: First-time generation must work seamlessly and not block or degrade the existing text exposition experience. Students should see content progressively rather than waiting for everything to complete.

**Independent Test**: Clear the cache for a subtopic, start a session, and verify the text exposition appears first, followed by the whiteboard image. Confirm both are saved to the cache for future sessions.

**Acceptance Scenarios**:

1. **Given** no cached exposition or image exists for a subtopic, **When** a student starts a session, **Then** the text exposition generates and displays first within 3 seconds
2. **Given** the text exposition has been displayed, **When** the whiteboard image generation completes, **Then** the image appears below the text within 10 seconds of session start
3. **Given** both text and image are generated successfully, **When** generation completes, **Then** both are cached together in the database for future use
4. **Given** image generation fails or times out, **When** the failure occurs, **Then** the text exposition remains visible and functional, and the session continues without the image
5. **Given** the image generation service is unavailable, **When** the session starts, **Then** only the text exposition is shown and cached, and image generation is automatically retried on every subsequent session start until successful
6. **Given** the text exposition is already cached but the image is not, **When** a session starts, **Then** the cached text displays immediately and the image is generated and cached asynchronously

---

### Edge Cases

- What happens if a technically invalid image is generated (corrupted, oversized, wrong format)? System validates that the image is valid PNG format, under size limits, and not corrupted; if validation fails, the image is not displayed or stored, and the failure is logged for admin review
- What if a stored image becomes corrupted or unavailable in the database? System detects missing or corrupted image data during retrieval, regenerates the image from the text exposition, and updates the database record
- How much storage space is needed for hundreds of subtopics? Storage requirements scale linearly with the number of subtopics; for a typical GCSE math curriculum (50-100 subtopics), database storage needs are reasonable for a demo application (images stored as binary data in the same database as text content)
- What if the image generation approach needs to be updated to improve quality? System includes a version identifier with stored images; admins can clear all images or clear specific subtopic images, then images regenerate automatically on next session access with the updated approach
- What happens if image generation is slower than text generation? System handles images independently from text, ensuring text exposition is never delayed by image processing
- What if the image generation service is unavailable for an extended period? System continues to retry image generation on every session start; once the service recovers, images are generated and cached automatically without manual intervention
- How do admins manage the image cache? Admins can clear all cached images (e.g., for testing or version updates) or clear a specific subtopic's image (e.g., to fix a problematic image); cleared images regenerate automatically on the next session access
- Can students zoom or expand the whiteboard images for better viewing? Images are displayed at a default size with click-to-expand functionality for detailed examination
- What if the text exposition is very long or complex? Image generation uses the full exposition text as context; the system is tested with typical exposition lengths (500-1000 words) to ensure quality
- What happens during concurrent first-time access to the same subtopic? Similar to text caching, the system handles concurrent generation gracefully, ensuring consistency without duplication
- How are images delivered to students? Images are retrieved from the database, encoded for web delivery, and displayed inline in the chat interface alongside the text exposition, with appropriate loading indicators and fallback behavior

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a whiteboard-style image for each subtopic exposition
- **FR-002**: System MUST use the prompt template: "now take the text from your reply and transform it into a professor's whiteboard image: diagrams, arrows, boxes, and captions explaining the core idea visually. Use colors as well." with the full exposition text included as context
- **FR-002a**: System MUST generate images in PNG format (lossless compression suitable for diagrams with text and sharp lines)
- **FR-003**: System MUST store generated whiteboard images persistently in the database as binary data, indexed by subtopic
- **FR-004**: System MUST check for a stored whiteboard image when retrieving the text exposition
- **FR-005**: System MUST display the stored whiteboard image alongside the text exposition instantly when available
- **FR-006**: System MUST generate a new whiteboard image only when no stored version exists for the requested subtopic
- **FR-007**: System MUST store the generated whiteboard image immediately after successful generation, including metadata: generation timestamp and version identifier
- **FR-008**: System MUST ensure stored images are associated with the correct subtopic to prevent mismatches
- **FR-009**: System MUST display the text exposition first, followed by the whiteboard image, to provide progressive content loading
- **FR-010**: System MUST handle image generation failures gracefully by displaying only the text exposition without showing errors to students
- **FR-010a**: System MUST automatically retry image generation on every session start when text exposition exists but image is missing, until generation succeeds
- **FR-011** `[LATER]`: System MUST validate generated images before storing by checking: file is not corrupted, file size is within acceptable limits (under 5MB to accommodate 2K resolution images), and image is in PNG format
- **FR-012** `[LATER]`: System MUST regenerate and re-store an image if the stored version is invalid, corrupted, or unavailable
- **FR-013** `[LATER]`: System SHOULD provide an admin function to clear all stored images
- **FR-013a** `[LATER]`: System SHOULD provide an admin function to clear the stored image for a specific subtopic by subtopic ID
- **FR-014** `[LATER]`: System SHOULD allow regenerating images by clearing and relying on automatic retry on next session access
- **FR-015** `[LATER]`: System SHOULD log image generation events (successful retrieval, new generation, generation time, failures) for monitoring and cost tracking
- **FR-016**: System SHOULD implement click-to-expand functionality for whiteboard images to allow detailed viewing
- **FR-017** `[LATER]`: System MAY include alt text or captions on images for accessibility

### Key Entities *(include if feature involves data)*

- **Stored Whiteboard Image**: A persistently stored whiteboard-style visual representation for a specific subtopic's exposition. Contains the image binary data in PNG format, the subtopic it belongs to, generation timestamp (when it was created), and version identifier (e.g., "v1" to track generation approach changes). Stored directly in the database alongside text expositions for consistency, backup, and migration simplicity. Retrieved on-demand during session initialization to display alongside the text exposition. The version identifier enables selective invalidation when the image generation approach is improved.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For subtopics with stored images, image display time is under 1 second (measured from session start to image visible to student)
- **SC-002**: Image generation operations are reduced by at least 90% in typical usage where students revisit topics or multiple students study the same topics
- **SC-003**: 100% of stored whiteboard images display correctly without corruption or errors
- **SC-004**: In testing with 20 subtopics, after initial generation, 100% of subsequent sessions retrieve stored images successfully
- **SC-005**: At least 80% of generated whiteboard images are rated by reviewers as "clearly illustrating the concept" in quality assessment testing
- **SC-006**: Students viewing sessions with whiteboard images report higher satisfaction (target: 20% improvement) compared to text-only sessions in user surveys
- **SC-007**: Session start experience remains smooth with text appearing within 3 seconds and images appearing within 10 seconds for first-time sessions
- **SC-008**: Image generation failures occur in less than 5% of attempts and never prevent text exposition from displaying
- **SC-009**: Storage requirements scale reasonably with the number of subtopics in the curriculum
- **SC-010**: Operational cost per subtopic is reduced by at least 85% after the first generation due to content reuse

## Clarifications

### Session 2025-11-27

- Q: What criteria define a failed image validation? → A: Only validate technical properties (file not corrupted, size under 5MB for 2K resolution images, valid PNG format)
- Q: When image generation fails due to service unavailability, what is the retry strategy? → A: Retry on every session start (when text exists but image doesn't) until successful
- Q: Where should images be stored - database or file system? → A: Store images as binary data directly in database (consistent with text caching approach)
- Q: What admin cache invalidation capabilities are needed? → A: "Clear all images" and "clear image for specific subtopic" functions
- Q: What image format should the system use? → A: PNG format only (lossless, best for diagrams with text and sharp lines)

## Assumptions

- An image generation service is available and configured in the application environment
- The image generation service can produce PNG format images suitable for educational diagrams with text and sharp lines
- Image generation takes approximately 5-10 seconds per request, which is acceptable for first-time session initialization
- Students have sufficient internet connectivity to load PNG images (typically under 1MB per image) within a reasonable time
- Whiteboard images generated from the same exposition text are sufficiently consistent in quality and style to provide a standardized learning experience
- Images do not need to be personalized per student—all students studying the same subtopic receive the same whiteboard image
- Database storage infrastructure supports storing binary image data alongside text content for consistency and simplified backup/migration
- Image generation costs are reasonable and acceptable for the demo scope
- The whiteboard prompt template is sufficient to produce high-quality educational images without additional customization
- Images are displayed inline in the chat interface alongside messages, similar to how text messages are displayed
- Alt text or accessibility features for images can be added in a later iteration—initial MVP focuses on visual learners with standard vision
- Image storage follows similar patterns as text exposition storage for consistency
- The image generation service respects the prompt structure and reliably produces educational diagrams (quality will be validated during initial testing)
- If image generation is slow or unreliable in practice, the feature can fall back to text-only mode without affecting core functionality
- The whiteboard prompt produces images that are pedagogically effective without requiring subject-matter expert review for every subtopic

