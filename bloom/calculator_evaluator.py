"""
Calculator Expression Evaluator

Provides server-side expression transformation, validation, and evaluation
for the advanced calculator feature.

This replaces client-side JavaScript evaluation with proper backend processing,
following the htmx architecture pattern.
"""

import math
import re
from typing import Dict, Any


def transform_expression(expr: str) -> str:
    """
    Transforms calculator expression syntax to Python math expressions.
    
    Transformations:
    - sin/cos/tan: Converts degrees to radians (GCSE standard)
    - asin/acos/atan: Converts radians to degrees for output
    - π: Replaces with math.pi
    - sqrt/cbrt: Converts to math.sqrt/math.cbrt
    - x^y: Converts to math.pow(x, y)
    - root(n, x): Converts to math.pow(x, 1/n)
    
    Args:
        expr: Calculator expression string (e.g., "sin(30) + 5")
        
    Returns:
        Transformed expression ready for eval() (e.g., "math.sin(math.radians(30)) + 5")
    """
    # IMPORTANT: Replace inverse functions BEFORE regular functions to avoid partial matches
    # e.g., "asin(" contains "sin(" so we must replace "asin(" first
    
    # Replace inverse trig functions (radians to degrees for output)
    expr = re.sub(r'\basin\(([^)]+)\)', r'math.degrees(math.asin(\1))', expr)
    expr = re.sub(r'\bacos\(([^)]+)\)', r'math.degrees(math.acos(\1))', expr)
    expr = re.sub(r'\batan\(([^)]+)\)', r'math.degrees(math.atan(\1))', expr)
    
    # Replace regular trig functions (degrees to radians for input)
    expr = re.sub(r'\bsin\(([^)]+)\)', r'math.sin(math.radians(\1))', expr)
    expr = re.sub(r'\bcos\(([^)]+)\)', r'math.cos(math.radians(\1))', expr)
    expr = re.sub(r'\btan\(([^)]+)\)', r'math.tan(math.radians(\1))', expr)
    
    # Replace π constant
    expr = expr.replace('π', 'math.pi')
    
    # Replace sqrt and cbrt
    expr = re.sub(r'\bsqrt\(([^)]+)\)', r'math.sqrt(\1)', expr)
    expr = re.sub(r'\bcbrt\(([^)]+)\)', r'math.pow(\1, 1/3)', expr)
    
    # Replace x^y with math.pow(x, y)
    expr = re.sub(r'([0-9.]+)\^([0-9.]+)', r'math.pow(\1, \2)', expr)
    
    # Replace nth root: root(n, x) → math.pow(x, 1/n)
    expr = re.sub(r'\broot\(([^,]+),\s*([^)]+)\)', r'math.pow(\2, 1/\1)', expr)
    
    return expr


def validate_expression(expr: str) -> Dict[str, Any]:
    """
    Validates mathematical expression before evaluation.
    
    Checks for:
    - Division by zero
    - Invalid arcsin/acos range (must be in [-1, 1])
    - Square root of negative numbers
    - Nth root of negative with even root
    - Mismatched parentheses
    - Zero as root value
    
    Args:
        expr: Calculator expression string
        
    Returns:
        Dict with 'valid' (bool) and optional 'error' (str) keys
        Example: {'valid': False, 'error': 'Maths Error'}
    """
    # Check for division by zero
    # Match: /0 or / 0 at end of string or followed by non-digit/non-dot
    if re.search(r'/\s*0\s*$', expr) or re.search(r'/\s*0[^\.\d]', expr):
        return {'valid': False, 'error': 'Maths Error'}
    
    # Check arcsin values (must be in [-1, 1])
    arcsin_matches = re.findall(r'asin\(([^)]+)\)', expr)
    for match in arcsin_matches:
        try:
            value = float(match.strip())
            if value < -1 or value > 1:
                return {'valid': False, 'error': 'Maths Error'}
        except ValueError:
            # Can't parse as float, will fail during evaluation
            pass
    
    # Check acos values (must be in [-1, 1])
    acos_matches = re.findall(r'acos\(([^)]+)\)', expr)
    for match in acos_matches:
        try:
            value = float(match.strip())
            if value < -1 or value > 1:
                return {'valid': False, 'error': 'Maths Error'}
        except ValueError:
            pass
    
    # Check for square root of negative numbers
    sqrt_matches = re.findall(r'sqrt\(([^)]+)\)', expr)
    for match in sqrt_matches:
        try:
            value = float(match.strip())
            if value < 0:
                return {'valid': False, 'error': 'Maths Error'}
        except ValueError:
            pass
    
    # Check nth root of negative with even root
    root_matches = re.findall(r'root\(([^,]+),\s*([^)]+)\)', expr)
    for root_value_str, radicand_str in root_matches:
        try:
            root_value = float(root_value_str.strip())
            radicand = float(radicand_str.strip())
            
            # Even root of negative is invalid
            if root_value % 2 == 0 and radicand < 0:
                return {'valid': False, 'error': 'Maths Error'}
            
            # Root value cannot be zero
            if root_value == 0:
                return {'valid': False, 'error': 'Maths Error'}
        except ValueError:
            pass
    
    # Check for mismatched parentheses
    open_parens = expr.count('(')
    close_parens = expr.count(')')
    if open_parens != close_parens:
        return {'valid': False, 'error': 'Maths Error'}
    
    return {'valid': True}


def evaluate_expression(expr: str) -> Dict[str, Any]:
    """
    Evaluates a calculator expression with validation and transformation.
    
    Process:
    1. Validate expression (check for errors)
    2. Transform expression (convert calculator syntax to Python)
    3. Sanitize expression (security check)
    4. Evaluate using eval() with restricted namespace
    5. Return result or error
    
    Args:
        expr: Calculator expression string (e.g., "sin(30) + 5")
        
    Returns:
        Dict with 'result' or 'error' key
        Examples:
            {'result': 10.5}
            {'error': 'Maths Error'}
    """
    # Validate expression
    validation = validate_expression(expr)
    if not validation['valid']:
        return {'error': validation['error']}
    
    # Transform expression
    try:
        transformed = transform_expression(expr)
    except Exception as e:
        return {'error': 'Maths Error'}
    
    # Sanitize: Only allow safe characters
    # Allow: digits, operators, parentheses, dots, spaces, math module calls
    safe_pattern = r'^[0-9+\-*/().,\s]+$|math\.(sin|cos|tan|asin|acos|atan|sqrt|pow|pi|degrees|radians|e)'
    if not re.match(safe_pattern, transformed.replace('math.', '')):
        # Additional check: ensure only math module functions are used
        if 'math.' in transformed:
            # Extract all function calls
            functions = re.findall(r'math\.(\w+)', transformed)
            allowed_functions = {
                'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
                'sqrt', 'pow', 'degrees', 'radians', 'pi', 'e'
            }
            if not all(f in allowed_functions for f in functions):
                return {'error': 'Maths Error'}
        else:
            return {'error': 'Maths Error'}
    
    # Evaluate with restricted namespace (only math module)
    try:
        result = eval(transformed, {'__builtins__': {}}, {'math': math})
        
        # Check for invalid results (NaN, Infinity)
        if not isinstance(result, (int, float)) or math.isnan(result) or math.isinf(result):
            return {'error': 'Maths Error'}
        
        return {'result': result}
    except (ValueError, ZeroDivisionError, OverflowError, ArithmeticError) as e:
        return {'error': 'Maths Error'}
    except Exception as e:
        return {'error': 'Maths Error'}



