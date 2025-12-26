# Tasks: Advanced Calculator Functions

**Input**: Design documents from `/specs/004-calculator-advanced-functions/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL per constitution. This task list focuses on implementation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `bloom/` at repository root (FastAPI + htmx integrated)
- Calculator code is inline in `bloom/templates/chat.html` (no separate calculator.js file)
- All paths shown below use this structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Understand existing calculator implementation and prepare for extension

- [x] T001 Review existing calculator implementation in bloom/templates/chat.html to understand current structure (4-column grid, calcAppend, calcEvaluate functions)
- [x] T002 Document current calculator state variables and function signatures in bloom/templates/chat.html

**Checkpoint**: Understanding of existing calculator code complete

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core calculator infrastructure that MUST be complete before user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Initialize calculator state variables in bloom/templates/chat.html: calculatorMemory (0), lastAnswer (0), inputState ('normal'), pendingOperation (null), pendingValue (null), shiftMode (false)
- [x] T004 Create expression transformation function transformExpression() in bloom/templates/chat.html that converts calculator syntax to JavaScript Math functions (sin → Math.sin with degrees conversion, π → Math.PI, etc.)
- [x] T005 Create expression validation function validateExpression() in bloom/templates/chat.html that checks for division by zero, invalid trigonometric inputs, mismatched parentheses, square root of negative numbers
- [x] T006 Create error state management function setErrorState() in bloom/templates/chat.html that displays "Maths Error" and disables memory buttons when error occurs
- [x] T007 Update calcEvaluate() function in bloom/templates/chat.html to use transformExpression() and validateExpression() before evaluation, handle "Maths Error" display

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Scientific and Trigonometric Functions (Priority: P1) 🎯 MVP

**Goal**: Students can use trigonometric functions, powers, roots, scientific notation, π constant, reciprocal, and sign change in the calculator

**Independent Test**: Open tutoring session on trigonometry subtopic, verify calculator shows sin/cos/tan buttons, calculate sin(30) = 0.5, test x^y, sqrt, ×10^x, π, 1/x, +/- functions

### Implementation for User Story 1

**Calculator Layout (5×7 Grid)**:
- [x] T008 [US1] Update calculator button grid in bloom/templates/chat.html from 4-column to 5-column grid (grid-cols-5)
- [x] T009 [US1] Add Row 1 buttons in bloom/templates/chat.html: SHIFT, Pi, MC, MR, M+ (placeholders, handlers added in US2 for memory)
- [x] T010 [US1] Add Row 2 buttons in bloom/templates/chat.html: sin, cos, tan, (, ) (parentheses already exist, verify they work)
- [x] T011 [US1] Add Row 3 buttons in bloom/templates/chat.html: x^2, x^y, sqrt, AC (rename C to AC), DEL
- [x] T012 [US1] Update Row 4 in bloom/templates/chat.html: keep 7, 8, 9, add 1/x, keep /
- [x] T013 [US1] Update Row 5 in bloom/templates/chat.html: keep 4, 5, 6, add x10^x, keep *
- [x] T014 [US1] Update Row 6 in bloom/templates/chat.html: keep 1, 2, 3, add +/-, keep -
- [x] T015 [US1] Update Row 7 in bloom/templates/chat.html: keep 0, ., add Ans, keep =, keep +

**Trigonometric Functions**:
- [x] T016 [US1] Create handleSin() function in bloom/templates/chat.html that appends "sin(" to expression and handles SHIFT mode for arcsin
- [x] T017 [US1] Create handleCos() function in bloom/templates/chat.html that appends "cos(" to expression and handles SHIFT mode for arccos
- [x] T018 [US1] Create handleTan() function in bloom/templates/chat.html that appends "tan(" to expression and handles SHIFT mode for arctan
- [x] T019 [US1] Create handleShift() function in bloom/templates/chat.html that toggles shiftMode and updates sin/cos/tan button labels to arcsin/arccos/arctan
- [x] T020 [US1] Create updateButtonLabels() function in bloom/templates/chat.html that updates sin/cos/tan button text based on shiftMode state

**Powers and Roots**:
- [x] T021 [US1] Create handleSquare() function in bloom/templates/chat.html that squares the current display value (x²)
- [x] T022 [US1] Create handleXToY() function in bloom/templates/chat.html that sets inputState to 'waiting_base' and pendingOperation to 'x^y' for multi-step input
- [x] T023 [US1] Create handleSqrt() function in bloom/templates/chat.html that appends "sqrt(" to expression
- [x] T024 [US1] Create handleCubeRoot() function in bloom/templates/chat.html that calculates cube root using Math.cbrt() (if nth root button not yet implemented, add ∛ button)
- [x] T025 [US1] Create handleNthRoot() function in bloom/templates/chat.html that sets inputState to 'waiting_root' and pendingOperation to 'nth_root' for multi-step input

**Scientific Notation**:
- [x] T026 [US1] Create handleScientificNotation() function in bloom/templates/chat.html that sets inputState to 'waiting_coefficient' and pendingOperation to 'scientific' for multi-step input

**Utility Functions**:
- [x] T027 [US1] Create handlePi() function in bloom/templates/chat.html that appends "π" to expression (will be transformed to Math.PI in transformExpression)
- [x] T028 [US1] Create handleReciprocal() function in bloom/templates/chat.html that calculates 1/x of current display value
- [x] T029 [US1] Create handleSignChange() function in bloom/templates/chat.html that toggles sign of current display value (+/-)
- [x] T030 [US1] Create handleAns() function in bloom/templates/chat.html that appends lastAnswer to expression
- [x] T031 [US1] Create handleDelete() function in bloom/templates/chat.html that removes last character from expression (DEL button)
- [x] T032 [US1] Update calcClear() function in bloom/templates/chat.html to reset all state variables (inputState, pendingOperation, pendingValue, shiftMode) and rename to handleAllClear() for AC button

**Multi-Step Input Handling**:
- [x] T033 [US1] Update calcAppend() function in bloom/templates/chat.html to handle multi-step input states (waiting_base, waiting_exponent, waiting_root, waiting_radicand, waiting_coefficient)
- [x] T034 [US1] Create completeMultiStepOperation() function in bloom/templates/chat.html that constructs expression from pendingOperation and pendingValue, evaluates, and resets state

**Expression Evaluation Enhancement**:
- [x] T035 [US1] Update transformExpression() in bloom/templates/chat.html to handle trigonometric functions with degrees-to-radians conversion (sin(30) → Math.sin(30 * Math.PI / 180))
- [x] T036 [US1] Update transformExpression() in bloom/templates/chat.html to handle inverse trigonometric functions with radians-to-degrees conversion (asin(0.5) → Math.asin(0.5) * 180 / Math.PI)
- [x] T037 [US1] Update transformExpression() in bloom/templates/chat.html to handle sqrt, cbrt, pow, π constant, and scientific notation patterns
- [x] T038 [US1] Update validateExpression() in bloom/templates/chat.html to check for invalid arcsin/acos inputs (outside [-1, 1]), square root of negative numbers, nth root of negative with even root

**Error Handling**:
- [x] T039 [US1] Update setErrorState() in bloom/templates/chat.html to disable memory buttons (M+, MC, MR) when error state is active
- [x] T040 [US1] Update calcEvaluate() in bloom/templates/chat.html to store result in lastAnswer variable for Ans button functionality

**Checkpoint**: User Story 1 should be fully functional - all scientific and trigonometric functions working, multi-step input working, error handling working

---

## Phase 4: User Story 2 - Memory Functions (Priority: P2)

**Goal**: Students can store intermediate results in calculator memory, recall them, and clear memory

**Independent Test**: Calculate 15*16=240, press M+, calculate 10+5=15, press MR, verify 240 is recalled, use in calculation, press MC, verify MR returns 0

### Implementation for User Story 2

- [x] T041 [US2] Create handleMPlus() function in bloom/templates/chat.html that adds current displayValue to calculatorMemory (if not error state)
- [x] T042 [US2] Create handleMClear() function in bloom/templates/chat.html that sets calculatorMemory to 0
- [x] T043 [US2] Create handleMRecall() function in bloom/templates/chat.html that appends calculatorMemory to expression (or displays 0 if memory is 0)
- [x] T044 [US2] Update setErrorState() in bloom/templates/chat.html to disable M+, MC, MR buttons when error state is active (add button IDs if needed)
- [x] T045 [US2] Update handleMPlus() in bloom/templates/chat.html to check for error state before allowing memory operation
- [x] T046 [US2] Add unit test in tests/test_calculator_memory.js for memory accumulation: test that M+ with value 10, then M+ with value 20, MR should show 30

**Checkpoint**: User Story 2 should be fully functional - memory operations working correctly, disabled on error state

---

## Phase 5: User Story 3 - Expression Grouping and Parentheses (Priority: P2)

**Goal**: Students can use parentheses to group operations and ensure correct order of operations

**Independent Test**: Enter "2 * (3 + 4)" using parentheses buttons, verify result is 14 (not 10), test nested parentheses "2 * ((3 + 4) * 2)" = 28

### Implementation for User Story 3

**Note**: Parentheses buttons already exist in current calculator. This phase ensures they work correctly with advanced functions.

- [x] T047 [US3] Verify parentheses buttons ( and ) in bloom/templates/chat.html work correctly with existing calcAppend() function
- [x] T048 [US3] Update validateExpression() in bloom/templates/chat.html to detect mismatched parentheses and return "Maths Error" before evaluation
- [x] T049 [US3] Add unit test in tests/test_calculator_logic.js for nested parentheses evaluation: test that expressions like "2 * ((3 + 4) * 2)" evaluate correctly (result: 28) - test transformExpression() and validateExpression() with nested parentheses patterns
- [x] T050 [US3] Add unit test in tests/test_calculator_logic.js for parentheses with advanced functions: test that expressions like "sin(30) + (5 * 2)" evaluate correctly - verify transformExpression() handles parentheses with trigonometric functions
- [ ] T051 [US3] Test error case: enter "2 * (3 + 4" (missing closing parenthesis), verify "Maths Error" is displayed (will be covered by validateExpression() test in T062 - uncheck until T062 is complete)

**Checkpoint**: User Story 3 should be fully functional - parentheses work correctly, nested parentheses work, error handling for mismatched parentheses

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, calculator history logging, and UI polish

**Calculator History Logging**:
- [ ] T052 Update calcEvaluate() in bloom/templates/chat.html to log calculation to server via POST /calculator/compute endpoint (if endpoint exists) or add TODO for future implementation
- [ ] T053 Verify calculator history logging includes expression text with function names (e.g., "sin(30) + 5") for tutor reference (FR-020)

**UI Polish**:
- [ ] T054 Add visual feedback for SHIFT button active state in bloom/templates/chat.html (highlight or change color when shiftMode is true)
- [ ] T055 Add button styling classes in bloom/templates/chat.html to distinguish function buttons (sin/cos/tan), memory buttons (M+/MC/MR), and utility buttons (π, Ans, +/-)
- [ ] T056 Verify calculator display shows prompt text during multi-step input (e.g., "Enter base:", "Enter exponent:") - may require display update function

**Error Handling Polish**:
- [ ] T057 Verify all error cases display "Maths Error" consistently: division by zero, sqrt(-4), arcsin(2), mismatched parentheses
- [ ] T058 Verify memory buttons are visually disabled (not just non-functional) when error state is active

**Backend Evaluation (htmx Architecture - Refactored)**:
- [x] T059 Create Python calculator evaluation module bloom/calculator_evaluator.py with transform_expression(), validate_expression(), and evaluate_expression() functions
- [x] T060 Add FastAPI endpoint POST /calculator/evaluate in bloom/routes/student.py for server-side expression evaluation
- [x] T061 Create Python unit tests tests/test_calculator_evaluator.py for all calculator logic functions (41 tests covering transformation, validation, and evaluation)
- [x] T062 Update bloom/templates/chat.html to call backend /calculator/evaluate endpoint via fetch() instead of client-side eval()
- [x] T063 Remove client-side transformExpression() and validateExpression() functions from chat.html (now handled server-side)

**Architecture Note**: Calculator evaluation was refactored from client-side JavaScript (with ES6 modules) to server-side Python evaluation following the htmx pattern. This provides:
  - Single source of truth (Python backend)
  - Easier testing (Python unit tests vs JavaScript)
  - Better security (server-side validation)
  - Consistent with htmx philosophy (minimal client JS, server-driven)
  - Calculator history logging happens server-side automatically

**Integration Testing**:
- [x] T064 Python unit tests verify calculator evaluation logic works (41/41 tests passed in tests/test_calculator_evaluator.py)
- [ ] T065 Manual test: Start development server and test POST /calculator/evaluate endpoint with curl or browser
- [ ] T066 Manual test: Complete calculation flow with all advanced functions per quickstart.md test checklist
- [ ] T067 Manual test: Verify calculator appears/hides correctly based on question type (existing functionality, should still work)
- [ ] T068 Manual test: Verify calculator history is logged correctly for tutor reference (check database calculator_history table via endpoint)

**Note**: Server-side calculator evaluation is fully implemented and tested. Manual testing requires:
  1. Install dependencies: `pip install jinja2` (if not already installed)
  2. Start server: `python -m bloom.main` or `uvicorn bloom.main:app --reload`
  3. Navigate to chat page and test calculator functions
  4. Verify POST /calculator/evaluate endpoint: `curl -X POST http://localhost:8000/calculator/evaluate -d "expression=sin(30)+5"`

