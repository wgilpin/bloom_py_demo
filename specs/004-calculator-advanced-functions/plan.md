# Implementation Plan: Advanced Calculator Functions

**Branch**: `004-calculator-advanced-functions` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-calculator-advanced-functions/spec.md`

## Summary

This feature extends the existing basic calculator in the Bloom tutor app with advanced scientific and trigonometric functions required for GCSE mathematics. The calculator will support trigonometric functions (sin, cos, tan and their inverses), powers (x², xʸ), roots (√, ∛, nth root), scientific notation (×10ˣ), memory functions (M+, MC, MR), and additional utilities (π constant, 1/x, +/- sign change, parentheses).

**Technical Approach**: Extend the existing calculator implementation in `bloom/templates/chat.html` and `bloom/static/js/calculator.js` (or equivalent) with new button handlers and evaluation logic. The calculator uses a 5-column × 7-row grid layout as specified. All advanced functions integrate with existing calculator history logging. No new database tables required—calculator memory persists in JavaScript session state.

**Layout Specification** (5 columns, 7 rows):
```
Row 1: ["SHIFT", "Pi", "MC", "MR", "M+"]
Row 2: ["sin", "cos", "tan", "(", ")"]
Row 3: ["x^2", "x^y", "sqrt", "AC", "DEL"]
Row 4: ["7", "8", "9", "1/x", "/"]
Row 5: ["4", "5", "6", "x10^x", "*"]
Row 6: ["1", "2", "3", "+/-", "-"]
Row 7: ["0", ".", "Ans", "=", "+"]
```

**Note**: Layout includes SHIFT button (for accessing inverse trigonometric functions) and Ans button (for previous answer) which are not explicitly in spec but are standard calculator features that enhance usability.

## Technical Context

**Language/Version**: Python 3.13+ (existing project)
**Primary Dependencies**: 
- Existing: FastAPI, htmx, Tailwind CSS, JavaScript (vanilla)
- New: None (uses Python's `math` module for trigonometric functions)

**Storage**: JavaScript session state (calculator memory), SQLite database (calculator history logging via existing endpoint)
**Testing**: pytest (optional, per constitution - only for repeatedly broken logic)
**Target Platform**: Web application (existing)
**Project Type**: Enhancement to existing web application
**Performance Goals**: 
- Calculation results appear within 1 second (SC-008)
- Complete calculation with advanced function in under 5 seconds (SC-002)
**Constraints**: 
- Must integrate seamlessly with existing calculator visibility logic
- Calculator memory persists only during active session (no database storage)
- All functions must work with existing expression evaluation system
- Error messages must display "Maths Error" for invalid inputs (FR-019)
**Scale/Scope**: 
- Single calculator instance per tutoring session
- Calculator memory: single numeric value (accumulative)
- Expression complexity: up to 3 levels of nested parentheses (SC-004)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Simplicity First ✓
- **Architecture**: Extends existing calculator implementation, no new architectural components
- **Dependencies**: Uses Python's built-in `math` module (stdlib), no new third-party libraries
- **No premature abstraction**: Direct JavaScript functions for button handlers, no class-based calculator state machine

### II. Minimal Boilerplate ✓
- **Reuses existing calculator code**: Extends `calcAppend()`, `calcEvaluate()` functions
- **No new configuration**: Calculator layout defined in HTML template
- **Direct approach**: JavaScript functions for each button type, no abstraction layers

### III. Rapid Iteration Over Perfection ✓
- **Tests optional**: Calculator logic is straightforward (expression evaluation)
- **Simple implementation**: Button click handlers → expression building → evaluation
- **No build step**: JavaScript runs directly in browser

### IV. Focused Scope ✓
- **Single purpose**: Add advanced functions to existing calculator
- **No feature bloat**: All functions directly support GCSE mathematics curriculum
- **Existing flow intact**: Calculator visibility and logging unchanged

### V. Pleasing Simplicity (UI/UX) ✓
- **Grid layout**: Clean 5×7 button grid, familiar calculator pattern
- **Consistent styling**: Uses existing Tailwind CSS classes
- **Responsive**: Calculator fits within existing chat interface

### Technology Constraints Compliance ✓
- ✓ Uses existing Python 3.13+
- ✓ Uses existing FastAPI/htmx/Tailwind stack
- ✓ No new dependencies (Python `math` module is stdlib)
- ✓ JavaScript evaluation (existing pattern, with input sanitization)
- ✓ Follows existing calculator code patterns

### Violations Requiring Justification

None. This feature extends existing functionality without adding complexity or new dependencies.

**Gate Status**: ✅ **PASS** - Pure enhancement with no violations

## Project Structure

### Documentation (this feature)

```text
specs/004-calculator-advanced-functions/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Calculator implementation decisions
├── data-model.md        # Phase 1: Calculator state model (if needed)
├── quickstart.md        # Phase 1: Testing calculator functions
├── contracts/           # Phase 1: API endpoints (if calculator logging extended)
│   └── api.yaml         # OpenAPI spec updates
└── checklists/          # Requirements checklist (already exists)
    └── requirements.md
