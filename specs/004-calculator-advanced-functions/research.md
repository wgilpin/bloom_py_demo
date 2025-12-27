# Research: Advanced Calculator Functions

**Feature**: Advanced Calculator Functions  
**Date**: 2025-01-27  
**Phase**: Phase 0 - Outline & Research

## Research Decisions

### 1. Calculator Expression Evaluation Strategy

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
    'cbrt': 'Math.cbrt', // Cube root (ES6)
};

// Sanitize and transform expression before eval
function sanitizeExpression(expr) {
    // Allow: digits, operators, parentheses, function names, constants (π, e)
    // Transform function calls: sin(30) → Math.sin(30 * Math.PI / 180) // degrees to radians
    // Transform constants: π → Math.PI
    // Then eval with restricted context
}
```

---

### 2. Multi-Step Input Handling (x^y, nth root, ×10^x)

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
let pendingValue = null; // Store first value while waiting for second

function handleXToY() {
    inputState = 'waiting_base';
    pendingOperation = 'x^y';
    displayPrompt('Enter base:');
}

function handleNumber(num) {
    if (inputState === 'waiting_base') {
        pendingValue = num;
        inputState = 'waiting_exponent';
        displayPrompt('Enter exponent:');
    } else if (inputState === 'waiting_exponent') {
        // Construct expression: pendingValue + '^' + num
        const expr = `${pendingValue}^${num}`;
        evaluateAndDisplay(expr);
        // Return to normal state
        inputState = 'normal';
        pendingOperation = null;
        pendingValue = null;
    } else {
        // Normal number input
        appendToExpression(num);
    }
}
```

---

### 3. Calculator Memory Implementation

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
    if (displayValue !== 'Error' && displayValue !== 'Maths Error') {
        const currentValue = parseFloat(displayValue) || 0;
        calculatorMemory += currentValue;
    }
}

function handleMClear() {
    calculatorMemory = 0;
}

function handleMRecall() {
    if (calculatorMemory === 0) {
        appendToExpression('0');
    } else {
        appendToExpression(calculatorMemory.toString());
    }
}
```

---

### 4. SHIFT Button for Inverse Functions

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
    // Visual feedback: highlight SHIFT button when active
    const shiftBtn = document.getElementById('shift-btn');
    shiftBtn.classList.toggle('active', shiftMode);
}

function handleSin() {
    if (shiftMode) {
        // Use arcsin
        evaluateFunction('asin', getCurrentValue());
        shiftMode = false; // Reset after use (optional - could persist)
        updateButtonLabels();
    } else {
        // Use sin
        evaluateFunction('sin', getCurrentValue());
    }
}

function updateButtonLabels() {
    document.getElementById('sin-btn').textContent = shiftMode ? 'arcsin' : 'sin';
    document.getElementById('cos-btn').textContent = shiftMode ? 'arccos' : 'cos';
    document.getElementById('tan-btn').textContent = shiftMode ? 'arctan' : 'tan';
}
```

---

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
    currentExpression = result.toString(); // Reset expression to result
}

function handleAns() {
    appendToExpression(lastAnswer.toString());
}
```

---

### 6. Error Handling and Validation

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
    const arcsinMatches = expr.match(/asin\(([^)]+)\)/g);
    if (arcsinMatches) {
        for (const match of arcsinMatches) {
            const value = parseFloat(match.match(/asin\(([^)]+)\)/)[1]);
            if (value < -1 || value > 1) {
                return { valid: false, error: 'Maths Error' };
            }
        }
    }
    
    // Check for mismatched parentheses
    const openParens = (expr.match(/\(/g) || []).length;
    const closeParens = (expr.match(/\)/g) || []).length;
    if (openParens !== closeParens) {
        return { valid: false, error: 'Maths Error' };
    }
    
    return { valid: true };
}

function evaluateExpression(expr) {
    const validation = validateExpression(expr);
    if (!validation.valid) {
        return 'Maths Error';
    }
    
    try {
        // Transform expression (degrees to radians, function names, constants)
        const transformed = transformExpression(expr);
        const result = eval(transformed);
        
        if (!isFinite(result) || isNaN(result)) {
            return 'Maths Error';
        }
        return result;
    } catch (e) {
        return 'Maths Error';
    }
}

function setErrorState(isError) {
    displayValue = isError ? 'Maths Error' : displayValue;
    // Disable memory buttons when error
    const memoryButtons = ['mplus-btn', 'mclear-btn', 'mrecall-btn'];
    memoryButtons.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = isError;
    });
}
```

---