**Checkpoint**: All features complete, calculator fully functional with advanced functions, memory, and parentheses support

---

## Dependencies

### User Story Completion Order

1. **Phase 2 (Foundational)** → **MUST complete before any user story**
   - Calculator state variables, expression transformation, validation, error handling

2. **Phase 3 (US1 - Scientific Functions)** → **Can start after Phase 2**
   - Independent: All scientific and trigonometric functions
   - Provides: Button layout, multi-step input, expression evaluation

3. **Phase 4 (US2 - Memory Functions)** → **Can start after Phase 2, benefits from US1 error handling**
   - Depends on: Error state management (Phase 2)
   - Independent: Memory operations don't require scientific functions

4. **Phase 5 (US3 - Parentheses)** → **Can start after Phase 2**
   - Depends on: Expression validation (Phase 2)
   - Independent: Parentheses already exist, just need validation

5. **Phase 6 (Polish)** → **MUST complete after all user stories**
   - Depends on: All user stories complete

### Parallel Execution Opportunities

**Within Phase 3 (US1)**:
- T008-T015 (Layout buttons) can be done in parallel
- T016-T020 (Trigonometric functions) can be done in parallel
- T021-T025 (Powers and roots) can be done in parallel
- T026-T032 (Utility functions) can be done in parallel
- T033-T034 (Multi-step input) must be sequential
- T035-T038 (Expression transformation) must be sequential