```

### Modified Files (repository root)

```text
bloom/
├── templates/
│   └── chat.html        # MODIFY: Update calculator button grid to 5×7 layout with new buttons
├── static/
│   └── js/
│       └── calculator.js # MODIFY: Add handlers for advanced functions, memory operations, multi-step input (x^y, nth root, ×10^x)
└── routes/
    └── student.py        # MODIFY: Update calculator logging to include advanced function usage (if needed)
```

**Note**: If `calculator.js` doesn't exist as a separate file, calculator logic may be inline in `chat.html`. Implementation will follow existing pattern.

## Complexity Tracking

**Added Complexity**:
- ~15-20 new button handlers (trigonometric, roots, powers, memory, utilities)
- Multi-step input state management (x^y, nth root, ×10^x require two inputs)
- Calculator memory state (single value, session-scoped)
- Enhanced expression evaluation (trigonometric functions, roots, scientific notation)

**Reduced Complexity**:
- Reuses existing calculator infrastructure (display, evaluation, logging)
- No new database tables or API endpoints required
- Standard JavaScript patterns (no frameworks)

**Net Complexity**: Moderate increase in JavaScript code, but well-scoped and follows existing patterns.

---

## Phase 0: Research

Research tasks completed during this phase:

### 1. Calculator Expression Evaluation Strategy

**Question**: How should we evaluate expressions containing trigonometric functions, roots, and scientific notation?

**Decision**: Extend existing `eval()`-based approach with input sanitization and function mapping

**Rationale**:
- Existing calculator uses `eval()` with sanitization (allows digits, operators, parentheses)
- Python's `math` module provides all required functions (sin, cos, tan, asin, acos, atan, sqrt, pow)
- JavaScript `Math` object provides equivalent functions
- Input sanitization must be extended to allow function names and constants
- Expression parsing can map button inputs to JavaScript Math functions

**Alternatives considered**:
- Custom expression parser: Over-engineered for demo, adds significant complexity
- Server-side evaluation: Adds latency, breaks existing client-side pattern
- Math.js library: Adds dependency, violates constitution (stdlib preferred)

**Implementation Pattern**:
```javascript
// Map calculator buttons to JavaScript Math functions
const functionMap = {
    'sin': 'Math.sin',
    'cos': 'Math.cos',
    'tan': 'Math.tan',
    'asin': 'Math.asin',
    'acos': 'Math.acos',
    'atan': 'Math.atan',
    'sqrt': 'Math.sqrt',
    'pow': 'Math.pow',
    // ... etc
};

