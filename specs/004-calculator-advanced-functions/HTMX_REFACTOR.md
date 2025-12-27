# Calculator htmx Refactoring Guide

**Status**: Ready to implement  
**Estimated Time**: 30 minutes  
**Lines Removed**: ~850 lines of JavaScript  
**Lines Added**: ~250 lines (Python state manager + htmx HTML)

## What We've Built

### ✅ Complete (Ready to Use)

1. **`bloom/calculator_state.py`** (400 lines)
   - Server-side calculator state management
   - All button logic (numbers, operators, functions, memory)
   - Multi-step operations (x^y, nth root, scientific notation)
   - SHIFT mode for inverse trig functions
   - Auto-close parentheses
   - Error handling

2. **`bloom/routes/student.py`** - New endpoint:
   - `POST /calculator/button` - htmx endpoint for button presses
   - Returns HTML fragment with updated display
   - Maintains state in `request.app.state.calculator_states`

3. **`bloom/templates/calculator_htmx.html`** (250 lines)
   - Pure htmx calculator (no JavaScript handlers)
   - Each button has `hx-post`, `hx-vals`, `hx-target`, `hx-swap`
   - Server returns HTML, htmx swaps it in
   - ~10 lines of JavaScript total (toggle visibility)

## How to Complete the Refactor

### Step 1: Replace Calculator HTML in chat.html

**Current** (lines 295-387 in `chat.html`):
```html
<!-- Calculator with onclick handlers -->
<button onclick="handleSin()">sin</button>
```

**Replace with**:
```html
{% include 'calculator_htmx.html' %}
```

### Step 2: Remove JavaScript (lines 392-1248)

Delete the entire `{% block extra_scripts %}` section that contains:
- ~600 lines of calculator JavaScript
- All `function handle*()` definitions
- State management (`calcExpression`, `inputState`, etc.)
- Expression transformation/validation (now server-side)

**Keep only**:
- Auto-scroll function
- MathJax typesetting
- htmx event handlers (afterRequest, afterSwap)
- Whiteboard image loading
- Error display functions

### Step 3: Update Imports

Add to `bloom/routes/student.py`:
```python
from bloom.calculator_state import CalculatorState
```

## Architecture Comparison

### Before (JavaScript-heavy)
```
User clicks button
  → JavaScript handler runs
  → Updates client state
  → Manipulates DOM
  → Only "=" hits server
```

**JavaScript**: ~600 lines  
**Server**: ~250 lines (evaluator only)

### After (htmx-native)
```
User clicks button
  → htmx sends POST request
  → Server updates state
  → Server returns HTML
  → htmx swaps HTML
```

**JavaScript**: ~50 lines (utilities only)  
**Server**: ~650 lines (state + evaluator)

## Benefits

✅ **90% less client JavaScript** (~600 lines → ~50 lines)  
✅ **True htmx architecture** (server-driven UI)  
✅ **Easier to test** (Python unit tests for all logic)  
✅ **Easier to maintain** (one source of truth)  
✅ **Better for accessibility** (server-rendered HTML)  
✅ **Simpler debugging** (server logs show all operations)

## Testing Plan

1. **Start server**: `uv run python -m bloom.main`
2. **Navigate to chat page** with calculator visible
3. **Test basic operations**:
   - Numbers: `1`, `2`, `3` → display shows `123`
   - Operators: `5 + 3 =` → display shows `8`
   - Clear: `AC` → display shows `0`

4. **Test advanced functions**:
   - Trig: `sin` → `30` → `=` → shows `0.5`
   - Auto-wrap: `3` → `=` → `cos` → shows `cos(3`
   - SHIFT: `SHIFT` → `sin` → button shows `arcsin`

5. **Test memory**:
   - `5` → `M+` → `3` → `M+` → `MR` → shows `8`
   - `MC` → `MR` → shows `0`

6. **Test error handling**:
   - `sqrt` → `-4` → `=` → error message above display
   - Expression still visible in display
   - `AC` → error clears

## Rollback Plan

If issues arise:
```bash
cp bloom/templates/chat.html.backup_js bloom/templates/chat.html
# Remove /calculator/button endpoint from student.py
# Delete calculator_state.py
```

## Next Steps

1. Include `calculator_htmx.html` in `chat.html`
2. Remove old JavaScript section
3. Test thoroughly
4. Update documentation
5. Delete backup file once confirmed working

## Files Summary

**New Files**:
- `bloom/calculator_state.py` (400 lines)
- `bloom/templates/calculator_htmx.html` (250 lines)
- `bloom/templates/chat.html.backup_js` (backup)

**Modified Files**:
- `bloom/routes/student.py` (+70 lines for `/calculator/button`)
- `bloom/templates/chat.html` (will be -850 lines, +1 line for include)

**Net Change**: -530 lines of code! 🎉