**Within Phase 4 (US2)**:
- T041-T043 (Memory functions) can be done in parallel
- T044-T045 (Error state integration) must be after T041-T043

**Within Phase 5 (US3)**:
- T047-T051 can be done mostly in parallel (testing tasks)

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**MVP = Phase 2 + Phase 3 (US1)**

This delivers:
- ✅ All scientific and trigonometric functions (sin, cos, tan, inverses)
- ✅ Powers (x², x^y)
- ✅ Roots (√, ∛, nth root)
- ✅ Scientific notation (×10^x)
- ✅ Utility functions (π, 1/x, +/-, Ans)
- ✅ Multi-step input handling
- ✅ Error handling with "Maths Error"
- ✅ 5×7 button grid layout

**MVP does NOT include**:
- Memory functions (US2) - can be added later
- Enhanced parentheses validation (US3) - basic parentheses already work

### Incremental Delivery

1. **Week 1**: Phase 2 (Foundational) + Phase 3 Layout (T008-T015)
2. **Week 2**: Phase 3 Functions (T016-T040) - implement one category at a time
3. **Week 3**: Phase 4 (US2 - Memory) + Phase 5 (US3 - Parentheses)
4. **Week 4**: Phase 6 (Polish & Integration)

### Testing Strategy

Per constitution testing policy (lines 111-117):
- **Unit tests required** for parsing/validation functions (these could cause user issues):
  - `transformExpression()` - transforms calculator syntax to JavaScript Math functions (T061)
    - Test: degrees-to-radians conversion (sin/cos/tan)
    - Test: radians-to-degrees conversion (asin/acos/atan)
    - Test: π constant replacement
    - Test: sqrt/pow/cbrt pattern matching
    - Test: nth root pattern transformation
    - Focus: Happy path and known failure modes
  - `validateExpression()` - validates expressions before evaluation (T062, T051)
    - Test: division by zero detection
    - Test: invalid arcsin/acos range [-1, 1]
    - Test: mismatched parentheses (T051)
    - Test: nested parentheses validation (T049)
    - Test: square root of negative numbers
    - Test: nth root of negative with even root
    - Focus: Happy path and known failure modes
  - **Parentheses evaluation tests** (T049, T050):
    - Test nested parentheses: "2 * ((3 + 4) * 2)" = 28 (T049)
    - Test parentheses with advanced functions: "sin(30) + (5 * 2)" (T050)
    - These tests verify transformExpression() handles parentheses correctly with nested structures and function calls