// Sanitize and transform expression before eval
function sanitizeExpression(expr) {
    // Allow: digits, operators, parentheses, function names, constants (π, e)
    // Transform function calls: sin(30) → Math.sin(30 * Math.PI / 180) // degrees to radians
    // Transform constants: π → Math.PI
    // Then eval with restricted context
}
```

### 2. Multi-Step Input Handling (x^y, nth root, ×10^x)

**Question**: How should we handle buttons that require two inputs (base and exponent, root value and radicand, coefficient and exponent)?

**Decision**: Use input state machine with prompt display

**Rationale**:
- Standard calculator pattern: button press → enter first value → enter second value → evaluate
- Display can show prompt text (e.g., "Enter base:" → "Enter exponent:")
- State machine tracks: normal input → waiting for first value → waiting for second value
- After second value entered, construct expression and return to normal state

**Alternatives considered**:
- Modal dialogs: Breaks calculator flow, adds UI complexity
- Separate input fields: Clutters interface, not standard calculator pattern
- Postfix notation: Unfamiliar to students, adds parsing complexity

**Implementation Pattern**:
```javascript
let inputState = 'normal'; // 'normal' | 'waiting_base' | 'waiting_exponent'
let pendingOperation = null; // 'x^y' | 'nth_root' | 'scientific'

function handleXToY() {
    inputState = 'waiting_base';
    pendingOperation = 'x^y';
    displayPrompt('Enter base:');
}

function handleNumber(num) {
    if (inputState === 'waiting_base') {
        baseValue = num;
        inputState = 'waiting_exponent';
        displayPrompt('Enter exponent:');
    } else if (inputState === 'waiting_exponent') {
        exponentValue = num;
        // Construct expression: baseValue + '^' + exponentValue
        // Evaluate and return to normal state
        inputState = 'normal';
        pendingOperation = null;
    } else {
        // Normal number input
        appendToExpression(num);
    }
}
```

### 3. Calculator Memory Implementation

**Question**: How should calculator memory (M+, MC, MR) be stored and managed?

**Decision**: JavaScript variable in session scope, cleared on page reload or session end

**Rationale**:
- Memory is session-scoped per spec (FR-009: "persists until explicitly cleared or session ends")
- No database storage needed (calculator history is logged, but memory state is ephemeral)
- Simple variable: `let calculatorMemory = 0;`
- M+ adds to memory, MC clears, MR recalls

**Alternatives considered**:
- LocalStorage persistence: Not required by spec, adds complexity
- Database storage: Over-engineered for session-scoped memory
- Session storage: Adds complexity, not needed for single-session use

**Implementation Pattern**:
```javascript
let calculatorMemory = 0;

function handleMPlus() {
    if (displayValue !== 'Error') {
        calculatorMemory += parseFloat(displayValue) || 0;
    }
}

function handleMClear() {
    calculatorMemory = 0;
}

function handleMRecall() {
    if (calculatorMemory === 0) {
        displayValue = '0';
    } else {
        appendToExpression(calculatorMemory.toString());
    }
}
```

### 4. SHIFT Button for Inverse Functions

**Question**: How should the SHIFT button work to access inverse trigonometric functions (arcsin, arccos, arctan)?

**Decision**: Toggle button state that changes sin/cos/tan labels to arcsin/arccos/arctan

**Rationale**:
- Standard calculator pattern: SHIFT key toggles secondary function labels
- Visual feedback: Button labels change when SHIFT is active
- Reduces button count: 3 buttons (sin/cos/tan) serve dual purpose
- SHIFT state persists until toggled off or function used

**Alternatives considered**:
- Separate buttons for inverse functions: Increases button count, clutters interface
- Long-press gesture: Not standard, adds complexity
- Dropdown menu: Breaks calculator flow, not standard pattern

**Implementation Pattern**:
```javascript
let shiftMode = false;

function handleShift() {
    shiftMode = !shiftMode;
    updateButtonLabels(); // sin → arcsin, cos → arccos, tan → arctan
}

function handleSin() {
    if (shiftMode) {
        // Use arcsin
        evaluateFunction('asin', getCurrentValue());
        shiftMode = false; // Reset after use
    } else {
        // Use sin
        evaluateFunction('sin', getCurrentValue());
    }
}
```

### 5. Ans Button (Previous Answer)

**Question**: What should the Ans button do? (Not explicitly in spec but included in layout)

**Decision**: Insert the last calculated result into the current expression

**Rationale**:
- Standard calculator feature: Ans = Answer (previous result)
- Useful for chaining calculations: calculate 2+3=5, then Ans*2=10
- Simple implementation: store last result, insert on Ans button press
- Enhances usability without adding complexity

**Implementation Pattern**:
```javascript
let lastAnswer = 0;

