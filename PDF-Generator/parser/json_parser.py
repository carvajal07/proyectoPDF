import re
import copy
import json
import time
import importlib
from transformer.created_nodes import apply_created_nodes, set_nested_value_recursive, get_default_value
import core.constants as const

def text_replace(obj, old, new):
    if isinstance(obj, dict):
        return {k: text_replace(v, old, new) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [text_replace(elem, old, new) for elem in obj]
    elif isinstance(obj, str):
        return obj.replace(old, new)
    else:
        return obj  # no cambia nada si es int, float, bool, None, etc.

def get_nested_value(data, keys):
    """Obtiene el valor de un objeto anidado dado una lista de claves."""
    for key in keys:
        if isinstance(data, list):
            # Si es una lista, asumimos que queremos el primer elemento
            data = data[0] if data else None
        elif isinstance(data, dict):
            data = data.get(key, None)
        else:
            return None
    return data

def get_nested_value(data, path):
    """
    Navega por una estructura de datos anidada (dict o list) usando una ruta de cadena.
    
    Args:
        data (dict/list): La estructura de datos en la que buscar.
        path (str): La ruta del campo, por ejemplo "Records.IdUnicoCruce".
        
    Returns:
        El valor encontrado o None si no se encuentra.
    """
    keys = path.split('.')
    current_data = data
    
    for key in keys:
        if isinstance(current_data, dict):
            current_data = current_data.get(key)
        elif isinstance(current_data, list):
            # Si el path navega a una lista, asumimos que estamos buscando un campo
            # que debe ser igual en todos los elementos (como en tu caso de un array
            # que representa una sola entidad con muchos detalles).
            # En este caso, tomaremos el valor del primer elemento de la lista.
            if current_data:
                current_data = current_data[0].get(key)
            else:
                return None
        else:
            # Si en algún punto el valor no es un dict ni una list,
            # significa que la ruta no es válida.
            return None
        
        if current_data is None:
            return None
            
    return current_data

def get_nested_value_gemini(data, path):
    """
    Navega por una estructura de datos anidada (dict o list) usando una ruta de cadena.
    
    Args:
        data (dict/list): La estructura de datos en la que buscar.
        path (str): La ruta del campo, por ejemplo "Documents.IdUnico".
        
    Returns:
        El valor encontrado o None si no se encuentra.
    """
    keys = path.split('.')
    current_data = data
    
    for key in keys:
        if isinstance(current_data, dict):
            current_data = current_data.get(key)
        elif isinstance(current_data, list):
            if current_data:
                # Si la lista tiene elementos, asumimos que el primer elemento es representativo
                current_data = current_data[0].get(key)
            else:
                return None
        else:
            return None
        
        if current_data is None:
            return None
            
    return current_data

def find_parent_node(data, path):
    """
    Navega por una estructura de datos anidada para encontrar el diccionario
    inmediatamente superior a la clave final del path.

    Args:
        data (dict/list): La estructura de datos en la que buscar.
        path (str): La ruta del campo, por ejemplo "Documents.IdUnico".

    Returns:
        tuple: Una tupla con (el diccionario padre, la clave final) o (None, None).
    """
    keys = path.split('.')
    parent_data = data
    
    # Navegamos hasta el penúltimo nivel del path para obtener el padre
    for key in keys[:-1]:
        if isinstance(parent_data, dict):
            parent_data = parent_data.get(key)
        elif isinstance(parent_data, list):
            if parent_data:
                parent_data = parent_data[0].get(key)
            else:
                return None, None
        else:
            return None, None

        if parent_data is None:
            return None, None
    
    # El diccionario padre es 'parent_data', y la clave final es el último elemento del path
    return parent_data, keys[-1]

def perform_cruce_de_datos_mejorado(principal_data, secondary_data, key_a, key_b):
    """
    Realiza el cruce de datos y fusiona la estructura secundaria en la principal.

    Args:
        principal_data (list): La estructura principal (por ejemplo, los Documents).
        secondary_data (list): La estructura secundaria (por ejemplo, los Records).
        key_a (str): La clave en la estructura principal para buscar coincidencias.
        key_b (str): La clave en la estructura secundaria para buscar coincidencias.
        
    Returns:
        list: Una nueva lista con los datos de la estructura secundaria fusionados.
    """

    if not key_a or not key_b:
        print("Error: Configuración de cruce incompleta.")
        return []

    # Crear un índice de búsqueda en la estructura secundaria
    secondary_index = {}
    for item in secondary_data:
        lookup_value = get_nested_value_gemini(item, key_b)
        if lookup_value is not None:
            secondary_index[lookup_value] = item
    
    # Crear una copia de la data principal para no modificar el original
    merged_results = copy.deepcopy(principal_data)
    
    # Recorrer la copia de la estructura principal y buscar coincidencias
    for item_principal in principal_data:
        lookup_value = get_nested_value_gemini(item_principal, key_a)
        
        if lookup_value is not None and lookup_value in secondary_index:
            item_secondary = secondary_index[lookup_value]
            
            # 1. Encontrar el diccionario padre en la data principal donde se hará la fusión
            parent_node, _ = find_parent_node(item_principal, key_a)
            
            if parent_node and isinstance(parent_node, dict):
                # 2. Encontrar el diccionario de datos a fusionar en la data secundaria
                secondary_merge_node, _ = find_parent_node(item_secondary, key_b)
                
                if secondary_merge_node and isinstance(secondary_merge_node, dict):
                    # 3. Fusionar los diccionarios.
                    #    El método `update()` fusiona los diccionarios, agregando
                    #    nuevas claves o sobrescribiendo las existentes.
                    parent_node.update(secondary_merge_node)

def _recursively_join(current_node, remaining_path_parts, secondary_index, b_key_name):
    """
    Recorre recursivamente la estructura de datos y realiza el cruce.
    """
    '''
    if not remaining_path_parts:
        # Hemos llegado al final de la ruta.
        # Aquí es donde ocurre el cruce.
        
        # 1. Obtener el valor de cruce
        lookup_value = current_node.get(next_key)
        
        # 2. Lógica de cruce (left join)
        if lookup_value is not None and lookup_value in secondary_index:
            item_secondary = secondary_index[lookup_value]
            # Realizar la fusión. Por simplicidad, asumimos que 'item_secondary'
            # se fusiona directamente con 'current_node'.
            current_node.update(item_secondary)
            # Eliminar la clave de cruce si es necesario
            # del item secundario antes de la fusión.
            del current_node[next_key]
        
        return

    # La ruta aún tiene partes; seguir descendiendo en la estructura
    next_key = remaining_path_parts[0]
    
    if isinstance(current_node, dict):
        if next_key in current_node:
            next_node = current_node[next_key]
            # Si el siguiente nodo es una lista, iteramos sobre ella
            if isinstance(next_node, list):
                for element in next_node:
                    _recursively_join(element, remaining_path_parts[1:], secondary_index)
            else:
                # Si es un diccionario, continuamos la recursión normal
                _recursively_join(next_node, remaining_path_parts[1:], secondary_index)
    # Aquí puedes añadir un 'else' para manejar errores si la ruta no existe
    '''



    """
    Recorre recursivamente la estructura de datos y realiza el cruce.
    """
    # Nuevo caso base: la ruta tiene solo una parte restante (la clave de cruce).
    # 'current_node' ahora es el nodo padre.
    if len(remaining_path_parts) == 1:
        final_key = remaining_path_parts[0]
        
        if isinstance(current_node, dict) and final_key in current_node:
            lookup_value = current_node[final_key]
            
            # Lógica de cruce (left join)
            if lookup_value is not None and lookup_value in secondary_index:
                item_secondary = secondary_index[lookup_value]
                
                # Se fusiona el 'item_secondary' con el 'current_node' (el nodo padre).
                # Se eliminan las claves de cruce del secundario si es necesario.
                if b_key_name in item_secondary:
                     del item_secondary[b_key_name]
                
                current_node.update(item_secondary)
            else:
                # Caso SIN coincidencia: se agrega la plantilla vacía.
                pass
                #current_node.update(b_empty_template)
        
        return # Termina la recursión aquí.

    # Lógica de descenso en la estructura (se mantiene igual)
    next_key = remaining_path_parts[0]
    
    if isinstance(current_node, dict) and next_key in current_node:
        next_node = current_node[next_key]
        
        if isinstance(next_node, list):
            for element in next_node:
                _recursively_join(element, remaining_path_parts[1:], secondary_index, b_key_name)
        else:
            _recursively_join(next_node, remaining_path_parts[1:], secondary_index, b_key_name)
    # Aquí iría el manejo de errores si la ruta no existe

def perform_cruce_de_datos_con_left_join(a_data, b_data, a_key_path, b_key_path):
    """
    Realiza un cruce tipo "left join" de A con B. Si no hay coincidencia,
    agrega una estructura de B vacía en la data de A.

    Args:
        a_data (list): La estructura principal.
        b_data (list): La estructura secundaria.
        a_key_path (str): La ruta a la clave de cruce en A.
        b_key_path (str): La ruta a la clave de cruce en B.
        b_structure_template_xml (str): El XML con la definición de la estructura de B.
        
    Returns:
        list: Una nueva lista con los datos de B fusionados en A.
    """
    if not a_key_path or not b_key_path:
        print("Error: Las rutas de las claves de cruce están incompletas.")
        return []

    # 1. Crear un índice de búsqueda en la estructura secundaria para un acceso rápido
    secondary_index = {}
    for item in b_data:
        lookup_value = get_nested_value(item, b_key_path)
        if lookup_value is not None:
            secondary_index[lookup_value] = item
    
    ###PRUEBAS###
    # LLenar secundary_index
    secondary_index['EPM'] = {
        "IdUnicoCruce":"dsag",
        "Direccion2": "190665200319905000",
        "Ciudad2": "Turbo"
    }

    b_empty_template = {}
    
    # 4. Recorrer la copia de la estructura principal y buscar coincidencias
    b_field_name = b_key_path.split('.')[-1]
    a_key_path_parts = a_key_path.split('.')
    for item_principal in a_data:
        register = {}
        register["Documents"] = item_principal
        _recursively_join(register, a_key_path_parts, secondary_index, b_field_name)
        
        '''
        lookup_value = get_nested_value(register, a_key_path)
        
        # Encontrar el diccionario padre en la data principal donde se hará la fusión
        parent_node, _ = find_parent_node(register, a_key_path)
        
        if parent_node and isinstance(parent_node, dict):
            # 5. Lógica de cruce (left join)
            if lookup_value is not None and lookup_value in secondary_index:
                # Caso de coincidencia: obtener el item de B y fusionarlo
                item_secondary = secondary_index[lookup_value]
                # Eliminar el campo de cruce
                del item_secondary[b_field_name]

                # Encontrar el nodo de datos a fusionar en la data secundaria
                #secondary_merge_node, _ = find_parent_node(item_secondary, b_key_path)

                parent_node.update(item_secondary)
            else:
                # Caso SIN coincidencia: agregar la plantilla vacía de B
                pass
                #parent_node.update(b_empty_template)
        '''

def get_nested_valuesV2(json_obj, dot_name, array_mode=None):
    """
    Obtiene todas las referencias (padre y clave) donde aplicar una transformación.

    - array_mode: "first", "last", o None. Si se usa, solo se aplica sobre el ÚLTIMO nivel lista encontrado.
    """
    parts = dot_name.split(".")
    results = []

    def recurse(obj, remaining_parts, apply_array_mode=False):
        if not remaining_parts:
            return

        current_key = remaining_parts[0]
        rest = remaining_parts[1:]

        if isinstance(obj, list):
            items = obj
            if apply_array_mode:
                if array_mode == "first":
                    items = obj[:1]
                elif array_mode == "last":
                    items = obj[-1:]
            for item in items:
                recurse(item, remaining_parts, apply_array_mode)

        elif isinstance(obj, dict):
            if current_key in obj:
                next_obj = obj[current_key]
                is_last_level = len(rest) == 0
                if is_last_level:
                    results.append((obj, current_key))
                else:
                    # Solo aplicar array_mode si el próximo objeto es una lista y estamos en el penúltimo nivel
                    next_is_array = isinstance(next_obj, list)
                    recurse(next_obj, rest, apply_array_mode=next_is_array and len(rest) == 1)

    recurse(json_obj, parts)
    return results

def get_nested_values(json_obj, dot_name):
    """Obtiene todas las referencias (padre y clave) donde aplicar una transformación."""
    parts = dot_name.split(".")
    results = []

    def recurse(obj, remaining_parts):
        if not remaining_parts:
            return

        current_key = remaining_parts[0]
        rest = remaining_parts[1:]

        if isinstance(obj, list):
            for item in obj:
                recurse(item, remaining_parts)
        elif isinstance(obj, dict):
            if current_key in obj:
                if not rest:
                    results.append((obj, current_key))
                else:
                    recurse(obj[current_key], rest)

    recurse(json_obj, parts)
    return results

def format_number_string(input_str, props):
    """
    Formatea un string numérico de acuerdo a las propiedades dadas.

    Args:
        input_str (str): El string de entrada a formatear.
        props (dict): Un diccionario de propiedades de formateo extraídas del XML.

    Returns:
        str: El string formateado.
    """
    if not isinstance(input_str, str) or not input_str:
        if props.get('EmptyOutput') == 'LikePrintNet3':
            return ""
        return ""

    # Pre-procesamiento: Limpiar el string para que sea un número válido
    # Eliminar separadores de miles de la entrada si existen
    temp_str = re.sub(r'[\s\.,]', '', input_str.strip())
    # Reemplazar el separador decimal de entrada por un punto para la conversión
    temp_str = temp_str.replace(props.get('InDecimalSeparator', '.'), '.', 1)
    
    # Manejar el caso de un string que no es un número (ej. "-", "abc")
    try:
        num = float(temp_str)
    except (ValueError, TypeError):
        # Si no se puede convertir a float, el valor de salida es vacío
        if props.get('EmptyOutput') == 'LikePrintNet3':
            return ""
        return input_str # O devolver el string original, dependiendo de la lógica exacta

    # Lógica de formateo del número
    sign = ""
    if num < 0:
        sign = "-"
        num = abs(num)
    elif props.get('OutPrintPlus') != 'Never' and num > 0:
        sign = "+"

    # Convertir el número a un string con el número correcto de decimales
    out_digits_after_decimal = props.get('OutDigitsAfterDecimal', 0)
    formatted_decimal = f"{num:.{out_digits_after_decimal}f}"
    
    # Separar la parte entera y la decimal
    if '.' in formatted_decimal:
        parts = formatted_decimal.split('.')
        integer_part = parts[0]
        decimal_part = parts[1]
    else:
        integer_part = formatted_decimal
        decimal_part = ""

    # Aplicar separador de miles de salida
    out_group_separator = props.get('OutGroupSeparator', '.')
    integer_part_with_groups = ""
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            integer_part_with_groups = out_group_separator + integer_part_with_groups
        integer_part_with_groups = digit + integer_part_with_groups

    # Juntar todo de nuevo con el separador decimal de salida
    final_output = integer_part_with_groups
    out_decimal_separator = props.get('OutDecimalSeparator', ',')
    if decimal_part:
        final_output += out_decimal_separator + decimal_part
    
    # Aplicar padding (la lógica de "Blank" no se especifica, se asume no hacer nada)
    out_digits_before_decimal = props.get('OutDigitsBeforeDecimal', 0)
    if out_digits_before_decimal > 0:
        # Se agrega padding si la parte entera es más corta que el número de digitos
        padding_length = out_digits_before_decimal - len(integer_part_with_groups.replace(out_group_separator, ''))
        if padding_length > 0:
            final_output = (" " * padding_length) + final_output

    # Aplicar la posición del signo
    if props.get('OutSignPosition') == 'Sign before number':
        final_output = sign + final_output
    elif props.get('OutSignPosition') == 'Sign after number':
        final_output = final_output + sign
    
    # Manejar el caso del valor cero
    if num == 0 and props.get('PrintZeroValue') == 'Input Dependent':
        # La lógica "Input Dependent" para cero es compleja sin más información.
        # Asumimos que si la entrada era un cero, la salida será "0" formateado.
        pass

    return final_output

def apply_transformation(full_register,transformation_class,field_path_to_transform,fcv_props):
    fields = get_nested_values(full_register, field_path_to_transform)
    
    for parent, key in fields:
        original_value = parent.get(key)
        # Manipulacion simple de string
        if transformation_class == "ConcatStrFCV":
            manipulation_type = fcv_props.find("Type").text
            # Concatenar string
            if manipulation_type == "Concatenation":
                from transformer.concatenated_string import concat_str
                pre = fcv_props.find("PreString").text or ""
                post = fcv_props.find("PostString").text or ""                                                
                parent[key] = concat_str([pre, original_value, post])
            # Convertir a mayusculas, minusculas, capitalizar
            elif manipulation_type == "SimpleCaseConversion":
                from transformer.case_converter import convert_string
                case_type = fcv_props.find("CaseType").text
                parent[key] = convert_string(original_value, case_type)
        elif transformation_class == "ConvNumFCV":
            props = {}
            props['InDecimalSeparator'] = fcv_props.findtext('InDecimalSeparator', default='.')
            props['OutDecimalSeparator'] = fcv_props.findtext('OutDecimalSeparator', default=',')
            props['OutGroupSeparator'] = fcv_props.findtext('OutGroupSeparator', default='.')
            props['OutDigitsAfterDecimal'] = int(fcv_props.findtext('OutDigitsAfterDecimal', default='0'))
            props['OutDigitsBeforeDecimal'] = int(fcv_props.findtext('OutDigitsBeforeDecimal', default='0'))
            props['OutPadding'] = fcv_props.findtext('OutPadding', default='Blank')
            props['OutSignPosition'] = fcv_props.findtext('OutSignPosition', default='Sign before number')
            props['PrintZeroValue'] = fcv_props.findtext('PrintZeroValue', default='Input Dependent')
            props['EmptyOutput'] = fcv_props.findtext('EmptyOutput', default='LikePrintNet3')
            parent[key] = format_number_string(original_value, props)
            
        elif transformation_class == "ScriptFCV":
            # Omitirlo en una version inicial (Script en datatransformer)
            pass
        elif transformation_class == "StackFCV":
            stack_children = list(fcv_props)
            # Iterar con un índice para poder acceder al siguiente elemento (FCVProps)
            for i in range(len(stack_children)):
                element = stack_children[i]

                # Procesar solo si el elemento actual es FCVClassName
                if element.tag == 'FCVClassName':
                    transformation_class_stack = element.text.strip()

                    # El siguiente elemento DEBE ser el FCVProps que le corresponde
                    if i + 1 < len(stack_children) and stack_children[i + 1].tag == 'FCVProps':
                        fcv_props_stack = stack_children[i + 1]

                        apply_transformation(full_register,transformation_class_stack,field_path_to_transform,fcv_props_stack)
                        
            
        elif transformation_class == "TextReplaceFCV":
            pass
            '''
            from transformer.text_replace_fcv import text_replace
            key = fcv_props.find("Key").text
            value = fcv_props.find("Value").text
            if key and value:
                parent[key] = text_replace(original_value, key, value)
            else:
                raise ValueError("El campo 'Key' y 'Value' deben estar presentes en TextReplaceFCV")
            '''
        
        elif transformation_class == "CaseConvFCV":
            pass

def parse_workflow_definition(workflow_definition_node):
    """
    Parsea la sección <WorkFlowDefinition> de un elemento raíz XML y construye un diccionario
    Python que representa su estructura, teniendo en cuenta el atributo 'Optionality'.

    Args:
        xml_root_element (ET.Element): El elemento raíz del XML ya parseado.

    Returns:
        dict: Un diccionario Python que representa la estructura de salida,
              o None si no se encuentra la sección WorkFlowDefinition.
    """
    
    if workflow_definition_node is None:
        return None

    output_structure = {}

    def process_node(node_element, current_dict_or_list):
        """Función recursiva para procesar nodos XML y construir la estructura del diccionario."""
        node_name = node_element.get("Name")
        node_type = node_element.get("Type")
        node_optionality = node_element.get("Optionality") # Obtener el atributo Optionality

        # Si el nodo es el "SubTree" raíz de WorkFlowDefinition sin nombre,
        # simplemente procesa sus hijos.
        if node_name == "" and node_type == "SubTree":
            for child in node_element:
                process_node(child, current_dict_or_list)
            return

        # Determinar si debe ser un array basándose en Optionality, si está presente y es "Array"
        should_be_array = (node_optionality == "Array")

        if should_be_array:
            # Si debe ser un Array, creamos una lista para ese nombre de nodo
            item_template = {}
            for child in node_element:
                process_node(child, item_template) # Recursivamente procesar hijos para la plantilla
            
            # Asegurarse de que el elemento template no esté vacío si no hay hijos
            if not item_template and not list(node_element): # Si no tiene hijos y item_template está vacío, es un array de algo simple
                # Esto es un caso raro, pero si un "Array" no tiene hijos, se puede asumir un array de None
                item_template = None 

            if isinstance(current_dict_or_list, dict):
                if node_name:
                    current_dict_or_list[node_name] = [item_template]
                else: # Si es un array sin nombre, sus hijos son los elementos directos
                    current_dict_or_list.append(item_template) # Agrega la plantilla como un elemento en la lista
            elif isinstance(current_dict_or_list, list) and current_dict_or_list:
                # Si ya estamos dentro de un array (ej. el elemento de un RecordsServicios),
                # y encontramos otro array anidado, el nombre del nodo será la clave
                # dentro del diccionario del elemento actual.
                if node_name:
                    current_dict_or_list[0][node_name] = [item_template] 
                else: # Array anidado sin nombre
                    current_dict_or_list[0].append(item_template)
            else:
                # Manejar otros casos, si es un array sin un contexto claro de dict/list padre
                if node_name:
                    current_dict_or_list[node_name] = [item_template]
                else:
                    current_dict_or_list.append(item_template)


        elif node_type == "SubTree":
            # Si es un SubTree y NO es un Array por Optionality, creamos un diccionario
            if node_name: # Si el subarbol tiene nombre
                current_dict_or_list[node_name] = {}
                for child in node_element:
                    process_node(child, current_dict_or_list[node_name])
            else: # Si es un subarbol sin nombre (ej. el nodo raíz dentro de WorkFlowDefinition)
                for child in node_element:
                    process_node(child, current_dict_or_list)

        else:
            # Para tipos de datos primitivos (String, Int, etc.) y NO es un Array por Optionality
            if node_name: # Asegurarse de que el nodo tiene un nombre para ser una clave
                if node_type == "Int":
                    current_dict_or_list[node_name] = 0
                else: # String, etc.
                    current_dict_or_list[node_name] = ""
    
    # Iniciar el procesamiento desde el nodo principal dentro de WorkFlowDefinition
    if workflow_definition_node:
        for child_node in workflow_definition_node:
            process_node(child_node, output_structure)

    return output_structure


def apply_script(script_str, input_value, full_context):
    """Aplica un script muy simple en Python simulado"""
    # Convertir pseudo-script a Python (muy limitado, para demostración)
    # ejemplo: if(Input.containsCaseInsensitive("#")){ return "<t>"+Input; }
    script_str = script_str.replace("&quot;", '"').replace("&#xd;&#xa;", "\n")
    script_str = script_str.replace("Input.containsCaseInsensitive", '"#" in Input.lower()')
    script_str = re.sub(r'\bInput\b', f'"{input_value}"', script_str)
    script_str = re.sub(r'\breturn\b', 'result =', script_str)
    try:
        local_vars = {"Input": input_value}
        exec(script_str, {}, local_vars)
        return local_vars.get("result", input_value)
    except Exception as e:
        print("Script error:", e)
        return input_value

def extract_stack_fcv(fcv_props):
    """Extrae lista de FCV anidados de un StackFCV"""
    # Este método depende de cómo recibas el XML convertido a dict
    # Suponemos que es una lista anidada, no una estructura embebida con mismo key repetido
    stack = []
    for key, value in fcv_props.items():
        if isinstance(value, dict) and "FCVClassName" in value:
            stack.append(value)
    return stack

def apply_single_fcv(value, fcv, context):
    """Aplica una sola transformación FCV"""
    cls = fcv['FCVClassName']
    props = fcv.get('FCVProps', {})

    if cls == "ConcatStrFCV":
        pre = props.get("PreString", "")
        post = props.get("PostString", "")
        return f"{pre}{value}{post}"

    elif cls == "ConvNumFCV":
        try:
            number = float(value)
            return f"{number:,.0f}".replace(",", ".")
        except:
            return value

    elif cls == "ScriptFCV":
        return apply_script(props.get("Script", ""), value, context)

    return value

def get_nodes(module):
    special_nodes = []
    new_nodes = []
    created_nodes = module.find("CreatedNodes")
    for node in created_nodes:
        linked_type = node.attrib.get("LinkedType", "")
        if linked_type == "Special":
            special_nodes.append(node)
        else:
            new_nodes.append(node)
    return special_nodes, new_nodes

def get_nested_values_for_path(json_obj, dot_name):
    """Retorna los objetos que contienen el key final del path, incluyendo arrays anidados."""
    parts = dot_name.split(".")
    results = []

    def recurse(obj, remaining_parts):
        if not remaining_parts:
            return

        current_key = remaining_parts[0]
        rest = remaining_parts[1:]

        if isinstance(obj, list):
            for item in obj:
                recurse(item, remaining_parts)
        elif isinstance(obj, dict):
            if current_key in obj:
                child = obj[current_key]
                if not rest:
                    # Si el último nivel es una lista, devolvemos cada elemento individualmente
                    if isinstance(child, list):
                        for i, el in enumerate(child):
                            results.append((child, i))  # ← para acceder como lista[index]
                    else:
                        results.append((obj, current_key))
                else:
                    recurse(child, rest)

    recurse(json_obj, parts)
    return results

def get_nested_value_gemini(data_structure, source_parts, index_type="first"):
    """
    Obtiene un valor anidado de una estructura de datos dado un camino.
    Maneja la selección del primer o último elemento de un array si no se especifica un índice.

    Args:
        data_structure (dict or list): La estructura de datos actual.
        source_parts (list): Una lista con las partes de la ruta de origen.
        index_type (str): 'first' para el primer elemento de una lista, 'last' para el último.
                          Por defecto es 'first'.
    Returns:
        any: El valor encontrado, o None si la ruta no existe o es inválida.
    """
    current_data = data_structure
    
    for i, part in enumerate(source_parts):
        if current_data is None:
            return None

        if isinstance(current_data, dict):
            if part in current_data:
                current_data = current_data[part]
            else:
                return None # La clave no existe
        elif isinstance(current_data, list):
            if not current_data: # Lista vacía
                return None
            
            if index_type == "first":
                current_data = current_data[0]
            elif index_type == "last":
                current_data = current_data[-1]
            else:
                return None # Tipo de índice inválido
            
            # Si después de seleccionar un elemento de la lista, es el último 'part' de source_parts,
            # y ese 'part' se refiere a una clave dentro del elemento seleccionado,
            # necesitamos asegurarnos de que el siguiente paso del bucle `for` lo capture.
            # No hay cambio aquí; el bucle `for` naturalmente continuará con `current_data`
            # siendo el elemento de la lista y procesando la siguiente 'part'.

        else: # Si el tipo no es dict ni list
            return None 
            
    # CRÍTICO: Una vez que el bucle for termina, 'current_data' tiene el VALOR FINAL.
    # Anteriormente, 'current_data' podría ser el diccionario que contenía el valor final.
    # Por ejemplo, si source_parts era ['a', 'b', 'c'], al final del bucle,
    # current_data sería el valor de 'c'. Si era ['a', 'b'], sería el diccionario 'b'.

    # El problema es que si el source_path_template termina en un campo dentro de un diccionario,
    # como "tres.ValorDetalleDescuento", cuando el bucle finaliza, 'current_data' ya es el valor de
    # 'ValorDetalleDescuento'.
    # Si source_parts era ['tres'], y queremos el objeto completo del primer/último 'tres',
    # entonces el 'current_data' al final del bucle ya es el objeto.

    # Re-evaluando la ruta. La lógica del bucle `for` para `get_nested_value` ya es correcta.
    # El valor final se asigna a `current_data` en cada paso. Si la ruta es 'tres.ValorDetalleDescuento',
    # 'current_data' se vuelve la lista 'tres', luego el elemento seleccionado de 'tres' (un dict),
    # luego el valor de 'ValorDetalleDescuento' dentro de ese dict.

    # Si `source_parts` es, por ejemplo, `['tres', 'ValorDetalleDescuento']`:
    # 1. `i=0, part='tres'`: `current_data` se convierte en el `selected_item` (el dict dentro de `tres`).
    # 2. `i=1, part='ValorDetalleDescuento'`: `current_data` (que es el dict `selected_item`) se busca 'ValorDetalleDescuento', y `current_data` se convierte en "1valor-1".
    # 3. El bucle termina. `return current_data` devuelve "1valor-1". Esto es lo que queremos.

    # Entonces, la lógica en `get_nested_value` debería estar bien si no se sobreescribía o se retornaba
    # antes de tiempo.

    # El único escenario donde podría devolver un objeto es si la *última parte de la ruta*
    # en `source_path_template` es el nombre de un objeto y no de un campo primitivo.
    # Ejemplo: source_path_template = "tres" -> devolvería el array `tres` (si el contexto es `dos`)
    # O source_path_template = "tres.ConceptoDetalleDescuento" -> devolvería "1concepto-1"

    # Revisando el JSON de "Pruebas.json", los campos "CopyFirstOfConceptoDetalleDescuento"
    # y "CopyLAstOfValorDetalleDescuento" tienen un OBJETO completo.
    # Esto indica que `source_path_template` pudo haber sido "tres" o "tres.ConceptoDetalleDescuento"
    # cuando en realidad se esperaba el valor de "ValorDetalleDescuento".

    # Asegurémonos de que la `source_path_for_value` sea precisamente la ruta al campo STRING.
    # Por ejemplo, para el campo "ValorDetalleDescuento" dentro de "tres", la ruta es "tres.ValorDetalleDescuento".

    # Mi código anterior ya usaba "tres.ValorDetalleDescuento".
    # La única forma en que esto devuelva un objeto es si 'ValorDetalleDescuento'
    # en el JSON real fuera un objeto, no un string.
    # Según tu JSON: "ValorDetalleDescuento": "1valor-1", es un string.

    # Esto sugiere que la asignación `item[new_field_name] = dynamic_value` está bien.
    # El error debe estar en cómo se usó la función o en un test anterior.

    # Vamos a agregar una comprobación final explícita para asegurarnos de que el valor sea un string
    # o de convertirlo si es un número/booleano, o a string JSON si es un objeto/lista.
    # Si SIEMPRE debe ser un string, podemos forzarlo.
    if not isinstance(current_data, (str, int, float, bool)) and current_data is not None:
        # Si no es un tipo primitivo y no es None, convertir a string JSON
        try:
            name = source_parts[-1]  # Última parte de la ruta
            valor = current_data[name]
            return valor
        except TypeError:
            # Si no es serializable a JSON (ej. un objeto Python complejo), forzar str()
            return str(current_data)
    
    return current_data

def add_field_with_dynamic_value(data_structure, target_path_parts, new_field_name, source_path_template, index_type_for_source="first"):
    """
    Agrega un nuevo campo a cada registro en arrays anidados, creando la ruta si no existe.
    El valor del nuevo campo se obtiene de otra parte de la misma estructura,
    relativa al contexto actual.

    Args:
        data_structure (dict or list): La estructura de datos actual (diccionario o lista).
        target_path_parts (list): Una lista con las partes restantes de la ruta destino.
        new_field_name (str): El nombre del nuevo campo a agregar.
        source_path_template (str): La ruta relativa (desde el contexto actual) para obtener el valor.
                                     Ejemplo: "tres.ValorDetalleDescuento"
        index_type_for_source (str): 'first' o 'last' para seleccionar elementos de arrays en la ruta de origen.
    """
    if not target_path_parts:
        return

    current_target_key = target_path_parts[0]
    remaining_target_path = target_path_parts[1:]

    if isinstance(data_structure, dict):
        # Crear la clave si no existe
        if current_target_key not in data_structure:
            if len(remaining_target_path) > 0:
                 data_structure[current_target_key] = []
            else:
                 data_structure[current_target_key] = {}

        # Navegar o agregar el campo
        if remaining_target_path:
            add_field_with_dynamic_value(
                data_structure[current_target_key], remaining_target_path, new_field_name, source_path_template, index_type_for_source
            )
        else:
            # Hemos llegado al punto de inserción (data_structure[current_target_key])
            if isinstance(data_structure[current_target_key], dict):
                source_parts = source_path_template.split('.')
                dynamic_value = get_nested_value_gemini(data_structure[current_target_key], source_parts, index_type_for_source)
                data_structure[current_target_key][new_field_name] = dynamic_value
            elif isinstance(data_structure[current_target_key], list):
                for item in data_structure[current_target_key]:
                    if isinstance(item, dict):
                        source_parts = source_path_template.split('.')
                        dynamic_value = get_nested_value_gemini(item, source_parts, index_type_for_source)
                        item[new_field_name] = dynamic_value
    
    elif isinstance(data_structure, list):
        for item in data_structure:
            if isinstance(item, (dict, list)):
                add_field_with_dynamic_value(item, target_path_parts, new_field_name, source_path_template, index_type_for_source)

#Agrega los campos correctamente en cualquier parte de la estructura de datos
def add_field_to_nested_array_V1(data_structure, path_parts, new_field_name, new_field_value):
    """
    Agrega un nuevo campo a cada registro en arrays anidados, creando la ruta si no existe.

    Args:
        data_structure (dict or list): La estructura de datos actual (diccionario o lista).
        path_parts (list): Una lista con las partes restantes de la ruta.
        new_field_name (str): El nombre del nuevo campo a agregar.
        new_field_value: El valor del nuevo campo.
    """
    if not path_parts:
        return

    current_key = path_parts[0]
    remaining_path = path_parts[1:]

    if isinstance(data_structure, dict):
        # Si la clave actual no existe, la creamos.
        # Determinamos si lo siguiente en la ruta debería ser una lista o un diccionario.
        if current_key not in data_structure:
            # Si no quedan más partes después de la actual (significa que current_key es el contenedor final),
            # y el nuevo campo es lo que se va a agregar, entonces este current_key debería ser un diccionario.
            # Si la siguiente parte es el campo a insertar, y este es un diccionario, entonces current_key es el contenedor.
            # PERO si current_key es uno de los nombres de "arrays" (Documents, uno, dos, tres),
            # entonces el valor asociado DEBE ser una lista para poder iterar sobre ella y añadir el campo a CADA elemento.
            # Esta es la parte más tricky: cómo sabemos si current_key debe ser una lista o un diccionario cuando se crea.
            # Para tu caso: Documents, uno, dos, tres son arrays. Asumiremos que si el *siguiente* elemento en path_parts
            # es un nombre de un "array" que espera contener múltiples elementos, entonces el valor debe ser una lista.
            # En nuestro path "Documents.uno.dos.tres", todos son nombres de arrays (listas de diccionarios).
            
            # Si remaining_path no está vacío, el siguiente elemento determinará el tipo.
            # Si el último elemento de remaining_path (el que precede al new_field_name) es un "array",
            # el contenedor debería ser una lista de diccionarios.

            # Simplificamos: para esta ruta específica, todos los niveles intermedios son listas de diccionarios.
            # Entonces, si current_key no existe y es un nivel intermedio, lo creamos como una lista.
            # Si current_key es el *último* nivel antes de new_field_name, lo creamos como un diccionario.
            if len(remaining_path) > 0: # Si aún hay más partes, esta clave intermedia debe apuntar a una lista para recorrer
                data_structure[current_key] = ""
            else: # Si esta es la última clave antes del campo final, debe ser un diccionario
                data_structure[current_key] = ""


        # Ahora que sabemos que current_key existe (o la hemos creado)
        if remaining_path:
            # Si hay más partes en la ruta, sigue descendiendo
            add_field_to_nested_array_V1(
                data_structure[current_key], remaining_path, new_field_name, new_field_value
            )
        else:
            # Si es la última parte de la ruta y es un diccionario, añade el campo directamente
            # Esta lógica solo se ejecutará si data_structure[current_key] es un diccionario,
            # lo cual es el caso si 'current_key' fue el *último* elemento de path_parts.
            # Ejemplo: data_structure = {'tres': {}}, current_key = 'tres', new_field_name = 'NuevoCampo'
            if isinstance(data_structure[current_key], dict):
                data_structure[current_key][new_field_name] = new_field_value
            elif isinstance(data_structure[current_key], list):
                # Esto es crucial: si el último elemento del path es un array (como 'tres' en tu ejemplo),
                # el campo 'NuevoCampo' debe agregarse a CADA diccionario dentro de ese array.
                for item in data_structure[current_key]:
                    if isinstance(item, dict):
                        item[new_field_name] = new_field_value
                    # Si un elemento no es un dict (es un tipo primitivo), lo ignoramos,
                    # ya que no podemos agregarle un campo.
    
    elif isinstance(data_structure, list):
        # Cuando estamos en una lista, iteramos sobre cada elemento.
        # Cada elemento debe ser procesado como si fuera el inicio de una nueva rama.
        for item in data_structure:
            if isinstance(item, (dict, list)):
                # Si el elemento es un diccionario o una lista, sigue la recursión
                # Pasamos las MISMAS path_parts, porque cada elemento de la lista debe seguir la misma ruta.
                add_field_to_nested_array_V1(item, path_parts, new_field_name, new_field_value)
            # Si el elemento es un tipo de dato básico, no podemos descender más por este camino.


def perform_cruce_de_datos(a_data, b_data, key_a, key_b):
    """
    Realiza el cruce de datos entre dos estructuras.

    Args:
        a_data (list): La estructura principal (por ejemplo, los Documents).
        a_data (list): La estructura secundaria (por ejemplo, los Records).
        key_a (str): La clave en la estructura principal para buscar coincidencias.
        key_b (str): La clave en la estructura secundaria para buscar coincidencias.
        
    Returns:
        list: Una lista de diccionarios con los datos cruzados.
    """

    if not key_a or not key_b:
        print("Error: Configuración de cruce incompleta.")
        return []

    # Crear un índice de búsqueda en la estructura secundaria para un acceso rápido O(1)
    secondary_index = {}
    for item in b_data:
        lookup_value = get_nested_value(item, key_b)
        if lookup_value is not None:
            secondary_index[lookup_value] = item
    
    joined_results = []
    
    # Recorrer la estructura principal y buscar coincidencias
    for item_principal in a_data:
        lookup_value = get_nested_value(item_principal, key_a)
        
        if lookup_value is not None and lookup_value in secondary_index:
            item_secondary = secondary_index[lookup_value]
            
            # Combina los datos de ambas estructuras
            # Aquí puedes decidir cómo fusionar los datos.
            # Por simplicidad, los unimos en un nuevo diccionario.
            joined_item = {
                "principal": item_principal,
                "secundaria": item_secondary
            }
            joined_results.append(joined_item)
            
    return joined_results

def json_parser(json_path, all_elements_workflow, elements_to_preprocess, connections):
    # Leer JSON desde disco
    with open(json_path, 'r', encoding="UTF-8") as f:
        json_data = json.load(f)

    docs = json_data.get(const.PRINCIPAL_ARRAY)
    # Se realiza validación de los documentos para verificar si son una lista o un diccionario para poder recorrerlo
    if isinstance(docs, dict):
        documents = [docs]  # Lo convertimos a lista
    elif isinstance(docs, list):
        documents = docs
    else:
        raise ValueError("Formato de 'Documents' no reconocido")

    full_context = json_data.copy()
    full_context["Documents"] = documents
    output_structures = {}

    #Realizar el proceso de los modulos que se deben preprocesar
    for element in elements_to_preprocess:
        if element in all_elements_workflow:
            module = all_elements_workflow[element]
            module_id = module.find("Id").text
            module_name = module.find("Name").text
            module_type = module.tag
            if module is not None:
                if module_type == "DataTransformer":                                        
                    special_nodes,new_nodes = get_nodes(module)

                    for node in new_nodes:
                        field_dot_name = node.attrib["FieldDotName"]
                        field_name = field_dot_name.split(".")[-1]
                        node_type = node.attrib["Type"]
                        default_value = node.attrib.get("DefaultValue", "")
                        add_field_to_nested_array_V1(
                            full_context, 
                            field_dot_name.split("."), 
                            field_name, 
                            get_default_value(node_type, default_value)
                        )
                    
                    for register in full_context["Documents"]:
                        full_register = {}
                        full_register["Documents"] = register 
                        transformations = module.find("Transformations")

                        #Realizar la creacion de los nuevos campos especiales
                        for special_node in special_nodes:
                            field_dot_name = special_node.attrib["FieldDotName"]
                            field_name = field_dot_name.split(".")[-1]
                            parent_dot_name = special_node.attrib["ParentDotName"]
                            linked_to_dot_name = special_node.attrib["LinkedToDotName"]
                            #tomar solo las dos ultimar partes de linked_to_dot_name
                            linked_to_dot_name = ".".join(linked_to_dot_name.split(".")[-2:])  # Tomar solo las dos últimas partes
                            operation = special_node.attrib["Operation"]                            
                            array_mode = "first" if operation == "CopyFirstValueLevelUp" else "last"
                            add_field_with_dynamic_value(
                                full_register,
                                parent_dot_name.split("."),
                                field_name,
                                linked_to_dot_name,
                                array_mode   
                            )                                                                            
                            

                        for transformation in transformations:
                            transformation_class = transformation.find("FCVClassName").text
                            field_path_to_transform = transformation.get('DotName')
                            fcv_props = transformation.find('FCVProps')
                            apply_transformation(full_register,transformation_class,field_path_to_transform,fcv_props)

                    
                elif module_type == "DataFilter":
                    pass
                elif module_type == "ScriptedSheeter":
                    # Solo realizar la creacion de la estructura de datos
                    workflow_definition = module.find("WorkFlowDefinition")
                    output_structures[module_id] = parse_workflow_definition(workflow_definition)
                elif module_type == "CustCode":
                    # Realizar el cruce de datos
                    selected_none_a = module.find("SelectedNodeA")
                    selected_none_b = module.find("SelectedNodeB")
                    if selected_none_a is None or selected_none_b is None:
                        print("Error: No se encontraron nodos seleccionados en CustCode")
                        continue
                    full_path_a = selected_none_a.get("FullPathName")
                    full_path_b = selected_none_b.get("FullPathName")                  
                    
                    a_data = full_context.get("Documents", [])
                    
                    '''
                    <Connect>
                        <From>ScriptedSheeter1</From>
                        <FromIndex>0</FromIndex>
                        <To>CustCode1</To>
                        <ToIndex>1</ToIndex>
                    </Connect>
                    '''
                    from_module_id = ""
                    if not module_id:
                        print("Error: No se encontró el ID del módulo CustCode")
                        continue
                    # Buscar el id del modulo que ingresa con la estructura B, este lo valido de los nodos Connect
                    # EL id lo obtengo buscando en los nodos Connect donde TO sea igual al id del modulo CustCode y el ToIndex sea 1
                    for connect in connections:
                        if connect.find("To").text == module_id and connect.find("ToIndex").text == "1":
                            from_module_id = connect.find("From").text
                            break

                    b_name_array = full_path_b.split(".")[0]

                    b_data = output_structures.get(from_module_id, {}).get(b_name_array, [])
                    perform_cruce_de_datos_con_left_join(a_data, b_data, full_path_a, full_path_b)
                    
                    
                elif module_type == "TextReplacer":
                    field = module.find("Field")
                    if field is not None:
                        key = field.get("Key")
                        value = field.get("Value")
                        if key and value:
                            json_data = text_replace(json_data, key, value)
                        else:
                            raise ValueError("El campo 'Field' debe tener atributos 'Key' y 'Value'")
                    else:
                        raise ValueError("No se encontró el campo 'Field' en el módulo TextReplacer")

                else:
                    print(f"Tipo de módulo desconocido: {module_type}")
                    #raise ValueError(f"Tipo de módulo desconocido: {module_type}")
                with open('D:\Pruebas.json', 'w', encoding='utf-8') as f:
                    json.dump(full_context, f, ensure_ascii=False)
    return full_context, documents


#Prueba de la función json_parser
if __name__ == "__main__":
    start = time.perf_counter()
    json_path = "\\Cad-fsx-eks.cadena.com.co\c$\trident_pvc_75f19d79_8dc5_4cdb_9aa1_67e850e1425d\Inputs\20250721\54287E3F_6006_4E52_AABB_225D1EB3FB41\PE_54287E3F_6006_4E52_AABB_225D1EB3FB41_Parte1.json"

    with open(json_path, 'r', encoding="UTF-8") as f:
        json_data = json.load(f)

    all_elements_workflow = {}  # Simulación de los elementos del workflow
    elements_to_preprocess = []  # Simulación de los elementos a preprocesar

    full_context, documents = json_parser(json_path, all_elements_workflow, elements_to_preprocess)
    end = time.perf_counter()
    print(f"Tiempo de ejecución: {end - start:.2f} segundos")