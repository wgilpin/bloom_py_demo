# Data Model: Advanced Calculator Functions

**Feature**: Advanced Calculator Functions  
**Date**: 2025-01-27  
**Phase**: Phase 1 - Design & Contracts

## Overview

This feature extends the existing calculator with advanced functions. **No new database tables are required.** Calculator memory is session-scoped JavaScript state. Calculator history logging uses the existing `calculator_history` table.

## Calculator State Model (JavaScript)

The calculator maintains state in JavaScript variables during the active session:

### State Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `calculatorMemory` | number | 0 | Accumulative memory value (M+ adds to this, MC clears, MR recalls) |
| `lastAnswer` | number | 0 | Previous calculation result (used by Ans button) |
| `currentExpression` | string | "" | Expression being built from button presses |
| `displayValue` | string | "0" | Current display value (shown in calculator display) |
| `inputState` | string | "normal" | Current input state: "normal" \| "waiting_base" \| "waiting_exponent" \| "waiting_root" \| "waiting_radicand" \| "waiting_coefficient" |
| `pendingOperation` | string \| null | null | Pending multi-step operation: "x^y" \| "nth_root" \| "scientific" \| null |
| `pendingValue` | number \| null | null | First value entered in multi-step operation (base, root value, or coefficient) |
| `shiftMode` | boolean | false | SHIFT button active state (toggles sin/cos/tan to arcsin/arccos/arctan) |

### State Transitions

**Normal Input Flow**:
1. User presses number/operator → `currentExpression` updated → `displayValue` shows expression
2. User presses function (sin, sqrt, etc.) → function applied to current value → `displayValue` updated
3. User presses = → expression evaluated → `displayValue` = result, `lastAnswer` = result

**Multi-Step Input Flow** (x^y, nth root, ×10^x):
1. User presses x^y → `inputState` = "waiting_base", `pendingOperation` = "x^y"
2. User enters base → `pendingValue` = base, `inputState` = "waiting_exponent"
3. User enters exponent → expression constructed, evaluated → `inputState` = "normal", `pendingOperation` = null

**Memory Operations**:
- M+: `calculatorMemory += parseFloat(displayValue)` (if not error state)
- MC: `calculatorMemory = 0`
- MR: `currentExpression += calculatorMemory.toString()`

**SHIFT Mode**:
- SHIFT pressed: `shiftMode = !shiftMode`, button labels updated
- Function used: if `shiftMode`, use inverse function, then `shiftMode = false` (optional)

### State Persistence

- **Session-scoped**: All state variables reset on page reload or new session
- **No database storage**: Memory state is ephemeral (per FR-009: "persists until explicitly cleared or session ends")
- **Calculator history**: Expression and result logged to database (existing `calculator_history` table)

## Calculator History (Existing Entity, Extended)

**Table**: `calculator_history` (existing)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Auto-increment ID |
| `session_id` | INTEGER | Foreign key to sessions table |
| `expression` | TEXT | Mathematical expression entered |
| `result` | TEXT | Calculated result |
| `timestamp` | TEXT | ISO8601 timestamp |

**Extension for Advanced Functions** (optional enhancement):
- Expression text already captures function usage (e.g., "sin(30) + 5")
- If enhanced logging desired, could add `functions_used` JSON column: `["sin"]`
- For demo, expression text is sufficient (FR-020: "log all calculator operations")

**Example Records**:
```sql
INSERT INTO calculator_history (session_id, expression, result, timestamp) VALUES
(1, 'sin(30)', '0.5', '2025-01-27T10:15:00'),
(1, '2^3', '8', '2025-01-27T10:15:30'),
(1, 'sqrt(16)', '4', '2025-01-27T10:16:00');
```

## Validation Rules

### Expression Validation

1. **Division by zero**: Reject expressions containing `/0` or `/ 0` (not `/0.5`)
2. **Invalid trigonometric inputs**: 
   - arcsin/acos: input must be in range [-1, 1]
   - tan: input must not be 90° + n×180° (undefined)
3. **Square root of negative**: Reject (display "Maths Error")
4. **Nth root of negative with even root**: Reject (display "Maths Error")
5. **Mismatched parentheses**: Count opening vs closing, reject if unequal
6. **Invalid function syntax**: Functions must have parentheses (sin(30), not sin30)

### Memory Operation Validation

1. **Error state**: Memory operations (M+, MC, MR) disabled when `displayValue === "Maths Error"`
2. **Empty memory**: MR returns "0" or empty when `calculatorMemory === 0`
3. **Accumulation**: M+ always adds to existing memory (never replaces)

### Input State Validation

1. **Multi-step operations**: Must complete both inputs (base+exponent, root+radicand, coefficient+exponent)
2. **State reset**: If user presses AC (clear) during multi-step input, reset to "normal" state
3. **Invalid transitions**: Cannot start new multi-step operation while another is pending

## Data Flow

### Calculation Flow

```
User Input → Button Handler → State Update → Expression Building → Validation → Evaluation → Display Update → History Logging
```

### Example: sin(30) + 5

1. User presses "sin" → `currentExpression = "sin("`
2. User presses "3", "0" → `currentExpression = "sin(30"`
3. User presses ")" → `currentExpression = "sin(30)"`
4. User presses "+" → evaluate sin(30) → `currentExpression = "0.5 +"`
5. User presses "5" → `currentExpression = "0.5 + 5"`
6. User presses "=" → evaluate → `displayValue = "5.5"`, `lastAnswer = 5.5`
7. Log to database: `expression="sin(30) + 5"`, `result="5.5"`

### Example: Memory Operations

1. User calculates "15 * 16" = 240
2. User presses M+ → `calculatorMemory = 240`
3. User calculates "10 + 5" = 15
4. User presses MR → `currentExpression = "15 + 240"` (or append "240")
5. User presses = → result = 255

## No Database Schema Changes Required

This feature requires **no database schema changes**. Calculator state is JavaScript session-scoped, and calculator history uses the existing `calculator_history` table with expression text capturing all function usage.

