"""
Unit Tests: Calculator Evaluator (Python Backend)

Tests for expression transformation, validation, and evaluation functions
in the backend calculator evaluator module.

This replaces the JavaScript unit tests (test_calculator_logic.js) now that
calculator evaluation is handled server-side following the htmx pattern.

Run with: pytest tests/test_calculator_evaluator.py
Or: python -m pytest tests/test_calculator_evaluator.py -v
"""

import math
import pytest
from bloom.calculator_evaluator import (
    transform_expression,
    validate_expression,
    evaluate_expression
)


# ====================================================================================
# Tests for transform_expression()
# ====================================================================================

class TestTransformExpression:
    """Tests for expression transformation (calculator syntax → Python math)"""
    
    def test_sin_degrees_to_radians(self):
        """sin(30) should transform to math.sin(math.radians(30))"""
        result = transform_expression('sin(30)')
        assert 'math.sin(math.radians(30))' in result
        # Verify it evaluates correctly
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 0.5) < 0.0001
    
    def test_cos_degrees_to_radians(self):
        """cos(60) should equal 0.5"""
        result = transform_expression('cos(60)')
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 0.5) < 0.0001
    
    def test_tan_degrees_to_radians(self):
        """tan(45) should equal 1.0"""
        result = transform_expression('tan(45)')
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 1.0) < 0.01
    
    def test_asin_radians_to_degrees(self):
        """asin(0.5) should equal 30 degrees"""
        result = transform_expression('asin(0.5)')
        assert 'math.degrees(math.asin(0.5))' in result
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 30) < 0.0001
    
    def test_acos_radians_to_degrees(self):
        """acos(0.5) should equal 60 degrees"""
        result = transform_expression('acos(0.5)')
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 60) < 0.0001
    
    def test_atan_radians_to_degrees(self):
        """atan(1) should equal 45 degrees"""
        result = transform_expression('atan(1)')
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 45) < 0.0001
    
    def test_pi_constant(self):
        """π should be replaced with math.pi"""
        result = transform_expression('π')
        assert 'math.pi' in result
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - math.pi) < 0.0001
    
    def test_pi_in_expression(self):
        """2 * π should work correctly"""
        result = transform_expression('2 * π')
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 2 * math.pi) < 0.0001
    
    def test_sqrt_transformation(self):
        """sqrt(16) should equal 4"""
        result = transform_expression('sqrt(16)')
        assert 'math.sqrt(16)' in result
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 4) < 0.0001
    
    def test_pow_transformation(self):
        """2^3 should equal 8"""
        result = transform_expression('2^3')
        assert 'math.pow(2, 3)' in result
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 8) < 0.0001
    
    def test_cbrt_transformation(self):
        """cbrt(8) should equal 2"""
        result = transform_expression('cbrt(8)')
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 2) < 0.0001
    
    def test_nth_root_transformation(self):
        """root(2, 16) should equal 4"""
        result = transform_expression('root(2, 16)')
        assert 'math.pow(16, 1/2)' in result
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 4) < 0.0001
    
    def test_complex_expression(self):
        """sin(30) + sqrt(16) + 2^3 should equal 12.5"""
        result = transform_expression('sin(30) + sqrt(16) + 2^3')
        assert abs(eval(result, {'__builtins__': {}}, {'math': math}) - 12.5) < 0.0001


# ====================================================================================
# Tests for validate_expression()
# ====================================================================================

