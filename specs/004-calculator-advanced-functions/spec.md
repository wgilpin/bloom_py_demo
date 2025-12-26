# Feature Specification: Advanced Calculator Functions

**Feature Branch**: `004-calculator-advanced-functions`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "the calculator needs additional functions: sin, cos, tan, inverses for each too. 1/x, x^2, x^y, M+, MC, MR, $\pi$, $\sqrt{}$, $\sqrt[3]{}$ (or $\sqrt[y]{x}$), $( )$, $\times 10^x$, $+/-$."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scientific and Trigonometric Functions (Priority: P1)

A student working on GCSE mathematics problems that involve trigonometry, powers, roots, or scientific notation can use advanced calculator functions to perform these calculations directly in the integrated calculator.

**Why this priority**: GCSE mathematics curriculum includes trigonometry, powers, roots, and scientific notation. Students need these functions to solve problems without switching to external tools. This extends the basic calculator to support the full range of GCSE-level calculations.

**Independent Test**: Open a tutoring session on a trigonometry subtopic (e.g., "Sine and Cosine"), verify the calculator displays trigonometric function buttons (sin, cos, tan), use sin(30) to calculate a value, verify the result is correct, and confirm the calculation is logged for the tutor to see.

**Acceptance Scenarios**:

1. **Given** the calculator is visible during a tutoring session, **When** the student views the calculator interface, **Then** buttons for trigonometric functions (sin, cos, tan) are available
2. **Given** the calculator displays trigonometric functions, **When** the student enters an expression like "sin(30)", **Then** the calculator evaluates the trigonometric function and displays the result
3. **Given** the calculator is visible, **When** the student needs to calculate an inverse trigonometric value (e.g., arcsin(0.5)), **Then** inverse trigonometric function buttons (arcsin, arccos, arctan) are available and produce correct results
4. **Given** the student is working on a problem requiring powers, **When** they use the x^2 or x^y buttons, **Then** the calculator correctly evaluates squared values and arbitrary powers
5. **Given** the student needs to calculate roots, **When** they use the square root (√) or cube root (∛) buttons, **Then** the calculator correctly evaluates these operations
6. **Given** the student needs the nth root, **When** they press the "ⁿ√" button and enter the root value (n) followed by the radicand (x), **Then** the calculator evaluates the nth root correctly (e.g., 5th root of 32 = 2)
7. **Given** the student is working with scientific notation, **When** they press the "×10^x" button and enter the coefficient followed by the exponent, **Then** the calculator correctly formats and evaluates numbers in scientific notation (e.g., 2.5×10³ = 2500)
8. **Given** the student needs to use the mathematical constant π, **When** they press the π button, **Then** the calculator inserts the value of π (approximately 3.14159...) into the expression
9. **Given** the student needs to calculate a reciprocal, **When** they use the 1/x button, **Then** the calculator correctly computes the reciprocal of the current value or entered number
10. **Given** the student needs to change the sign of a number, **When** they use the +/- button, **Then** the calculator toggles the sign of the current display value (positive ↔ negative)

---

### User Story 2 - Memory Functions (Priority: P2)

A student working on multi-step calculations can store intermediate results in calculator memory, recall them later, and clear memory when needed.

**Why this priority**: GCSE problems often require multiple calculation steps. Memory functions allow students to store intermediate values (e.g., a percentage result) and use them in subsequent calculations without re-entering numbers. This improves efficiency and reduces errors.

**Independent Test**: During a tutoring session, calculate a value (e.g., 15% of 240 = 36), press M+ to store it, perform another calculation, press MR to recall the stored value, use it in a new calculation, and verify the result is correct. Press MC to clear memory and verify MR returns zero or empty.

**Acceptance Scenarios**:

1. **Given** the calculator is visible and the student has calculated a value, **When** they press the M+ button, **Then** the current display value is added to memory (or stored if memory is empty)
2. **Given** a value has been stored in memory, **When** the student presses the MR (Memory Recall) button, **Then** the stored value is displayed and can be used in calculations
3. **Given** memory contains a value, **When** the student presses MC (Memory Clear), **Then** the memory is cleared and MR returns zero or empty
4. **Given** memory contains a value, **When** the student presses M+ with a new value, **Then** the new value is added to the existing memory value (accumulative memory)
5. **Given** the student recalls a memory value, **When** they use it in a calculation (e.g., MR + 10), **Then** the calculator correctly performs the operation with the recalled value

---

### User Story 3 - Expression Grouping and Parentheses (Priority: P2)

A student working on complex expressions can use parentheses to group operations and ensure correct order of operations.

**Why this priority**: GCSE mathematics requires understanding order of operations. Parentheses allow students to explicitly control calculation order, which is essential for multi-step problems. This supports the existing calculator's ability to handle complex expressions.

