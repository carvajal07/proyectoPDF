import core.constants as const
from parser.json_parser import json_parser
from parser.xml_parser import xml_read, map_elements
from styles.parastyles import register_parastyles
from styles.borderstyles import register_borderstyles
from styles.fonts import register_fonts
from styles.colors import register_colors
from models.load_input_result import LoadInputResult
from loader.preprocessing import topological_sort
from styles.images import register_images

def load_input(json_path, customer, product, pruebas) -> LoadInputResult:
    """
    Carga el JSON y el layout XML completo desde sus fuentes.
    Retorna un objeto LoadInputResult con toda la información estructurada.
    """   
    # Obtener XML desde BD
    workflow = xml_read(customer, product)
    connections = workflow.findall(const.CONNECTIONS_CONTAINER)
    layout = workflow.find(const.LAYOUT_CONTAINER)
  
    if layout is None:
        print("⚠️ No se encontró el contenedor de diseño en el XML")
        #raise ValueError("No se encontró el contenedor de diseño en el XML")
    
    if connections is None:
        raise ValueError("No se encontraron conexiones en el XML")
    
    #Preprocesar la info de las conexiones de cada modulo
    list_to_preprocess = topological_sort(connections)
    #elements_to_preprocess = [obj for obj in list_to_preprocess if obj in const.OBJECT_TYPES]

    all_elements_workflow = {}
    for elem in workflow:
        id_elem = elem.find("Id")
        if id_elem is not None:
            node_id = id_elem.text.strip()
            all_elements_workflow[node_id] = elem


    full_context, documents = json_parser(json_path, all_elements_workflow, list_to_preprocess, connections)
    
    config_dicts, data_dicts, grouped_nodes, all_elements = map_elements(layout)
    parastyle_reportlabs = register_parastyles(config_dicts["ParaStyle"])
    fonts_reportlabs = register_fonts(config_dicts["Font"], include_bytes=False)
    colors_reportlabs = register_colors(config_dicts["Color"])
    borderstyle_reportlabs = register_borderstyles(
        config_dicts["BorderStyle"], 
        config_dicts["FillStyle"], 
        colors_reportlabs
    )

    # Realizo inicialmente el registro de las imagenes del primer registro
    #images_cache = register_images(config_dicts["Image"], data_dicts["Variable"], full_context)
    
    return LoadInputResult(
        layout=layout,
        full_context=full_context,
        documents=documents,
        config_dicts=config_dicts,
        data_dicts=data_dicts,
        grouped_nodes=grouped_nodes,
        all_elements=all_elements,
        parastyle_reportlabs=parastyle_reportlabs,
        fonts_reportlabs=fonts_reportlabs,
        colors_reportlabs=colors_reportlabs,
        borderstyle_reportlabs=borderstyle_reportlabs,
        images_cache={}
    )
