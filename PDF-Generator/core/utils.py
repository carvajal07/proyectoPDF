import re
import operator
from decimal import Decimal
import core.constants as const

def convert_units(value):
    """Convierte las unidades del XML de metros a puntos para ReportLab"""
    value = Decimal(value) 
    return float(value * Decimal(72) * Decimal(39.3701))  # Convertir metros a puntos (72 puntos = 1 inch, 39.37 inches = 1 metro)    

def get_variable_value(var_id, variables, full_context, context=None, default=None):
    """Obtiene el valor real de una variable desde el JSON (self.register) usando la jerarquía definida por ParentId."""
    def resolve_hierarchy_path(variable_id):
        """Construye la ruta jerárquica completa basada en los ParentId."""
        path = []
        current_id = variable_id

        while current_id:
            variable_object = variables.get(current_id)
            if variable_object is None:
                break

            name_elem = variable_object.find('Name')
            name = name_elem.text if name_elem is not None else None
            
            # 🚩 OMITE 'Value'
            if name and name != "Value":
                path.insert(0, name)  # Insertamos al principio para construir la ruta

            parent_elem = variable_object.find('ParentId')
            current_id = parent_elem.text if parent_elem is not None else None

        return path

    def get_value_from_path(data, path):
        """Navega el diccionario usando la ruta para obtener el valor."""
        # Si el contexto no tiene las claves iniciales las omito
        while path and not (isinstance(data, dict) and path[0] in data):
            path.pop(0)

        for key in path:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                # Retornar valor por defecto cuando no sea necesario validar la existencia del path
                if default is not None:
                    return default
                else:
                    raise ValueError(f"ERROR: No se encontró la clave '{key}' en el path '{' -> '.join(path)}'")
        # Transformar los valores numericos a String para evitar problemas en los join de los textos
        if isinstance(data, (int, float, Decimal)) and not isinstance(data, bool):        
            data = str(data)
        
        return data

    # Construimos el path desde la raíz hasta la variable actual
    full_path = resolve_hierarchy_path(var_id)
    if context is None:
        context = full_context

    return get_value_from_path(context, full_path)

def evaluate_condition(expression: str, context) -> bool:
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

    def get_value_from_path(path):
        path = path.replace("DATA.","")
        parts = path.strip().split('.')
        val = context
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                raise KeyError(f"No se encontró '{path}' en el contexto.")
        return val

    def get_value(path: str):
        """Obtiene un valor del contexto usando notación de punto."""
        # Remover prefijos opcionales
        path = path.strip()
        if path.startswith("CR."):
            path = path.replace("CR.",f"{const.PRINCIPAL_ARRAY}.")
        if path.startswith("DATA."):
            path = path[5:]
        
        parts = path.split('.')
        value = context
        
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
            "isEmpty": lambda a: (a is None) or (str(a).strip() == "") or (a == []),
            "isNotEmpty": lambda a: not ((a is None) or (str(a).strip() == "") or (a == []))
        }

        # Operadores de comparación
        operators = {
            "==": operator.eq, "!=": operator.ne,
            ">=": operator.ge, "<=": operator.le,
            ">": operator.gt, "<": operator.lt,
        }
        expr = expr.strip()
        
        # 1. Métodos personalizados: Path.method('arg')
        #pattern = r"^([A-Za-z_][\w.]*?)\.(\w+)\(\s*['\"]([^'\"]*)['\"]?\s*\)$"
        #pattern = r"^([A-Za-z_][\w.]*?)\.(\w+)\(\s*(?:['\"]([^'\"]*)['\"])?\s*\)$"
        pattern = r"^([A-Za-z_][\w.]*?)\.(\w+)\(\s*(?:['\"]?([^'\"]*)['\"]?)?\s*\)$"
        m = re.match(pattern, expr)
        if m:
            path, method_name, arg = m.groups()
            value = get_value(path)

            # Métodos sin argumento (como .isEmpty())
            if method_name.lower() == "isempty":
                return (value is None) or (str(value).strip() == "") or (value == [])

            if method_name.lower() == "isnotempty":
                return not ((value is None) or (str(value).strip() == "") or (value == []))

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

