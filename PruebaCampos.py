import json

# Cargar el contenido de tu archivo JSON original
json_string_original = """
{
    "Documents": [
        {
            "IdUnico": "DEEP10507508",
            "Canal_Datos": "PE",
            "Ordenamiento": "0000001",
            "Agrupamiento": "0000001",
            "Nombre": "MARIANO ANTONIO AVILA ANGULO",
            "Direccion": "190665200319905000",
            "Ciudad": "Turbo",
            "Departamento": "Antioquia",
            "uno": [
                {
                    "conceptoDetalle": "ENERGIA PREPAGO MERCADO REG",
                    "NumeroMedidor": "14497506346",
                    "ConsumoPromedio": "12.70",
                    "dos": [
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "PeriodoEnergía",
                            "ValorNotaServices_SubscriberConsumption": "6-2025",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "1concepto-1",
                                    "ValorDetalleDescuento": "1valor-1"
                                }
                            ]
                        },
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "Operador",
                            "ValorNotaServices_SubscriberConsumption": "EPM",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "2concepto-1",
                                    "ValorDetalleDescuento": "2valor-1"
                                },
                                {
                                    "ConceptoDetalleDescuento": "2concepto-2",
                                    "ValorDetalleDescuento": "2valor-2"
                                }
                            ]
                        },
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "DirOperador",
                            "ValorNotaServices_SubscriberConsumption": "CARRERA 58 NRO 42 125",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "3concepto-1",
                                    "ValorDetalleDescuento": "3valor-1"
                                },
                                {
                                    "ConceptoDetalleDescuento": "3concepto-2",
                                    "ValorDetalleDescuento": "3valor-2"
                                },
                                {
                                    "ConceptoDetalleDescuento": "3concepto-3",
                                    "ValorDetalleDescuento": "3valor-3"
                                }
                            ]
                        }
                    ]
                },
                {
                    "conceptoDetalle": "ENERGIA PREPAGO MERCADO REGdg",
                    "NumeroMedidor": "14497506346dsgf",
                    "ConsumoPromedio": "12.70sfg",
                    "dos": [
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "PeriodoEnergíasdgf",
                            "ValorNotaServices_SubscriberConsumption": "6-2025dsg",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "1concepto-1dsg",
                                    "ValorDetalleDescuento": "1valor-1dsg"
                                }
                            ]
                        },
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "Operadordsgf",
                            "ValorNotaServices_SubscriberConsumption": "EPMsdg",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "2concepto-1sdgf",
                                    "ValorDetalleDescuento": "2valor-1dsgf"
                                },
                                {
                                    "ConceptoDetalleDescuento": "2concepto-2sdg",
                                    "ValorDetalleDescuento": "2valor-2dsg"
                                }
                            ]
                        },
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "DirOperadordsgf",
                            "ValorNotaServices_SubscriberConsumption": "CARRERA 58 NRO 42 125dgfs",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "3concepto-1dgf",
                                    "ValorDetalleDescuento": "3valor-1dgf"
                                },
                                {
                                    "ConceptoDetalleDescuento": "3concepto-2dgf",
                                    "ValorDetalleDescuento": "3valor-2dgf"
                                },
                                {
                                    "ConceptoDetalleDescuento": "3concepto-3dgf",
                                    "ValorDetalleDescuento": "3valor-3dfg"
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "IdUnico": "DEEP10507508-2",
            "Canal_Datos": "PE-2",
            "Ordenamiento": "0000001-2",
            "Agrupamiento": "0000001-2",
            "Nombre": "MARIANO ANTONIO AVILA ANGULO-2",
            "Direccion": "190665200319905000-2",
            "Ciudad": "Turbo-2",
            "Departamento": "Antioquia-2",
            "uno": [
                {
                    "conceptoDetalle": "ENERGIA PREPAGO MERCADO REG-2",
                    "NumeroMedidor": "14497506346-2",
                    "ConsumoPromedio": "12.70-2",
                    "dos": [
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "PeriodoEnergía2",
                            "ValorNotaServices_SubscriberConsumption": "6-20252",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "1concepto-12",
                                    "ValorDetalleDescuento": "1valor-12"
                                }
                            ]
                        },
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "Operador2",
                            "ValorNotaServices_SubscriberConsumption": "EPM2",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "2concepto-12",
                                    "ValorDetalleDescuento": "2valor-1"
                                },
                                {
                                    "ConceptoDetalleDescuento": "2concepto-22",
                                    "ValorDetalleDescuento": "2valor-22"
                                }
                            ]
                        },
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "DirOperador2",
                            "ValorNotaServices_SubscriberConsumption": "CARRERA 58 NRO 42 1252",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "3concepto-12",
                                    "ValorDetalleDescuento": "3valor-12"
                                },
                                {
                                    "ConceptoDetalleDescuento": "3concepto-22",
                                    "ValorDetalleDescuento": "3valor-22"
                                },
                                {
                                    "ConceptoDetalleDescuento": "3concepto-32",
                                    "ValorDetalleDescuento": "3valor-32"
                                }
                            ]
                        }
                    ]
                },
                {
                    "conceptoDetalle": "ENERGIA PREPAGO MERCADO REG-2ryt",
                    "NumeroMedidor": "14497506346-2ryt",
                    "ConsumoPromedio": "12.70-2ry",
                    "dos": [
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "PeriodoEnergía2ry",
                            "ValorNotaServices_SubscriberConsumption": "6-20252rty",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "1concepto-12r",
                                    "ValorDetalleDescuento": "1valor-12rty"
                                }
                            ]
                        },
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "Operador2ry",
                            "ValorNotaServices_SubscriberConsumption": "EPM2ry",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "2concepto-12ry",
                                    "ValorDetalleDescuento": "2valor-1ry"
                                },
                                {
                                    "ConceptoDetalleDescuento": "2concepto-22rty",
                                    "ValorDetalleDescuento": "2valor-22rty"
                                }
                            ]
                        },
                        {
                            "DescripcionNotaServices_SubscriberConsumption": "DirOperador2rty",
                            "ValorNotaServices_SubscriberConsumption": "CARRERA 58 NRO 42 1252rty",
                            "tres": [
                                {
                                    "ConceptoDetalleDescuento": "3concepto-12rty",
                                    "ValorDetalleDescuento": "3valor-12rty"
                                },
                                {
                                    "ConceptoDetalleDescuento": "3concepto-22try",
                                    "ValorDetalleDescuento": "3valor-22try"
                                },
                                {
                                    "ConceptoDetalleDescuento": "3concepto-32tr",
                                    "ValorDetalleDescuento": "3valor-32ty"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}
"""
data = json.loads(json_string_original)

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


