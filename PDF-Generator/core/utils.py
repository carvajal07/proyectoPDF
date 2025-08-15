import re
import operator
from decimal import Decimal

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
    }

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
    condition_str = re.sub(r'\s*or\s*', ' or ', condition_str)
    condition_str = re.sub(r'\s*and\s*', ' and ', condition_str)

    # Manejo de `or` y `and` de forma segura
    if ' or ' in condition_str:
        parts = split_and_or(condition_str)
        return any(safe_eval(p) for p in parts)

    if ' and ' in condition_str:
        parts = split_and_or(condition_str)
        return all(safe_eval(p) for p in parts)

    return safe_eval(condition_str)