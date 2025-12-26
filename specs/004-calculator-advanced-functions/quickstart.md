# Quickstart: Testing Advanced Calculator Functions

**Feature**: Advanced Calculator Functions  
**Date**: 2025-01-27

This guide shows how to verify that advanced calculator functions are working correctly after implementation.

## Prerequisites

- Bloom tutor app running locally
- A tutoring session started on a numerical problem (calculator should be visible)
- Basic calculator functions working (numbers, +, -, *, /, =)

## Testing Checklist

### 1. Basic Trigonometric Functions

**Test sin(30)**:
1. Press "sin" button
2. Press "3", "0"
3. Press ")" (if needed)
4. Press "="
5. **Expected**: Display shows `0.5` (sin(30°) = 0.5)

**Test cos(60)**:
1. Press "cos" button
2. Press "6", "0"
3. Press ")" (if needed)
4. Press "="
5. **Expected**: Display shows `0.5` (cos(60°) = 0.5)

**Test tan(45)**:
1. Press "tan" button
2. Press "4", "5"
3. Press ")" (if needed)
4. Press "="
5. **Expected**: Display shows `1` (tan(45°) = 1)

### 2. SHIFT Button and Inverse Functions

**Test arcsin(0.5)**:
1. Press "SHIFT" button (sin button should change to "arcsin")
2. Press "arcsin" button (or "sin" if label changed)
3. Press "0", ".", "5"
4. Press ")" (if needed)
5. Press "="
6. **Expected**: Display shows `30` (arcsin(0.5) = 30°)
7. **Verify**: SHIFT mode should reset after function use (or remain active, depending on implementation)

**Test arccos(0.5)**:
1. Press "SHIFT" (if not already active)
2. Press "arccos" button
3. Press "0", ".", "5"
4. Press ")" (if needed)
5. Press "="
6. **Expected**: Display shows `60` (arccos(0.5) = 60°)

### 3. Powers and Roots

**Test x² (square)**:
1. Press "2"
2. Press "x²" button
3. **Expected**: Display shows `4` (2² = 4)

**Test x^y (power)**:
1. Press "x^y" button
2. Enter base: "2"
3. Enter exponent: "3"
4. **Expected**: Display shows `8` (2³ = 8)

**Test √ (square root)**:
1. Press "√" button (or "sqrt")
2. Press "1", "6"
3. Press ")" (if needed)
4. Press "="
5. **Expected**: Display shows `4` (√16 = 4)

**Test ∛ (cube root)**:
1. Press "∛" button (if available, or use nth root)
2. Press "8"
3. Press ")" (if needed)
4. Press "="
5. **Expected**: Display shows `2` (∛8 = 2)

**Test nth root (5th root of 32)**:
1. Press "ⁿ√" button (or equivalent)
2. Enter root value: "5"
3. Enter radicand: "32"
4. **Expected**: Display shows `2` (5th root of 32 = 2)

### 4. Scientific Notation

**Test ×10^x (2.5 × 10³)**:
1. Press "×10^x" button (or "x10^x")
2. Enter coefficient: "2", ".", "5"
3. Enter exponent: "3"
4. **Expected**: Display shows `2500` (2.5 × 10³ = 2500)

### 5. Memory Functions

**Test M+ (Memory Add)**:
1. Calculate "15 * 16" = 240
2. Press "M+" button
3. **Verify**: Memory should store 240 (no visual feedback needed)

**Test MR (Memory Recall)**:
1. After M+ above, calculate "10 + 5" = 15
2. Press "MR" button
3. **Expected**: Display shows `240` (or appends 240 to expression)
4. Press "+", "10", "="
5. **Expected**: Result is 250 (240 + 10)

**Test MC (Memory Clear)**:
1. After using memory above
2. Press "MC" button
3. Press "MR" button
4. **Expected**: Display shows `0` or empty (memory cleared)

**Test Memory Accumulation**:
1. Calculate "10" and press "M+"
2. Calculate "20" and press "M+"
3. Press "MR"
4. **Expected**: Display shows `30` (10 + 20 = 30, memory accumulates)

### 6. Utility Functions

**Test π (pi constant)**:
1. Press "π" button (or "Pi")
2. **Expected**: Display shows `3.14159...` (or π inserted into expression)
3. Press "*", "2", "="
4. **Expected**: Result is approximately `6.28318...` (2π)

**Test 1/x (reciprocal)**:
1. Press "4"
2. Press "1/x" button
3. **Expected**: Display shows `0.25` (1/4 = 0.25)