# ---
# Prueba 1: Agregar 'ValorPeriodoEnergiaPrimer' a 'Documents.uno.dos' tomando el 'ValorDetalleDescuento'
# del PRIMER elemento del array 'tres' (relativo al contexto de 'dos')
print("--- Estructura Original ---")
# print(json.dumps(data, indent=4)) # Descomentar para ver la estructura completa

target_path_1 = "Documents.uno.dos"
new_field_name_1 = "ValorPeriodoEnergiaPrimer"
source_path_for_value_1 = "tres.ValorDetalleDescuento" # 'tres' es la lista, 'ValorDetalleDescuento' es el campo dentro del diccionario
index_type_1 = "first"

target_path_parts_1 = target_path_1.split('.')
add_field_with_dynamic_value(data, target_path_parts_1, new_field_name_1, source_path_for_value_1, index_type_1)

print("\n--- Después de agregar 'ValorPeriodoEnergiaPrimer' (valor de tres.ValorDetalleDescuento - PRIMERO) ---")
print(json.dumps(data, indent=4))

# ---
# Prueba 2: Agregar 'ValorPeriodoEnergiaUltimo' a 'Documents.uno.dos' tomando el 'ValorDetalleDescuento'
# del ÚLTIMO elemento del array 'tres' (relativo al contexto de 'dos')
print("\n--- Prueba Adicional: Agregar 'ValorPeriodoEnergiaUltimo' (valor de tres.ValorDetalleDescuento - ÚLTIMO) ---")

target_path_2 = "Documents.uno.dos"
new_field_name_2 = "ValorPeriodoEnergiaUltimo"
source_path_for_value_2 = "tres.ValorDetalleDescuento"
index_type_2 = "last"

target_path_parts_2 = target_path_2.split('.')
add_field_with_dynamic_value(data, target_path_parts_2, new_field_name_2, source_path_for_value_2, index_type_2)

print("\n--- Después de agregar 'ValorPeriodoEnergiaUltimo' (valor de tres.ValorDetalleDescuento - ÚLTIMO) ---")
print(json.dumps(data, indent=4))