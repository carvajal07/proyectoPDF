import xml.etree.ElementTree as ET
import json
import copy

def parse_workflow_definition_for_template(xml_root_element):
    """
    Parsea la sección <WorkFlowDefinition> de un elemento raíz XML y construye un diccionario
    vacío (una plantilla) que representa su estructura.
    
    Esta es una versión simplificada para obtener la estructura inicial.
    
    Args:
        xml_root_element (ET.Element): El elemento raíz del XML ya parseado.

    Returns:
        dict: Un diccionario Python con la estructura de salida.
    """
    workflow_definition_node = xml_root_element.find(".//WorkFlowDefinition")
    
    if workflow_definition_node is None:
        return {}

    output_structure = {}

    def process_node(node_element, current_dict_or_list):
        node_name = node_element.get("Name")
        node_type = node_element.get("Type")
        node_optionality = node_element.get("Optionality")

        if node_name == "" and node_type == "SubTree":
            for child in node_element:
                process_node(child, current_dict_or_list)
            return

        should_be_array = (node_optionality == "Array")

        if should_be_array:
            item_template = {}
            for child in node_element:
                process_node(child, item_template)
            
            if isinstance(current_dict_or_list, dict) and node_name:
                current_dict_or_list[node_name] = [item_template]
            elif isinstance(current_dict_or_list, list):
                if node_name:
                    if current_dict_or_list:
                        current_dict_or_list[0][node_name] = [item_template]
                    else:
                        current_dict_or_list.append({node_name: [item_template]})
                else:
                    current_dict_or_list.append(item_template)
            else:
                 if node_name:
                     current_dict_or_list[node_name] = [item_template]
                 else:
                    current_dict_or_list.append(item_template)

        elif node_type == "SubTree":
            if node_name:
                current_dict_or_list[node_name] = {}
                for child in node_element:
                    process_node(child, current_dict_or_list[node_name])
            else:
                for child in node_element:
                    process_node(child, current_dict_or_list)

        else:
            if node_name:
                if node_type == "Int":
                    current_dict_or_list[node_name] = 0
                else:
                    current_dict_or_list[node_name] = ""
    
    if workflow_definition_node:
        for child_node in workflow_definition_node:
            process_node(child_node, output_structure)

    return output_structure

def get_nested_value(data, path):
    """Navega por una estructura de datos anidada para obtener un valor."""
    keys = path.split('.')
    current_data = data
    for key in keys:
        if isinstance(current_data, dict):
            current_data = current_data.get(key)
        elif isinstance(current_data, list):
            if current_data:
                current_data = current_data[0].get(key)
            else:
                return None
        else:
            return None
        if current_data is None:
            return None
    return current_data

def find_parent_node(data, path):
    """Navega por una estructura de datos anidada para encontrar el diccionario padre."""
    keys = path.split('.')
    parent_data = data
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
    return parent_data, keys[-1]


### Función de Cruce de Datos con Left Join

def perform_cruce_de_datos_con_left_join(a_data, b_data, a_key_path, b_key_path, b_structure_template_xml):
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
    
    # 2. Obtener la plantilla vacía para la estructura de B a partir del XML
    try:
        b_root_element = ET.fromstring(b_structure_template_xml)
        b_empty_template = parse_workflow_definition_for_template(b_root_element)
    except ET.ParseError as e:
        print(f"Error al parsear el XML de la plantilla: {e}")
        return copy.deepcopy(a_data) # Devuelve A sin cambios si hay un error

    # 3. Crear una copia de la data principal para no modificar el original
    merged_results = copy.deepcopy(a_data)
    
    # 4. Recorrer la copia de la estructura principal y buscar coincidencias
    for item_principal in merged_results:
        lookup_value = get_nested_value(item_principal, a_key_path)
        
        # Encontrar el diccionario padre en la data principal donde se hará la fusión
        parent_node, _ = find_parent_node(item_principal, a_key_path)
        
        if parent_node and isinstance(parent_node, dict):
            # 5. Lógica de cruce (left join)
            if lookup_value is not None and lookup_value in secondary_index:
                # Caso de coincidencia: obtener el item de B y fusionarlo
                item_secondary = secondary_index[lookup_value]
                
                # Encontrar el nodo de datos a fusionar en la data secundaria
                secondary_merge_node, _ = find_parent_node(item_secondary, b_key_path)

                if secondary_merge_node and isinstance(secondary_merge_node, dict):
                    parent_node.update(secondary_merge_node)
            else:
                # Caso SIN coincidencia: agregar la plantilla vacía de B
                parent_node.update(b_empty_template)

    return merged_results