function handleEquals() {
    const result = evaluateExpression(currentExpression);
    lastAnswer = result;
    displayValue = result.toString();
}

function handleAns() {
    appendToExpression(lastAnswer.toString());
}
```

### 6. Error Handling and Validation

**Question**: How should we validate expressions and handle mathematical errors?

**Decision**: Pre-evaluation validation + try-catch with "Maths Error" message

**Rationale**:
- Spec requires "Maths Error" message (FR-019)
- Validate before evaluation: check for division by zero, invalid function inputs (arcsin > 1), mismatched parentheses
- Try-catch for runtime errors (overflow, NaN, Infinity)
- Display "Maths Error" and disable memory operations (FR-008)

**Implementation Pattern**:
```javascript
function validateExpression(expr) {
    // Check for division by zero patterns
    if (expr.includes('/0') || expr.match(/\/\s*0[^.]/)) {
        return { valid: false, error: 'Maths Error' };
    }
    // Check for arcsin/acos with values outside [-1, 1]
    // Check for mismatched parentheses
    // ... etc
    return { valid: true };
}

function evaluateExpression(expr) {
    const validation = validateExpression(expr);
    if (!validation.valid) {
        return 'Maths Error';
    }
    
    try {
        // Transform and evaluate
        const result = eval(transformedExpression);
        if (!isFinite(result) || isNaN(result)) {
            return 'Maths Error';
        }
        return result;
    } catch (e) {
        return 'Maths Error';
    }
}
```

### 7. Degrees vs Radians for Trigonometry

**Question**: How should trigonometric functions handle angle units? (Spec says degrees)

**Decision**: Convert degrees to radians for JavaScript Math functions (which use radians)

**Rationale**:
- Spec requires degrees (FR-002, FR-004)
- JavaScript Math.sin/cos/tan use radians
- Convert on evaluation: sin(30°) → Math.sin(30 * Math.PI / 180)
- Inverse functions convert back: Math.asin(0.5) * 180 / Math.PI → 30°

**Implementation Pattern**:
```javascript
function evaluateTrigFunction(funcName, angleInDegrees) {
    const angleInRadians = angleInDegrees * Math.PI / 180;
    const result = Math[funcName](angleInRadians);
    return result;
}

function evaluateInverseTrigFunction(funcName, value) {
    const resultInRadians = Math[funcName](value);
    const resultInDegrees = resultInRadians * 180 / Math.PI;
    return resultInDegrees;
}
```

---

## Phase 1: Design & Contracts

### Data Model

**No new database tables required.** Calculator memory is session-scoped JavaScript state.

**Calculator State Model** (JavaScript):
- `calculatorMemory`: number (accumulative memory value, default 0)
- `lastAnswer`: number (previous calculation result, for Ans button)
- `currentExpression`: string (expression being built)
- `displayValue`: string (current display, default "0")
- `inputState`: string ('normal' | 'waiting_base' | 'waiting_exponent' | 'waiting_root' | 'waiting_coefficient')
- `pendingOperation`: string | null ('x^y' | 'nth_root' | 'scientific' | null)
- `shiftMode`: boolean (SHIFT button active state)

**Calculator History** (existing entity, extended):
- Existing `calculator_history` table already logs expressions and results
- Extended to include function names and parameters for advanced operations (FR-020)
- No schema changes needed—expression text captures all information

### API Contracts

**No new API endpoints required.** Calculator operates client-side.

**Existing Endpoint** (if calculator logging is extended):
- `POST /calculator/compute` (existing, may need updates to log advanced function usage)
  - Request: `{ "expression": "sin(30) + 5", "result": "5.5" }`
  - Response: `{ "logged": true }`
  - Extended to capture function names: `{ "expression": "sin(30) + 5", "functions_used": ["sin"], "result": "5.5" }`

**Note**: If existing calculator doesn't have logging endpoint, this feature can defer logging enhancement to later phase.

### Calculator Layout Implementation

**HTML Structure** (5 columns × 7 rows grid):
```html
<div class="grid grid-cols-5 gap-2">
    <!-- Row 1 -->
    <button onclick="handleShift()">SHIFT</button>
    <button onclick="handlePi()">π</button>
    <button onclick="handleMClear()">MC</button>
    <button onclick="handleMRecall()">MR</button>
    <button onclick="handleMPlus()">M+</button>
    
    <!-- Row 2 -->
    <button onclick="handleSin()" id="sin-btn">sin</button>
    <button onclick="handleCos()" id="cos-btn">cos</button>
    <button onclick="handleTan()" id="tan-btn">tan</button>
    <button onclick="calcAppend('(')">(</button>
    <button onclick="calcAppend(')')">)</button>
    
    <!-- Row 3 -->
    <button onclick="handleSquare()">x²</button>
    <button onclick="handleXToY()">x^y</button>
    <button onclick="handleSqrt()">√</button>
    <button onclick="calcClear()">AC</button>
    <button onclick="handleDelete()">DEL</button>
    
    <!-- Rows 4-7: Numbers, operators, etc. -->
    <!-- ... -->