### 7. Degrees vs Radians for Trigonometry

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
    // Validate input range for arcsin/acos
    if ((funcName === 'asin' || funcName === 'acos') && (value < -1 || value > 1)) {
        return 'Maths Error';
    }
    
    const resultInRadians = Math[funcName](value);
    const resultInDegrees = resultInRadians * 180 / Math.PI;
    return resultInDegrees;
}

function transformExpression(expr) {
    // Replace sin(30) with Math.sin(30 * Math.PI / 180)
    expr = expr.replace(/sin\(([^)]+)\)/g, 'Math.sin(($1) * Math.PI / 180)');
    expr = expr.replace(/cos\(([^)]+)\)/g, 'Math.cos(($1) * Math.PI / 180)');
    expr = expr.replace(/tan\(([^)]+)\)/g, 'Math.tan(($1) * Math.PI / 180)');
    
    // Replace asin(0.5) with Math.asin(0.5) * 180 / Math.PI
    expr = expr.replace(/asin\(([^)]+)\)/g, '(Math.asin($1) * 180 / Math.PI)');
    expr = expr.replace(/acos\(([^)]+)\)/g, '(Math.acos($1) * 180 / Math.PI)');
    expr = expr.replace(/atan\(([^)]+)\)/g, '(Math.atan($1) * 180 / Math.PI)');
    
    // Replace π with Math.PI
    expr = expr.replace(/π/g, 'Math.PI');
    
    // Replace sqrt with Math.sqrt
    expr = expr.replace(/sqrt\(([^)]+)\)/g, 'Math.sqrt($1)');
    
    // Replace x^y with Math.pow(x, y)
    expr = expr.replace(/([0-9.]+)\^([0-9.]+)/g, 'Math.pow($1, $2)');
    
    return expr;
}
```

---

### 8. Cube Root and Nth Root Implementation

**Decision**: Use Math.cbrt() for cube root, Math.pow(x, 1/n) for nth root

**Rationale**:
- Math.cbrt() is ES6 standard (cube root)
- Nth root: x^(1/n) = Math.pow(x, 1/n)
- Multi-step input for nth root: enter root value (n), then radicand (x)

**Implementation Pattern**:
```javascript
function handleCubeRoot() {
    const value = parseFloat(displayValue) || 0;
    if (value < 0) {
        displayValue = 'Maths Error';
        return;
    }
    const result = Math.cbrt(value);
    displayValue = result.toString();
}

function handleNthRoot() {
    inputState = 'waiting_root';
    pendingOperation = 'nth_root';
    displayPrompt('Enter root value:');
}

// In number handler:
if (inputState === 'waiting_root') {
    pendingValue = parseFloat(num); // Root value (n)
    inputState = 'waiting_radicand';
    displayPrompt('Enter radicand:');
} else if (inputState === 'waiting_radicand') {
    const radicand = parseFloat(num);
    if (radicand < 0 && pendingValue % 2 === 0) {
        // Even root of negative number
        displayValue = 'Maths Error';
    } else {
        const result = Math.pow(radicand, 1 / pendingValue);
        displayValue = result.toString();
    }
    inputState = 'normal';
    pendingOperation = null;
    pendingValue = null;
}
```

---

### 9. Scientific Notation (×10^x) Implementation

**Decision**: Multi-step input: coefficient first, then exponent

**Rationale**:
- Matches x^y and nth root pattern (consistency)
- Standard scientific notation: coefficient × 10^exponent
- Display result in standard format or decimal as appropriate

**Implementation Pattern**:
```javascript
function handleScientificNotation() {
    inputState = 'waiting_coefficient';
    pendingOperation = 'scientific';
    displayPrompt('Enter coefficient:');
}

// In number handler:
if (inputState === 'waiting_coefficient') {
    pendingValue = parseFloat(num); // Coefficient
    inputState = 'waiting_exponent';
    displayPrompt('Enter exponent:');
} else if (inputState === 'waiting_exponent' && pendingOperation === 'scientific') {
    const exponent = parseFloat(num);
    const result = pendingValue * Math.pow(10, exponent);
    displayValue = result.toString();
    inputState = 'normal';
    pendingOperation = null;
    pendingValue = null;
}
```

---

## Key Takeaways

1. **Expression Evaluation**: Extend existing eval() pattern with sanitization and transformation
2. **Multi-Step Input**: State machine pattern for x^y, nth root, ×10^x
3. **Memory**: Simple JavaScript variable, session-scoped
4. **SHIFT Button**: Toggle labels for inverse functions
5. **Degrees Conversion**: Convert degrees to radians for Math functions, back for inverse
6. **Error Handling**: Pre-validation + try-catch, "Maths Error" message
7. **Ans Button**: Store last result, insert on button press

All decisions prioritize simplicity and align with constitution principles. No new dependencies required.