class TestValidateExpression:
    """Tests for expression validation (check for errors before evaluation)"""
    
    def test_valid_simple_expression(self):
        """Simple valid expression should pass"""
        result = validate_expression('2 + 3')
        assert result['valid'] is True
    
    def test_division_by_zero(self):
        """5 / 0 should be invalid"""
        result = validate_expression('5 / 0')
        assert result['valid'] is False
        assert result['error'] == 'Maths Error'
    
    def test_division_by_zero_with_space(self):
        """5 / 0 (with space) should be invalid"""
        result = validate_expression('5 / 0')
        assert result['valid'] is False
    
    def test_division_by_decimal_valid(self):
        """5 / 0.5 should be valid (not zero)"""
        result = validate_expression('5 / 0.5')
        assert result['valid'] is True
    
    def test_arcsin_out_of_range_positive(self):
        """asin(2) should be invalid (outside [-1, 1])"""
        result = validate_expression('asin(2)')
        assert result['valid'] is False
        assert result['error'] == 'Maths Error'
    
    def test_arcsin_out_of_range_negative(self):
        """asin(-2) should be invalid (outside [-1, 1])"""
        result = validate_expression('asin(-2)')
        assert result['valid'] is False
    
    def test_arcsin_in_range(self):
        """asin(0.5) should be valid (within [-1, 1])"""
        result = validate_expression('asin(0.5)')
        assert result['valid'] is True
    
    def test_acos_out_of_range(self):
        """acos(2) should be invalid (outside [-1, 1])"""
        result = validate_expression('acos(2)')
        assert result['valid'] is False
    
    def test_acos_in_range(self):
        """acos(0.5) should be valid (within [-1, 1])"""
        result = validate_expression('acos(0.5)')
        assert result['valid'] is True
    
    def test_sqrt_negative(self):
        """sqrt(-4) should be invalid"""
        result = validate_expression('sqrt(-4)')
        assert result['valid'] is False
        assert result['error'] == 'Maths Error'
    
    def test_sqrt_positive(self):
        """sqrt(16) should be valid"""
        result = validate_expression('sqrt(16)')
        assert result['valid'] is True
    
    def test_nth_root_even_root_negative(self):
        """root(2, -4) should be invalid (even root of negative)"""
        result = validate_expression('root(2, -4)')
        assert result['valid'] is False
    
    def test_nth_root_odd_root_negative(self):
        """root(3, -8) should be valid (odd root of negative)"""
        result = validate_expression('root(3, -8)')
        assert result['valid'] is True
    
    def test_nth_root_zero_root_value(self):
        """root(0, 16) should be invalid (zero root value)"""
        result = validate_expression('root(0, 16)')
        assert result['valid'] is False
    
    def test_mismatched_parentheses_missing_closing(self):
        """2 * (3 + 4 should be invalid (missing closing parenthesis)"""
        result = validate_expression('2 * (3 + 4')
        assert result['valid'] is False
        assert result['error'] == 'Maths Error'
    
    def test_mismatched_parentheses_extra_closing(self):
        """2 * (3 + 4)) should be invalid (extra closing parenthesis)"""
        result = validate_expression('2 * (3 + 4))')
        assert result['valid'] is False
    
    def test_valid_nested_parentheses(self):
        """2 * ((3 + 4) * 2) should be valid"""
        result = validate_expression('2 * ((3 + 4) * 2)')
        assert result['valid'] is True
    
    def test_complex_valid_expression(self):
        """sin(30) + sqrt(16) * (2 + 3) should be valid"""
        result = validate_expression('sin(30) + sqrt(16) * (2 + 3)')
        assert result['valid'] is True


# ====================================================================================
# Tests for evaluate_expression() - Integration Tests
# ====================================================================================

class TestEvaluateExpression:
    """Tests for end-to-end expression evaluation (validate + transform + eval)"""
    
    def test_simple_arithmetic(self):
        """2 + 3 should equal 5"""
        result = evaluate_expression('2 + 3')
        assert result.get('result') == 5
    
    def test_trigonometric_function(self):
        """sin(30) should equal 0.5"""
        result = evaluate_expression('sin(30)')
        assert abs(result.get('result', 0) - 0.5) < 0.0001
    
    def test_complex_expression(self):
        """sin(30) + sqrt(16) + 2^3 should equal 12.5"""
        result = evaluate_expression('sin(30) + sqrt(16) + 2^3')
        assert abs(result.get('result', 0) - 12.5) < 0.0001
    
    def test_division_by_zero_error(self):
        """5 / 0 should return error"""
        result = evaluate_expression('5 / 0')
        assert 'error' in result
        assert result['error'] == 'Maths Error'
    
    def test_sqrt_negative_error(self):
        """sqrt(-4) should return error"""
        result = evaluate_expression('sqrt(-4)')
        assert 'error' in result
        assert result['error'] == 'Maths Error'
    
    def test_arcsin_out_of_range_error(self):
        """asin(2) should return error"""
        result = evaluate_expression('asin(2)')
        assert 'error' in result
        assert result['error'] == 'Maths Error'
    
    def test_parentheses_nested(self):
        """2 * ((3 + 4) * 2) should equal 28"""
        result = evaluate_expression('2 * ((3 + 4) * 2)')
        assert result.get('result') == 28
    
    def test_parentheses_with_functions(self):
        """sin(30) + (5 * 2) should equal 10.5"""
        result = evaluate_expression('sin(30) + (5 * 2)')
        assert abs(result.get('result', 0) - 10.5) < 0.0001
    
    def test_pi_constant(self):
        """π should evaluate to math.pi"""
        result = evaluate_expression('π')
        assert abs(result.get('result', 0) - math.pi) < 0.0001
    
    def test_power_function(self):
        """2^10 should equal 1024"""
        result = evaluate_expression('2^10')
        assert result.get('result') == 1024


if __name__ == '__main__':
    # Allow running tests directly with: python tests/test_calculator_evaluator.py
    pytest.main([__file__, '-v'])