- **Extraction tasks** (T059-T060, T063):
  - Extract logic functions to separate module for testability
  - Maintain backward compatibility with existing HTML template
- **Manual testing** per quickstart.md for integration:
  - Test each function category independently
  - Test error cases
  - Test multi-step input flows
  - Test memory operations
  - Test parentheses with advanced functions
- **No tests needed** for:
  - UI button handlers (UI components - excluded per constitution)
  - State management functions (simple variable updates)
  - API endpoints (excluded per constitution - test underlying logic instead)
  - Functions that depend on LLM (none in calculator)

## Success Criteria Verification

After implementation, verify:
- **SC-001**: sin(30°) = 0.5, arcsin(0.5) = 30° (4 decimal places accuracy)
- **SC-002**: All calculations complete in < 5 seconds
- **SC-003**: Memory functions work 100% of the time
- **SC-004**: Nested parentheses (3 levels) work correctly
- **SC-005**: All error cases show "Maths Error"
- **SC-006**: Calculator history logs all operations
- **SC-007**: π, ×10^x, +/- work successfully (95% success rate)
- **SC-008**: Interface responsive (< 1 second for results)

---

## Summary

**Total Tasks**: 67
- Phase 1 (Setup): 2 tasks
- Phase 2 (Foundational): 5 tasks
- Phase 3 (US1 - Scientific Functions): 33 tasks
- Phase 4 (US2 - Memory Functions): 6 tasks
- Phase 5 (US3 - Parentheses): 5 tasks
- Phase 6 (Polish): 16 tasks (5 unit test tasks + 11 polish/integration tasks)

**MVP Tasks**: 40 (Phase 2 + Phase 3)

**Test Tasks**: 5 unit test tasks (T059-T063) for critical parsing/validation functions per constitution testing policy:
- Extract logic functions for testability (T059-T060)
- Unit tests for transformExpression() and validateExpression() (T061-T062)
- Integration of extracted functions (T063)
- Note: Tests focus on happy path and known failure modes, not exhaustive edge case coverage

**Parallel Opportunities**: Multiple tasks within each phase can be done in parallel (marked with [P] where applicable, though most calculator tasks are sequential due to shared state)

**Estimated Complexity**: Moderate - extends existing calculator with ~15-20 new button handlers and enhanced evaluation logic

