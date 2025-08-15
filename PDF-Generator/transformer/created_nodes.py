def set_nested_value_recursive(json_data, keys, value):
    if not keys:
        return

    key = keys[0]

    if isinstance(json_data, list):
        for item in json_data:
            set_nested_value_recursive(item, keys, value)

    elif isinstance(json_data, dict):
        if len(keys) == 1:
            json_data[key] = value
        else:
            if key not in json_data:
                json_data[key] = {}
            # Si es diccionario, seguir recursivamente
            next_obj = json_data[key]
            # Si no existe, asumimos que es un dict
            if isinstance(next_obj, list) or isinstance(next_obj, dict):
                set_nested_value_recursive(next_obj, keys[1:], value)
            else:
                # Si el valor actual no es contenedor, lo reemplazamos por un dict
                json_data[key] = {}
                set_nested_value_recursive(json_data[key], keys[1:], value)

def get_default_value(node_type, default):
    if node_type == "String":
        return default if default else ""
    elif node_type == "Int":
        return int(default) if default else 0
    elif node_type == "Float":
        return float(default) if default else 0.0
    elif node_type == "Bool":
        return default.lower() == "true" if default else False
    return None

def get_all_nested_values(data, keys):
    """Obtiene todos los valores en cualquier nivel, incluso dentro de arrays anidados."""
    if not keys:
        return [data]

    key = keys[0]
    rest_keys = keys[1:]
    results = []

    if isinstance(data, dict):
        if key in data:
            results += get_all_nested_values(data[key], rest_keys)

    elif isinstance(data, list):
        for item in data:
            results += get_all_nested_values(item, keys)

    return results


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

def apply_created_nodes(new_nodes, json_data):
    #<CreatedNode Type="String" Optionality="MustExist" Caption="Estrato_ServiceSPD_ArrPr" FieldDotName="Documents.Estrato_ServiceSPD_ArrPr" ParentDotName="Documents" LinkedToDotName="Documents.ChannelServicesSPD.Estrato_ServiceSPD" LinkedToDotName2="" NodeLink2NodeType="String" LinkedType="Special" Operation="CopyFirstValueLevelUp" DefaultValue="" SearchArrayKeyValue=""/>
    #<CreatedNode Type="String" Optionality="MustExist" Caption="rutaFirma" FieldDotName="Documents.rutaFirma" ParentDotName="Documents" LinkedToDotName="" LinkedToDotName2="" NodeLink2NodeType="String" LinkedType="StandAlone" DefaultValue="" SearchArrayKeyValue=""/>
    for node in new_nodes:
        field_path = node.attrib["FieldDotName"].split(".")
        linked_type = node.attrib["LinkedType"]
        if "Estrato_ServiceSPD_ArrPr" in field_path:
            print("pausa")
        node_type = node.attrib["Type"]
        default_value = node.attrib.get("DefaultValue", "")

        value = get_default_value(node_type, default_value)
        field_path = get_all_nested_values(json_data, field_path)
        set_nested_value_recursive(json_data, field_path, value)

    return json_data
