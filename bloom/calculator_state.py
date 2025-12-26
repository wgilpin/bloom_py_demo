"""
Calculator State Manager (Session-based for htmx)

Manages calculator state server-side in user sessions.
This enables proper htmx implementation with minimal client-side JavaScript.
"""

from typing import Dict, Any, Optional
from bloom.calculator_evaluator import evaluate_expression


class CalculatorState:
    """Manages calculator state for a single session."""
    
    def __init__(self):
        self.expression = '0'
        self.memory = 0
        self.last_answer = 0
        self.input_state = 'normal'  # 'normal' | 'waiting_base' | 'waiting_exponent' | etc.
        self.pending_operation = None  # 'x^y' | 'nth_root' | 'scientific'
        self.pending_value = None
        self.shift_mode = False
        self.error_message = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dict for session storage."""
        return {
            'expression': self.expression,
            'memory': self.memory,
            'last_answer': self.last_answer,
            'input_state': self.input_state,
            'pending_operation': self.pending_operation,
            'pending_value': self.pending_value,
            'shift_mode': self.shift_mode,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculatorState':
        """Deserialize state from dict."""
        state = cls()
        state.expression = data.get('expression', '0')
        state.memory = data.get('memory', 0)
        state.last_answer = data.get('last_answer', 0)
        state.input_state = data.get('input_state', 'normal')
        state.pending_operation = data.get('pending_operation')
        state.pending_value = data.get('pending_value')
        state.shift_mode = data.get('shift_mode', False)
        state.error_message = data.get('error_message')
        return state
    
    def handle_button(self, button: str, session_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Handle a button press and return response for htmx.
        
        Args:
            button: Button identifier (e.g., '7', '+', 'sin', '=', 'AC')
            session_id: Optional session ID for logging
            
        Returns:
            Dict with 'display', 'error', 'shift_labels' keys
        """
        # Clear error on any new input (except AC which is handled separately)
        if button != 'AC' and self.error_message:
            self.error_message = None
        
        # Handle special buttons
        if button == 'AC':
            return self._handle_all_clear()
        elif button == 'DEL':
            return self._handle_delete()
        elif button == '=':
            return self._handle_evaluate(session_id)
        elif button == 'SHIFT':
            return self._handle_shift()
        elif button == 'M+':
            return self._handle_memory_plus()
        elif button == 'MC':
            return self._handle_memory_clear()
        elif button == 'MR':
            return self._handle_memory_recall()
        elif button == 'Ans':
            return self._handle_ans()
        elif button == 'π':
            return self._handle_pi()
        elif button == '+/-':
            return self._handle_sign_change()
        elif button == '1/x':
            return self._handle_reciprocal()
        elif button == 'x^2':
            return self._handle_square()
        elif button == 'x^y':
            return self._handle_x_to_y()
        elif button == 'sqrt':
            return self._handle_sqrt()
        elif button == 'cbrt':
            return self._handle_cbrt()
        elif button == 'nth_root':
            return self._handle_nth_root()
        elif button == 'x10^x':
            return self._handle_scientific_notation()
        elif button in ['sin', 'cos', 'tan']:
            return self._handle_trig(button)
        else:
            # Regular input (numbers, operators, parentheses)
            return self._handle_append(button)
    
    def _handle_all_clear(self) -> Dict[str, Any]:
        """Reset calculator state."""
        self.expression = '0'
        self.input_state = 'normal'
        self.pending_operation = None
        self.pending_value = None
        self.shift_mode = False
        self.error_message = None
        return {
            'display': self.expression,
            'error': None,
            'shift_labels': {'sin': 'sin', 'cos': 'cos', 'tan': 'tan'}
        }
    
    def _handle_delete(self) -> Dict[str, Any]:
        """Delete last character."""
        if self.expression and self.expression not in ['0', 'Maths Error']:
            self.expression = self.expression[:-1] or '0'
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_shift(self) -> Dict[str, Any]:
        """Toggle SHIFT mode for inverse trig functions."""
        self.shift_mode = not self.shift_mode
        labels = {
            'sin': 'arcsin' if self.shift_mode else 'sin',
            'cos': 'arccos' if self.shift_mode else 'cos',
            'tan': 'arctan' if self.shift_mode else 'tan'
        }
        return {'display': self.expression, 'error': self.error_message, 'shift_labels': labels}
    
    def _handle_append(self, value: str) -> Dict[str, Any]:
        """Append value to expression."""
        # Handle multi-step input states
        if self.input_state in ['waiting_exponent', 'waiting_radicand']:
            if self.expression == '' or self.expression.startswith('Enter'):
                self.expression = value
            else:
                self.expression += value
            return {'display': self.expression, 'error': self.error_message}
        
        # Normal input
        if self.expression in ['0', 'Maths Error'] or self.expression.startswith('Enter'):
            self.expression = value
        else:
            self.expression += value
        
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_evaluate(self, session_id: Optional[int]) -> Dict[str, Any]:
        """Evaluate current expression."""
        from bloom.calculator_evaluator import evaluate_expression
        
        # Handle multi-step operations
        if self.input_state in ['waiting_exponent', 'waiting_radicand']:
            return self._complete_multi_step()
        
        if self.input_state in ['waiting_base', 'waiting_root', 'waiting_coefficient']:
            # Store first value and transition to next state
            self.pending_value = float(self.expression) if self.expression else 0
            if self.input_state == 'waiting_base':
                self.input_state = 'waiting_exponent'
                self.expression = 'Enter exponent:'
            elif self.input_state == 'waiting_root':
                self.input_state = 'waiting_radicand'
                self.expression = 'Enter radicand:'
            elif self.input_state == 'waiting_coefficient':
                self.input_state = 'waiting_exponent'
                self.expression = 'Enter exponent:'
            return {'display': self.expression, 'error': self.error_message}
        
        # Auto-close parentheses (Casio-style)
        open_parens = self.expression.count('(')
        close_parens = self.expression.count(')')
        if open_parens > close_parens:
            self.expression += ')' * (open_parens - close_parens)
        
        # Evaluate
        result = evaluate_expression(self.expression)
        
        if 'error' in result:
            self.error_message = result['error']
            return {'display': self.expression, 'error': self.error_message}
        else:
            self.last_answer = result['result']
            self.expression = str(result['result'])
            self.error_message = None
            return {'display': self.expression, 'error': None}
    
    def _complete_multi_step(self) -> Dict[str, Any]:
        """Complete multi-step operation (x^y, nth_root, scientific)."""
        second_value = float(self.expression) if self.expression else 0
        
        if self.pending_operation == 'x^y':
            expr = f'{self.pending_value}^{second_value}'
        elif self.pending_operation == 'nth_root':
            expr = f'root({self.pending_value}, {second_value})'
        elif self.pending_operation == 'scientific':
            expr = f'{self.pending_value} * 10^{second_value}'
        else:
            self.input_state = 'normal'
            return {'display': self.expression, 'error': self.error_message}
        
        # Reset state
        self.input_state = 'normal'
        self.pending_operation = None
        self.pending_value = None
        
        # Evaluate
        result = evaluate_expression(expr)
        if 'error' in result:
            self.error_message = result['error']
            return {'display': expr, 'error': self.error_message}
        else:
            self.last_answer = result['result']
            self.expression = str(result['result'])
            return {'display': self.expression, 'error': None}
    
    def _handle_trig(self, func: str) -> Dict[str, Any]:
        """Handle trig function button (sin/cos/tan or arcsin/arccos/arctan)."""
        # Auto-wrap if there's a value
        should_wrap = self.expression and self.expression not in ['0', 'Maths Error']
        
        if self.shift_mode:
            func = f'a{func}'  # asin, acos, atan
            self.shift_mode = False
        
        if should_wrap:
            self.expression = f'{func}({self.expression}'
        else:
            self.expression = f'{func}('
        
        return {
            'display': self.expression,
            'error': self.error_message,
            'shift_labels': {'sin': 'sin', 'cos': 'cos', 'tan': 'tan'}  # Reset labels
        }
    
    def _handle_sqrt(self) -> Dict[str, Any]:
        """Handle square root."""
        should_wrap = self.expression and self.expression not in ['0', 'Maths Error']
        if should_wrap:
            self.expression = f'sqrt({self.expression}'
        else:
            self.expression = 'sqrt('
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_cbrt(self) -> Dict[str, Any]:
        """Handle cube root."""
        should_wrap = self.expression and self.expression not in ['0', 'Maths Error']
        if should_wrap:
            self.expression = f'cbrt({self.expression}'
        else:
            self.expression = 'cbrt('
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_pi(self) -> Dict[str, Any]:
        """Append π constant."""
        return self._handle_append('π')
    
    def _handle_ans(self) -> Dict[str, Any]:
        """Append last answer."""
        return self._handle_append(str(self.last_answer))
    
    def _handle_reciprocal(self) -> Dict[str, Any]:
        """Handle 1/x."""
        if self.expression not in ['', '0', 'Maths Error']:
            self.expression = f'1/({self.expression})'
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_sign_change(self) -> Dict[str, Any]:
        """Toggle sign of current value."""
        if self.expression and self.expression not in ['0', 'Maths Error']:
            try:
                value = float(self.expression)
                self.expression = str(-value)
            except ValueError:
                pass
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_square(self) -> Dict[str, Any]:
        """Square current value."""
        if self.expression not in ['', '0', 'Maths Error']:
            self.expression = f'({self.expression})^2'
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_x_to_y(self) -> Dict[str, Any]:
        """Start x^y multi-step input."""
        if self.expression and self.expression not in ['0', 'Maths Error']:
            self.pending_value = float(self.expression)
            self.input_state = 'waiting_exponent'
            self.pending_operation = 'x^y'
            self.expression = 'Enter exponent:'
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_nth_root(self) -> Dict[str, Any]:
        """Start nth root multi-step input."""
        if self.expression and self.expression not in ['0', 'Maths Error']:
            self.pending_value = float(self.expression)
            self.input_state = 'waiting_radicand'
            self.pending_operation = 'nth_root'
            self.expression = 'Enter radicand:'
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_scientific_notation(self) -> Dict[str, Any]:
        """Start scientific notation multi-step input."""
        if self.expression and self.expression not in ['0', 'Maths Error']:
            self.pending_value = float(self.expression)
            self.input_state = 'waiting_exponent'
            self.pending_operation = 'scientific'
            self.expression = 'Enter exponent:'
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_memory_plus(self) -> Dict[str, Any]:
        """Add current value to memory."""
        if self.expression not in ['Maths Error', '']:
            try:
                value = float(self.expression)
                self.memory += value
            except ValueError:
                pass
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_memory_clear(self) -> Dict[str, Any]:
        """Clear memory."""
        self.memory = 0
        return {'display': self.expression, 'error': self.error_message}
    
    def _handle_memory_recall(self) -> Dict[str, Any]:
        """Recall memory value."""
        self.expression = str(self.memory) if self.memory != 0 else '0'
        return {'display': self.expression, 'error': self.error_message}

