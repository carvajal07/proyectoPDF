import re
import operator
    
def evaluate_condition(expression: str) -> bool:
    """Evalúa una expresión completa con operadores lógicos."""
    def _looks_like_path(s: str) -> bool:
        return re.fullmatch(r"[A-Za-z_][\w.]*", s.strip()) is not None

    def _try_get_path(s: str):
        """Devuelve (True, valor) si s es un path válido en el contexto; de lo contrario (False, s)."""
        s = s.strip()
        if _looks_like_path(s):
            try:
                return True, get_value(s)
            except KeyError:
                return False, s
        return False, s

    def get_value(path: str):
        """Obtiene un valor del contexto usando notación de punto."""
        # Remover prefijos opcionales
        path = path.strip()
        if path.startswith("DATA."):
            path = path[5:]
        
        parts = path.split('.')
        value = register
        
        for part in parts:
            if isinstance(value, dict):
                if part not in value:
                    raise KeyError(f"No se encontró '{path}' en el contexto")
                value = value[part]
            else:
                raise KeyError(f"No se puede acceder a '{part}' en '{path}'")
        
        return value

    def convert_if_to_expression(code: str) -> str:
        """
        Convierte bloques if/else con returns a expresiones booleanas.
        Ejemplo: if(A){ return true; } else { return false; } -> (A)
        """
        # Normalizar espacios pero mantener estructura
        code = re.sub(r'\s+', ' ', code).strip()
        
        def find_matching_brace(s: str, start: int) -> int:
            """Encuentra la llave de cierre que corresponde a la de apertura en 'start'."""
            depth = 0
            for i in range(start, len(s)):
                if s[i] == '{':
                    depth += 1
                elif s[i] == '}':
                    depth -= 1
                    if depth == 0:
                        return i
            return -1
        
        def parse_if_block(s: str) -> str:
            s = s.strip()
            
            # Caso base: return true/false
            m = re.match(r'return\s+(true|false)\s*;?', s, re.IGNORECASE)
            if m:
                return 'True' if m.group(1).lower() == 'true' else 'False'
            
            # Caso recursivo: if(COND){THEN}else{ELSE}
            # Buscar "if("
            if_match = re.match(r'if\s*\(', s, re.IGNORECASE)
            if not if_match:
                return s
            
            # Encontrar la condición (contenido entre paréntesis)
            paren_start = s.index('(')
            paren_depth = 0
            paren_end = -1
            for i in range(paren_start, len(s)):
                if s[i] == '(':
                    paren_depth += 1
                elif s[i] == ')':
                    paren_depth -= 1
                    if paren_depth == 0:
                        paren_end = i
                        break
            
            if paren_end == -1:
                return s
            
            cond = s[paren_start + 1:paren_end].strip()
            
            # Buscar el bloque then {...}
            rest = s[paren_end + 1:].strip()
            if not rest.startswith('{'):
                return s
            
            then_end = find_matching_brace(rest, 0)
            if then_end == -1:
                return s
            
            then_block = rest[1:then_end].strip()
            
            # Buscar "else"
            after_then = rest[then_end + 1:].strip()
            has_else = after_then.lower().startswith('else')

            if has_else:
                after_else = after_then[4:].strip()  # Skip "else"
                if not after_else.startswith('{'):
                    return s
                else_end = find_matching_brace(after_else, 0)
                if else_end == -1:
                    return s
                else_block = after_else[1:else_end].strip()

                then_expr = parse_if_block(then_block)
                else_expr = parse_if_block(else_block)

                if then_expr == 'True' and else_expr == 'False':
                    return f"({cond})"
                elif then_expr == 'False' and else_expr == 'True':
                    return f"not ({cond})"
                else:
                    return f"(({cond}) and ({then_expr})) or (not ({cond}) and ({else_expr}))"

            else:
                # 🔧 NUEVO: if sin else
                then_expr = parse_if_block(then_block)
                if then_expr == 'True':
                    return f"({cond})"
                elif then_expr == 'False':
                    return f"not ({cond})"
                else:
                    # if (C) { X }  ≡  (C and X)
                    return f"(({cond}) and ({then_expr}))"
        
        try:
            return parse_if_block(code)
        except Exception as e:
            # En caso de error, devolver el código original
            return code

    def evaluate_atom(expr: str) -> bool:
        """Evalúa una expresión atómica (sin and/or/not)."""
        # Métodos personalizados disponibles
        methods = {
            "equalCaseInsensitive": lambda a, b: str(a).lower() == str(b).lower(),
            "beginWithCaseInsensitive": lambda a, b: str(a).lower().startswith(str(b).lower()),
            "endsWithCaseInsensitive": lambda a, b: str(a).lower().endswith(str(b).lower()),
            "containsCaseInsensitive": lambda a, b: str(b).lower() in str(a).lower(),
            "beginWith": lambda a, b: str(a).startswith(str(b)),
            "endsWith": lambda a, b: str(a).endswith(str(b)),
            "contains": lambda a, b: str(b) in str(a),
            "equalCase": lambda a, b: str(a) == str(b),
        }

        # Operadores de comparación
        operators = {
            "==": operator.eq, "!=": operator.ne,
            ">=": operator.ge, "<=": operator.le,
            ">": operator.gt, "<": operator.lt,
        }
        expr = expr.strip()
        
        # 1. Métodos personalizados: Path.method('arg')
        pattern = r"^([A-Za-z_][\w.]*?)\.(\w+)\(\s*['\"]([^'\"]*)['\"]?\s*\)$"
        m = re.match(pattern, expr)
        if m:
            path, method_name, arg = m.groups()
            value = get_value(path)
            
            if method_name not in methods:
                raise ValueError(f"Método no soportado: {method_name}")
            
            return methods[method_name](value, arg)
        
        # 2. Comparaciones: left OP right
        for op_str in ["==", "!=", ">=", "<=", ">", "<"]:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                if len(parts) == 2:
                    left_str = parts[0].strip()
                    right_str = parts[1].strip()

                    left_val = get_value(left_str)
                    right_val = coerce_value(left_val, right_str)

                    # si ambos numéricos, compara numéricamente
                    if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
                        return operators[op_str](left_val, right_val)

                    # si no, compara con las reglas del operador tal cual
                    return operators[op_str](left_val, right_val)
        
        # 3. Valor booleano directo
        value = get_value(expr)
        return bool(value)

    def coerce_value(reference, value_str: str):
        """Convierte value_str al tipo apropiado, soportando paths del contexto."""
        value_str = value_str.strip()

        # 0) Si es un path válido y existe → úsalo
        is_path, val = _try_get_path(value_str)
        if is_path:
            return val

        # 1) Quitar comillas
        if (value_str.startswith('"') and value_str.endswith('"')) or \
        (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        # 2) Boolean
        if value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true'

        # 3) Números: intenta tipar en función del lado izquierdo
        if isinstance(reference, (int, float)):
            try:
                # si referencia es int, intenta int; si no, float
                return int(value_str) if isinstance(reference, int) else float(value_str)
            except Exception:
                # si no se pudo, intenta literal Python (p.ej. 1.0, 0x10)
                try:
                    lit = eval(value_str, {"__builtins__": {}}, {})
                    return lit
                except Exception:
                    pass

        # 4) Fallback: intenta literal Python (None, números, bools)
        try:
            return eval(value_str, {"__builtins__": {}}, {})
        except Exception:
            return value_str
        
    def _strip_trailing_block_safe(s: str) -> str:
        s = re.sub(r'\s+', ' ', s).strip()
        if '{' in s and not s.lstrip().lower().startswith('if'):
            left = s.split('{', 1)[0].strip()
            if left and left.count('(') == left.count(')'):
                return left
        return s

    def _eval_logic(expr: str) -> bool:
        """Evalúa expresiones lógicas con precedencia: NOT > AND > OR."""
        expr = expr.strip()
        
        # Remover paréntesis exteriores balanceados
        if expr.startswith('(') and expr.endswith(')'):
            if _is_balanced_outer(expr):
                return _eval_logic(expr[1:-1])
        
        # OR (menor precedencia)
        parts = _split_by_operator(expr, ' or ')
        if len(parts) > 1:
            return any(_eval_logic(p) for p in parts)
        
        # AND
        parts = _split_by_operator(expr, ' and ')
        if len(parts) > 1:
            return all(_eval_logic(p) for p in parts)
        
        # NOT
        if expr.lower().startswith('not '):
            return not _eval_logic(expr[4:].strip())
        
        # Átomo
        try:
            return evaluate_atom(expr)
        except KeyError:
            return False

    def _split_by_operator(expr: str, op: str) -> list:
        """Divide una expresión por un operador respetando paréntesis."""
        parts = []
        current = []
        depth = 0
        i = 0
        
        while i < len(expr):
            if expr[i] == '(':
                depth += 1
                current.append(expr[i])
            elif expr[i] == ')':
                depth -= 1
                current.append(expr[i])
            elif depth == 0 and expr[i:i+len(op)] == op:
                parts.append(''.join(current).strip())
                current = []
                i += len(op) - 1
            else:
                current.append(expr[i])
            i += 1
        
        if current:
            parts.append(''.join(current).strip())
        
        return parts if len(parts) > 1 else [expr]

    def _is_balanced_outer(expr: str) -> bool:
        """Verifica si los paréntesis exteriores están balanceados."""
        depth = 0
        for i, ch in enumerate(expr):
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0 and i < len(expr) - 1:
                    return False
        return depth == 0

    # Convertir if/else a expresión
    expression = convert_if_to_expression(expression)
    
    # Limpiar expresión cortando bloques que sobren
    expression = _strip_trailing_block_safe(expression)
    
    # Normalizar operadores lógicos
    expression = re.sub(r'\s+', ' ', expression)
    expression = re.sub(r'\band\b', ' and ', expression, flags=re.IGNORECASE)
    expression = re.sub(r'\bor\b', ' or ', expression, flags=re.IGNORECASE)
    expression = re.sub(r'\bnot\b', ' not ', expression, flags=re.IGNORECASE)
    expression = expression.strip()
    
    return _eval_logic(expression)



register = {
    "CR": {
        "Band_PO": True,
        "BanderaCertificadoSaldos": False,
        "FlagX": True,
        "FlagY": True,
    },
    "_PO": True,
    "Canal": "PE",
    "Status": "OK123",
    "A": {"B": {"C": True}},
    "Value": 10,
    "Zero": 0,
    "eraCertificadoSaldos": False
}

("""
if(CR.Band_PO and _PO){
return true;
}
""", True),

tests = [
    ("""
    if(CR.Band_PO and _PO){
    return true;
    }else{ return false;//Pruebas}
    """, True),
    # Test 1: if/else anidado -> (A) and not (B)
    ("""
    if(CR.Band_PO) {
        if(CR.BanderaCertificadoSaldos) {
            return false;
        } else {
            return true;
        }
    } else {
        return false;
    }
    """, True),
    
    # Test 2: if/else anidado -> (A) and (B)
    ("""
    if(CR.FlagX) {
        if(CR.FlagY) {
            return true;
        } else {
            return false;
        }
    } else {
        return false;
    }
    """, True),
    
    # Test 3: if simple
    ("if(A.B.C){ return true; } else { return false; }", True),
    
    # Test 4: if negado
    ("if(CR.Band_PO){ return false; } else { return true; }", False),
    
    # Test 5: Expresión con espacios
    ("CR.Band_PO AND not CR.BanderaCertificadoSaldos", True),
    
    # Test 6: Variable con 'and' en el nombre
    ("CR.Band_PO and _PO", True),
    
    # Test 7: Métodos personalizados 🔥
    ("Canal.equalCaseInsensitive('pe') and not Status.beginWith('ERR')", True),
    
    # Test 8: Método case insensitive
    ("Status.beginWithCaseInsensitive('ok')", True),
    
    # Test 9: Expresión con bloque colgante
    ("(not CR.BanderaCertificadoSaldos) { if (CR.FlagX) }", True),
    
    # Test 10: Variable inexistente
    ("Missing.Var and CR.Band_PO", False),
]

print("=" * 70)
print("EJECUTANDO TESTS")
print("=" * 70)

passed = 0
failed = 0

for i, (expr, expected) in enumerate(tests, 1):
    try:
        result = evaluate_condition(expr)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} Test {i}: {result} (esperado: {expected})")
    except Exception as e:
        failed += 1
        print(f"❌ FAIL Test {i}: Error - {e}")
        print(f"   Expresión: {expr.strip()[:100]}...")

print(f"\n{'=' * 70}")
print(f"Resultados: {passed} passed, {failed} failed")
print("=" * 70)

# Test complejo
print("\nTEST COMPLEJO:")
complex_condition = """
if(CR.Band_PO and not CR.BanderaCertificadoSaldos or 
    (Canal.equalCaseInsensitive('pe') and not Status.beginWith('ERR')))
{
    if(A.B.C and (CR.FlagX or CR.FlagY))
    {
        if((Value > Zero and CR.FlagX) or not eraCertificadoSaldos)
        {
            if(CR.FlagY and not (CR.BanderaCertificadoSaldos or not CR.Band_PO))
            {
                return true;
            }
            else
            {
                return false;
            }
        }
        else
        {
            return false;
        }
    }
    else
    {
        return false;
    }
}
else
{
    return false;
}
"""

result = evaluate_condition(complex_condition)
status = "✅ PASS" if result == True else "❌ FAIL"
print(f"{status} Test complejo: {result} (esperado: True)")