def evaluate_condition_v2(condition_str, context):
    """
    Evalúa condiciones complejas con operadores, métodos simulados,
    `not`, `and`, `or` y paréntesis.
    """

    ops = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
    }

    simulated_methods = {
        "equalCaseInsensitive": lambda a, b: str(a).lower() == b.lower(),
        "beginWithCaseInsensitive": lambda a, b: str(a).lower().startswith(b.lower()),
        "endsWithCaseInsensitive": lambda a, b: str(a).lower().endswith(b.lower()),
        "contains": lambda a, b: b in str(a),
        "equalCase": lambda a, b: str(a) == b,
        "beginWith": lambda a, b: str(a).startswith(b),
        "endsWith": lambda a, b: str(a).endswith(b),
        "isEmpty": lambda a: (a is None) or (str(a).strip() == "") or (a == []),
        "isNotEmpty": lambda a: not ((a is None) or (str(a).strip() == "") or (a == []))
    }

    def get_value_from_path(path):
        path = path.replace("DATA.","")
        path = path.replace("Current.","")
        parts = path.strip().split('.')
        val = context
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                raise KeyError(f"No se encontró '{path}' en el contexto.")
        return val

    def eval_single(expr):
        expr = expr.strip()

        # Evalúa métodos simulados
        for method_name, method_func in simulated_methods.items():
            pattern = f".{method_name}("
            if pattern in expr:
                try:
                    field_part, arg = expr.split(pattern, 1)
                    field = field_part.strip()
                    expected = arg.strip().rstrip(")").strip('"').strip("'")
                    actual = get_value_from_path(field)
                    return method_func(actual, expected)
                except Exception as e:
                    raise ValueError(f"Error evaluando {method_name}: {expr} → {e}")

        # Evalúa operadores normales
        for op_str, op_func in ops.items():
            if op_str in expr:
                left, right = expr.split(op_str, 1)
                left = left.strip()
                right = right.strip().strip('"').strip("'")
                actual_value = get_value_from_path(left)
                return op_func(str(actual_value), right)

        # Evalúa condición booleana directa
        val = get_value_from_path(expr)
        return bool(val)

    def safe_eval(expr):
        expr = expr.strip()
        if expr.startswith("not "):
            inner = expr[4:].strip()
            return not safe_eval(inner)
        elif expr.startswith("(") and expr.endswith(")"):
            return safe_eval(expr[1:-1])
        else:
            return eval_single(expr)

    def split_and_or(expression):
        """
        Divide la expresión preservando paréntesis (anidación).
        Retorna tokens conectados por `and` / `or`.
        """
        tokens = []
        depth = 0
        token = ''
        i = 0
        while i < len(expression):
            c = expression[i]
            if c == '(':
                depth += 1
                token += c
            elif c == ')':
                depth -= 1
                token += c
            elif depth == 0 and expression[i:i+4] == ' and':
                tokens.append(token.strip())
                token = ''
                i += 3  # saltar 'and'
            elif depth == 0 and expression[i:i+3] == ' or':
                tokens.append(token.strip())
                token = ''
                i += 2  # saltar 'or'
            else:
                token += c
            i += 1
        if token:
            tokens.append(token.strip())
        return tokens

    # Normaliza espacios
    condition_str = re.sub(r'\b(or)\b', ' or ', condition_str)
    condition_str = re.sub(r'\b(and)\b', ' and ', condition_str)

    # Manejo de `or` y `and` de forma segura
    if ' or ' in condition_str:
        parts = split_and_or(condition_str)
        return any(safe_eval(p) for p in parts)

    if ' and ' in condition_str:
        parts = split_and_or(condition_str)
        return all(safe_eval(p) for p in parts)

    return safe_eval(condition_str)