**Independent Test**: Enter an expression like "2 × (3 + 4)" using the parentheses buttons, verify the calculator evaluates the grouped expression correctly (result: 14), and confirm it handles nested parentheses like "2 × ((3 + 4) × 2)".

**Acceptance Scenarios**:

1. **Given** the calculator is visible, **When** the student uses opening and closing parentheses buttons, **Then** the calculator displays parentheses in the expression
2. **Given** an expression contains parentheses, **When** the student evaluates it, **Then** the calculator respects order of operations and evaluates grouped expressions first
3. **Given** the student enters nested parentheses, **When** they evaluate the expression, **Then** the calculator correctly handles multiple levels of nesting
4. **Given** the student enters mismatched parentheses (more opening than closing or vice versa), **When** they attempt to evaluate, **Then** the calculator displays an error message indicating the parentheses mismatch

---

### Edge Cases

- What happens when a student enters an invalid trigonometric input (e.g., arcsin(2) which is outside the valid range [-1, 1])? System displays a clear error message indicating the input is out of range
- How does the calculator handle square root of a negative number? System displays "Maths Error" message
- What happens when memory is empty and the student presses MR? System displays zero or empty, consistent with standard calculator behavior
- How does the calculator handle very large or very small numbers in scientific notation? System correctly formats and evaluates numbers within standard floating-point range limits
- What happens when a student uses parentheses incorrectly (e.g., "2 × (3 + 4" with missing closing parenthesis)? System detects mismatched parentheses and displays an error message before evaluation
- How does the calculator handle nested functions (e.g., sin(cos(30)))? System correctly evaluates nested function calls respecting order of operations
- What happens when a student presses 1/x with zero as the input? System displays an error message for division by zero
- How does the calculator handle memory operations when the display shows an error? System prevents memory operations (M+, MC, MR buttons disabled) when display shows error, requiring user to clear error first before memory operations are allowed
- What happens when a student uses x^y with very large exponents? System handles within floating-point limits or displays appropriate error for overflow
- How does the calculator handle the π constant in expressions with other operations (e.g., 2π, π/2)? System correctly substitutes π value and evaluates the full expression
- What happens when a student uses the +/- button multiple times in succession? System toggles sign correctly each time (positive → negative → positive)
- How does the calculator handle memory accumulation when memory contains a very large number? System handles within floating-point limits or displays appropriate error for overflow
- What happens when a student enters an expression with both basic and advanced functions (e.g., "sin(30) + 5 × 2")? System correctly evaluates respecting order of operations
- How does the calculator handle nth root when the root value is zero or negative? System displays an error message for invalid root values
- What happens when a student uses scientific notation in a complex expression (e.g., "2.5 × 10^3 + 100")? System correctly evaluates the scientific notation and performs the operation

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide trigonometric function buttons (sin, cos, tan) in the calculator interface
- **FR-002**: System MUST evaluate trigonometric functions with angle inputs in degrees (standard for GCSE mathematics)
- **FR-003**: System MUST provide inverse trigonometric function buttons (arcsin, arccos, arctan) in the calculator interface
- **FR-004**: System MUST evaluate inverse trigonometric functions and return results in degrees
- **FR-005**: System MUST provide a reciprocal function (1/x) button that calculates the reciprocal of the current value or entered number
- **FR-006**: System MUST provide a square function (x^2) button that squares the current value or entered number
- **FR-007**: System MUST provide a power function (x^y) button that allows raising a base to an arbitrary exponent
- **FR-008**: System MUST provide memory function buttons: M+ (add to memory), MC (clear memory), MR (recall memory). Memory operations MUST be disabled when the display shows an error state, requiring the user to clear the error first
- **FR-009**: System MUST maintain calculator memory state throughout a tutoring session, persisting until explicitly cleared or session ends
- **FR-010**: System MUST provide a π (pi) constant button that inserts the mathematical constant π into expressions
- **FR-011**: System MUST provide a square root (√) function button that calculates the square root of a value
- **FR-012**: System MUST provide a cube root (∛) function button that calculates the cube root of a value
- **FR-013**: System MUST support nth root calculations via a single "ⁿ√" button that prompts users to enter the root value (n) first, then the radicand (x), following the same interaction pattern as x^y (e.g., calculate the 5th root of 32)
- **FR-014**: System MUST provide parentheses buttons (opening and closing) for expression grouping
- **FR-015**: System MUST evaluate expressions with parentheses respecting standard order of operations (parentheses first, then exponents, then multiplication/division, then addition/subtraction)
- **FR-016**: System MUST provide a scientific notation function (×10^x) via a single button that prompts users to enter the coefficient first, then the exponent, following the same interaction pattern as x^y and nth root
- **FR-017**: System MUST provide a sign change button (+/-) that toggles the sign of the current display value (what's shown on screen)
- **FR-018**: System MUST validate mathematical expressions before evaluation, detecting errors such as division by zero, invalid function inputs (e.g., arcsin of value > 1), and mismatched parentheses
- **FR-019**: System MUST display clear error messages when calculations fail due to invalid inputs or mathematical errors (e.g., "Maths Error" for square root of negative numbers, division by zero, invalid trigonometric inputs)
- **FR-020**: System MUST log all calculator operations (including advanced functions) to the calculator history for tutor reference, consistent with existing calculator logging behavior

### Key Entities *(include if feature involves data)*

- **Calculator Memory**: A storage location that holds a numeric value throughout a tutoring session. Can be modified by M+ (adds current value to memory), cleared by MC, and recalled by MR. Persists during the session but may be reset when starting a new session.
- **Calculator Expression**: A mathematical expression entered by the student, which may include numbers, operators, functions (trigonometric, roots, powers), constants (π), parentheses, and scientific notation. The expression is evaluated to produce a result.
- **Calculator History**: Existing entity that records all calculator operations. Extended to include advanced function usage (trigonometric, roots, powers, memory operations) for tutor reference.

## Clarifications

### Session 2025-01-27

- Q: Should trigonometric functions use degrees or radians? → A: Degrees (standard for GCSE mathematics curriculum)
- Q: How should memory functions behave when memory is empty and MR is pressed? → A: Display zero or empty, consistent with standard calculator behavior
- Q: Should M+ accumulate (add to existing memory) or replace? → A: Accumulate (add to existing memory value), standard calculator behavior
- Q: What precision should be used for π and trigonometric calculations? → A: Standard floating-point precision sufficient for GCSE-level accuracy requirements
- Q: How should students enter nth root calculations (specifying both root value n and radicand x)? → A: Single "ⁿ√" button that prompts for root value (n) first, then radicand (x) - similar to x^y pattern
- Q: How should the calculator handle square root of negative numbers? → A: Display "Maths Error" message
- Q: How should the calculator handle memory operations when the display shows an error? → A: Prevent memory operations (M+, MC, MR disabled) when display shows error, require user to clear error first
- Q: How should students enter scientific notation (×10^x)? → A: Single "×10^x" button that prompts for coefficient first, then exponent (e.g., press button → enter 2.5 → enter 3 → result: 2.5×10³)
- Q: When should the +/- button toggle sign - current display value or last entered number? → A: Always toggle sign of current display value (what's shown on screen)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All trigonometric functions (sin, cos, tan, arcsin, arccos, arctan) produce results accurate to at least 4 decimal places when tested with standard GCSE-level inputs (e.g., sin(30°) = 0.5, arcsin(0.5) = 30°)
- **SC-002**: Students can complete a calculation using any advanced function (trigonometric, roots, powers, scientific notation) in under 5 seconds from button press to result display
- **SC-003**: Memory functions (M+, MC, MR) work correctly in 100% of test cases, with memory persisting throughout a session until explicitly cleared
- **SC-004**: Expressions with up to 3 levels of nested parentheses evaluate correctly 100% of the time in testing
- **SC-005**: The calculator handles invalid inputs (e.g., square root of negative number, arcsin of value > 1, division by zero) by displaying clear error messages in 100% of test cases
- **SC-006**: All advanced calculator operations are logged to calculator history with 100% accuracy, allowing tutors to see the full calculation sequence
- **SC-007**: Students can use the π constant, scientific notation (×10^x), and sign change (+/-) functions successfully in 95% of attempts without errors
- **SC-008**: The calculator interface remains responsive (no noticeable delay) when using advanced functions, with results appearing within 1 second of expression evaluation

## Assumptions

- Trigonometric functions use degrees as the angle unit, consistent with GCSE mathematics curriculum standards
- Calculator memory persists only during an active tutoring session and is cleared when starting a new session or when MC is pressed
- Memory accumulation (M+) adds values to existing memory, following standard calculator behavior
- The π constant is stored with sufficient precision for GCSE-level calculations (standard floating-point representation)
- Square root and cube root functions handle positive inputs; negative inputs display "Maths Error" message
- Nth root function uses a single "ⁿ√" button that prompts for root value (n) first, then radicand (x), following the same interaction pattern as x^y
- Parentheses support is an extension of existing calculator functionality, ensuring compatibility with current expression evaluation
- Scientific notation (×10^x) uses a single button that prompts for coefficient first, then exponent, following the same interaction pattern as x^y and nth root (e.g., 2.5 × 10^3 = 2500)
- Sign change (+/-) always toggles the sign of the current display value (what's shown on screen)
- All advanced functions integrate seamlessly with existing basic calculator operations (addition, subtraction, multiplication, division)
- Error handling for advanced functions follows the same pattern as existing calculator error handling (display "Error" message for invalid operations)
- Calculator history logging includes function names and parameters for advanced operations, not just the final result
- The calculator interface layout will accommodate additional buttons without cluttering the interface, with the specific layout to be determined during planning
- All advanced functions are available whenever the calculator is visible, regardless of the specific problem type (no context-specific function filtering)

