import core.constants as const
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from typing import Dict, List, Tuple
from infra.db import get_connection

def get_xml(customer, product):
    conn = get_connection("PruebaMapeo")
    cursor = conn.cursor()

    query = """
        SELECT [schema]
        FROM SchemeXml
        WHERE customer = ? AND product = ?
    """
    try:
        cursor.execute(query, (customer, product))
    except Exception as e:
        conn.close()
        raise ValueError(f"Error al ejecutar la consulta: {e}")
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    else:
        raise ValueError(f"No se encontró layout para {customer}-{product}")

def map_elements(layout: Element) -> Tuple[Dict, Dict, Dict[str, List[Element]], Dict[str, Element]]:
    """
    Procesa un layout XML y organiza los elementos según su tipo y jerarquía.

    Args:
        layout (Element): Nodo XML <Layout> que contiene los elementos del diseño.

    Returns:
        tuple:
            - config_dicts: Elementos raíz por tipo (no tienen ParentId).
            - data_dicts: Elementos hijos organizados por tipo (tienen ParentId).
            - grouped_nodes: Elementos agrupados por su ParentId.
            - all_elements: Mapeo plano de todos los elementos por Id.
    """
    
    config_dicts = {}
    data_dicts = {}
    grouped_nodes = {}
    all_elements = {}

    for object_type in const.OBJECT_TYPES:
        config_dicts[object_type] = {}
        data_dicts[object_type] = {}
    
        elements = layout.findall(object_type)
        for element in elements:
            obj_id_elem = element.find("Id")
            if obj_id_elem is None:
                continue
            obj_id = obj_id_elem.text.strip()
            # Si existe el objeto "ParentId" quiere decir que el nodo corresponde al arbol de objetos
            parent_element = element.find('ParentId')
            if parent_element is not None:
                parent = parent_element.text
                if parent not in grouped_nodes:
                    grouped_nodes[parent] = []
                grouped_nodes[parent].append(element)
                data_dicts[object_type][obj_id] = element
            else:
                config_dicts[object_type][obj_id] = element
                all_elements[obj_id] = element

    return config_dicts, data_dicts, grouped_nodes, all_elements

def xml_read(customer:str,product:str) -> ET.Element:
    """
    Realiza la consulta del XML para obtener el nodo <Layout> con la configuración del PDF.

    Args:
        customer (str): Nombre del cliente.
        product (str): Nombre del producto.

    Returns:
        ET.Element: Nodo <Layout> del XML.
    
    Raises:
        ValueError: Si el contenedor de layout no se encuentra.
    """
    xml_string = get_xml(customer, product)
    workflow = ET.fromstring(xml_string)    
    
    return workflow