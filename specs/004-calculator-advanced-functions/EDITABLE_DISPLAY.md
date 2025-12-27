# Calculator Editable Display Feature

## Overview
Made the calculator display editable to improve user experience, especially when fixing errors or making quick edits.

## Implementation Date
December 26, 2025

## Problem Solved
Previously, if a user made a typo (e.g., typed `sin(450)` instead of `sin(45)`), they would need to:
- Press DEL multiple times to delete characters, OR
- Press AC to clear everything and start over

This was frustrating, especially for longer expressions.

## Solution
Made the display input field directly editable:
- Users can click the display at any time
- Edit the expression directly with keyboard/cursor
- Changes sync to server state on blur/change event
- Error messages clear automatically when user starts editing

## Technical Changes

### 1. Frontend (`calculator_htmx.html`)
- Removed `readonly` attribute from `#calc-display` input
- Changed `bg-gray-100` → `bg-white` (white background indicates editability)
- Added hover/focus states (`hover:border-blue-400`, `focus:ring-2`)
- Added htmx attributes:
  - `hx-post="/calculator/sync"` - Sync endpoint
  - `hx-trigger="change"` - Triggers on blur or Enter key
  - `hx-include="#calc-form-data"` - Includes session_id
  - `hx-target="#calc-display-container"` - Updates display container
  - `hx-swap="outerHTML"` - Replaces entire container

### 2. Backend (`bloom/routes/student.py`)
**New Endpoint: `POST /calculator/sync`**
```python
@router.post("/calculator/sync")
async def calculator_sync_expression(
    request: Request,
    expression: str = Form(...),
    session_id: int = Form(None)
)
```

**Functionality:**
- Receives manually edited expression from display
- Updates calculator state with new expression
- Clears error message (user is fixing the error)
- Returns updated HTML fragment for htmx swap
- Maintains all htmx attributes in returned HTML

**Enhanced `POST /calculator/button` Endpoint:**
- Added optional `expression: str = Form(None)` parameter
- Syncs expression to state before handling button press
- Enables Enter key to work: sync expression, then evaluate

**Enter Key Implementation:**
```javascript
// In calc-display input
onkeypress="if(event.key==='Enter'){
    event.preventDefault(); 
    document.getElementById('calc-eval-btn').click();
}"
```

- Hidden button (`calc-eval-btn`) triggers htmx POST with button="=" and current expression
- Minimal JavaScript (just event handler)
- Maintains htmx architecture (server handles all logic)

### 3. State Management (`bloom/calculator_state.py`)
No changes needed - direct expression assignment works:
```python
calc_state.expression = expression if expression else '0'
calc_state.error_message = None
```

## User Experience

### Before
```
Display: sin(450)
User: "Oops, I meant 45, not 450"
Actions: Press DEL 3 times, type "45)"
```

### After
```
Display: sin(450)  [editable field]
User: Clicks display, changes 450 → 45
Actions: Click, delete "0", press Enter to evaluate!
```

## Keyboard Support
**Enter Key = Equals Button**
- Pressing Enter in the display evaluates the expression (same as pressing =)
- Enter key syncs the current expression, then evaluates it
- No need to click the = button after editing!

## Visual Feedback
- **White background** instead of gray (indicates editability)
- **Blue border on hover** (shows it's interactive)
- **Blue ring on focus** (standard form input behavior)
- **Smooth transitions** for border colors

## Edge Cases Handled
1. **Empty input**: Defaults to '0'
2. **Error state**: Error message clears when user starts editing
3. **Session persistence**: Uses same session key as button presses
4. **htmx consistency**: Returned HTML maintains all htmx attributes
5. **Enter key**: Prevents default form submission, syncs expression, then evaluates
6. **Blur vs Enter**: Blur (change) syncs only; Enter syncs + evaluates

## Testing
```bash
# Test manual expression sync and evaluation (Enter key workflow)
python -c "
from bloom.calculator_state import CalculatorState

# Test 1: Manual sync
state = CalculatorState()
state.expression = 'sin(45)+10'
state.error_message = None
response = state.handle_button('=')
print(f'Test 1 - Manual sync + eval: {response}')

# Test 2: Enter key workflow (sync then evaluate)
state2 = CalculatorState()
state2.expression = '2+3'
response2 = state2.handle_button('=')
print(f'Test 2 - Enter key flow: {response2}')
"
# Output: 
# Test 1 - Manual sync + eval: {'display': '10.707106781186548', 'error': None}
# Test 2 - Enter key flow: {'display': '5', 'error': None}
```

## Future Enhancements
- **Real-time validation**: Show error indicator while typing invalid syntax
- **Autocomplete**: Suggest function completions (e.g., `sin(` when user types `s`)
- **Expression history**: Arrow up/down to cycle through previous expressions
- **Syntax highlighting**: Color-code functions, operators, numbers

## Related Files
- `bloom/templates/calculator_htmx.html` - Frontend template
- `bloom/routes/student.py` - Sync endpoint
- `bloom/calculator_state.py` - State management

## Spec Reference
Part of spec: `specs/004-calculator-advanced-functions/`
Not explicitly in original spec - UX improvement suggested by user.