**Test +/- (sign change)**:
1. Press "5"
2. Press "+/-" button
3. **Expected**: Display shows `-5`
4. Press "+/-" again
5. **Expected**: Display shows `5` (toggles back)

**Test Ans (previous answer)**:
1. Calculate "2 + 3" = 5
2. Press "Ans" button
3. **Expected**: `5` inserted into expression
4. Press "*", "2", "="
5. **Expected**: Result is `10` (5 * 2)

### 7. Error Handling

**Test Division by Zero**:
1. Press "5", "/", "0", "="
2. **Expected**: Display shows `Maths Error`

**Test Square Root of Negative**:
1. Press "√" button
2. Press "-", "4"
3. Press ")" (if needed)
4. Press "="
5. **Expected**: Display shows `Maths Error`

**Test arcsin with Invalid Input**:
1. Press "SHIFT" (if needed)
2. Press "arcsin" button
3. Press "2" (outside valid range [-1, 1])
4. Press ")" (if needed)
5. Press "="
6. **Expected**: Display shows `Maths Error`

**Test Memory Operations on Error**:
1. Create error state (e.g., sqrt(-4))
2. **Verify**: M+, MC, MR buttons should be disabled or non-functional
3. Press "AC" to clear error
4. **Verify**: Memory buttons should work again

### 8. Complex Expressions

**Test Mixed Functions**:
1. Enter: "sin(30) + 5 * 2"
2. Press "="
3. **Expected**: Result is `15` (0.5 + 10 = 15.5, or order of operations applied)

**Test Nested Functions**:
1. Enter: "sin(cos(60))"
2. Press "="
3. **Expected**: Valid result (sin(cos(60°)))

**Test Parentheses**:
1. Enter: "2 * (3 + 4)"
2. Press "="
3. **Expected**: Result is `14` (not 10 - parentheses respected)

**Test Nested Parentheses**:
1. Enter: "2 * ((3 + 4) * 2)"
2. Press "="
3. **Expected**: Result is `28` (2 * (7 * 2) = 28)

### 9. Layout Verification

**Verify Button Grid**:
- Check that calculator has 5 columns × 7 rows
- Verify all buttons from layout specification are present:
  - Row 1: SHIFT, Pi, MC, MR, M+
  - Row 2: sin, cos, tan, (, )
  - Row 3: x², x^y, sqrt, AC, DEL
  - Row 4: 7, 8, 9, 1/x, /
  - Row 5: 4, 5, 6, ×10^x, *
  - Row 6: 1, 2, 3, +/-, -
  - Row 7: 0, ., Ans, =, +

**Verify Button Styling**:
- Buttons should be visually distinct (numbers vs operators vs functions)
- SHIFT button should show active state when pressed
- Error state should be visually clear

### 10. Calculator History Logging

**Verify History Logging** (if endpoint exists):
1. Perform several calculations with advanced functions
2. Check database `calculator_history` table
3. **Expected**: All calculations logged with expression and result
4. **Verify**: Function names visible in expression text (e.g., "sin(30) + 5")

## Success Criteria Verification

- **SC-001**: Trigonometric functions accurate to 4 decimal places ✓
- **SC-002**: Calculations complete in under 5 seconds ✓
- **SC-003**: Memory functions work correctly ✓
- **SC-004**: Nested parentheses (3 levels) work correctly ✓
- **SC-005**: Error messages display "Maths Error" ✓
- **SC-006**: All operations logged to history ✓
- **SC-007**: π, ×10^x, +/- work successfully ✓
- **SC-008**: Interface responsive (< 1 second) ✓

## Troubleshooting

**Issue**: Functions not evaluating correctly
- Check that degrees are converted to radians for Math functions
- Verify expression transformation (function names → Math.*)

**Issue**: Multi-step operations not working
- Check input state machine (waiting_base, waiting_exponent, etc.)
- Verify pendingOperation and pendingValue variables

**Issue**: Memory not persisting
- Verify calculatorMemory variable scope (not reset on button press)
- Check that M+ actually updates calculatorMemory

**Issue**: Error messages not showing
- Check validation function (pre-evaluation checks)
- Verify try-catch around eval() call

**Issue**: SHIFT button not working
- Verify shiftMode state variable
- Check button label update function

## Next Steps

After verifying all functions work:
1. Test with actual GCSE mathematics problems
2. Verify calculator appears/hides correctly based on question type
3. Check that tutor can see calculator history in feedback
4. Perform manual smoke test of full tutoring session with calculator