# --- Uso del script con datos de ejemplo ---

# 1. Configuración de la estructura de B (el XML que me proporcionaste)
b_structure_xml = """
<ScriptedSheeter>
    <WorkFlowDefinition>
      <Node Name="" Type="SubTree" Optionality="MustExist">
        <Node Name="Records" Type="SubTree" Optionality="Array">
          <Node Name="IdUnicoCruce" Type="String" Optionality="MustExist"/>
          <Node Name="DetallesTablaEstadoCuenta" Type="SubTree" Optionality="Array">
            <Node Name="detalles" Type="String" Optionality="MustExist"/>
            <Node Name="valor" Type="String" Optionality="MustExist"/>
          </Node>
        </Node>
        <Node Name="RecordsServicios" Type="SubTree" Optionality="Array">
          <Node Name="ConceptoCruce" Type="String" Optionality="MustExist"/>
          <Node Name="DetallesTablaServicioConsumo" Type="SubTree" Optionality="Array">
            <Node Name="valoresFacturados" Type="String" Optionality="MustExist"/>
            <Node Name="unidad" Type="String" Optionality="MustExist"/>
            <Node Name="costo" Type="String" Optionality="MustExist"/>
            <Node Name="total" Type="String" Optionality="MustExist"/>
          </Node>
          <Node Name="DetallesTablaHistoricos" Type="SubTree" Optionality="Array">
            <Node Name="fechaRecarga" Type="String" Optionality="MustExist"/>
            <Node Name="valorUnidades" Type="String" Optionality="MustExist"/>
            <Node Name="valor" Type="String" Optionality="MustExist"/>
            <Node Name="indice" Type="Int" Optionality="MustExist"/>
          </Node>
          <Node Name="DetallesComponentesCostos" Type="SubTree" Optionality="Array">
            <Node Name="conceptoConsumo" Type="String" Optionality="MustExist"/>
            <Node Name="valorConsumo" Type="String" Optionality="MustExist"/>
          </Node>
        </Node>
      </Node>
    </WorkFlowDefinition>
</ScriptedSheeter>
"""

# 2. Datos de ejemplo para las estructuras
a_data_example = [
    {"Documents": {"IdUnico": "A123", "otros_datos": "datos_principal_1"}},
    {"Documents": {"IdUnico": "B456", "otros_datos": "datos_principal_2"}},
    {"Documents": {"IdUnico": "C789", "otros_datos": "datos_principal_3"}} # Este no tiene coincidencia
]

b_data_example = [
    {"Records": {"IdUnicoCruce": "A123", "datos_secundarios": "info_secundaria_1", "nuevo_campo_b": 123}},
    {"Records": {"IdUnicoCruce": "B456", "datos_secundarios": "info_secundaria_2"}},
]

# Claves de cruce
a_key_path = "Documents.IdUnico"
b_key_path = "Records.IdUnicoCruce"

# Realizar el cruce de datos con la nueva función
resultados_cruce = perform_cruce_de_datos_con_left_join(a_data_example, b_data_example, a_key_path, b_key_path, b_structure_xml)

print("Resultados del cruce de datos (left join):")
print(json.dumps(resultados_cruce, indent=4))