</div>
```

**Button Styling**: Reuse existing `calc-btn-*` classes from current calculator implementation.

### Quickstart

See [quickstart.md](./quickstart.md) for testing instructions.

**Verification Steps**:
1. Open tutoring session with numerical problem → calculator appears
2. Test trigonometric: sin(30) → should equal 0.5
3. Test SHIFT: press SHIFT → sin button changes to arcsin → press → arcsin(0.5) → should equal 30
4. Test memory: calculate 5+3=8 → M+ → calculate 2*2=4 → MR → should show 8
5. Test multi-step: press x^y → enter 2 → enter 3 → should equal 8
6. Test error: sqrt(-4) → should show "Maths Error"
7. Test memory on error: after error, M+ should be disabled

---

## Phase 1 Design Artifacts: Constitution Re-Check

**Post-Design Evaluation** (after data model, contracts, and research complete):

### Architecture Review ✓

**Implementation Pattern**:
- ✓ Extends existing calculator code (no new architecture)
- ✓ JavaScript functions for button handlers (no classes)
- ✓ Session-scoped state (no database storage)
- ✓ Reuses existing evaluation infrastructure

**Layout Design**:
- ✓ 5×7 grid layout as specified
- ✓ Standard calculator button arrangement
- ✓ SHIFT button for inverse functions (reduces button count)
- ✓ Ans button for previous answer (standard feature)

### Principles Compliance ✓

**I. Simplicity First**:
- ✓ No new dependencies (Python `math` module is stdlib, JavaScript `Math` is built-in)
- ✓ Direct JavaScript functions (no abstraction layers)
- ✓ Extends existing code patterns

**II. Minimal Boilerplate**:
- ✓ Reuses existing calculator infrastructure
- ✓ Button handlers are simple functions
- ✓ No configuration files

**III. Rapid Iteration Over Perfection**:
- ✓ Tests optional (calculator logic is straightforward)
- ✓ Manual testing sufficient for demo
- ✓ No build step required

**IV. Focused Scope**:
- ✓ All functions directly support GCSE mathematics
- ✓ No feature bloat (SHIFT and Ans are standard calculator features)
- ✓ Existing calculator flow unchanged

**V. Pleasing Simplicity (UI/UX)**:
- ✓ Clean 5×7 grid layout
- ✓ Familiar calculator pattern
- ✓ Responsive within existing interface

### Constitution Violations: None ✅

All design decisions align with constitution principles. Implementation extends existing functionality without adding complexity.

---

## Final Gate Status: ✅ APPROVED FOR IMPLEMENTATION

**Summary**:
- ✓ Extends existing calculator with advanced functions
- ✓ 5×7 button grid layout as specified
- ✓ JavaScript implementation (no new dependencies)
- ✓ Session-scoped memory (no database changes)
- ✓ All GCSE-level mathematics functions supported
- ✓ Error handling with "Maths Error" messages
- ✓ SHIFT button for inverse functions
- ✓ Ans button for previous answer

Ready to proceed to `/speckit.tasks` for task breakdown.
