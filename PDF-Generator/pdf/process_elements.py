from renderer.flowarea_renderer import process_flows_areas
from renderer.path_renderer import process_path_object
from renderer.image_renderer import process_image_objects
from renderer.chart_renderer import process_chart
from renderer.barcode_renderer import process_barcode_objects

def process_elements_by_object(config, object_id, page_width, page_height, c, parent_offset=(0,0), element=False):
    offset_x = parent_offset[0]
    offset_y = parent_offset[1]
    elements_to_process = config.grouped_nodes.get(object_id) 
    for element_to_process in elements_to_process:
        #Obtener el nombre del nodo raiz
        node_name = element_to_process.tag
        element_name = element_to_process.find("Name")
        if element_name is not None:
            name = element_name.text
            print(f"Procesando elemento: {name}")
        
        element_id = element_to_process.find('Id').text
        element_objects = config.config_dicts[node_name]
        element_object = element_objects.get(element_id)  


        if (name == "FlowArea 2"):
            pass
            #print("Pausa")

        if (node_name == "FlowArea"):
            process_flows_areas(config, element_object, page_height, page_width, c, parent_offset=(offset_x,offset_y), element=element)
        elif (node_name == "ElementObject"):
            print("Se omite hasta que se configure")
            #process_flows_areas(config, element_to_process, c, parent_offset=(offset_x,offset_y), element=True)
        elif (node_name == "PathObject"):
            process_path_object(element_object, page_height, c, parent_offset=(offset_x,offset_y))
        elif (node_name == "ImageObject"):
            image_objects = config.config_dicts['Image']
            image_id = element_object.find('ImageId').text
            image_element = image_objects.get(image_id)
            images_cache = config.images_cache         
            process_image_objects(config, element_object, image_element, images_cache, page_height, c, parent_offset=(offset_x,offset_y))
        elif (node_name == "Chart"):
            process_chart(element_object, c, parent_offset=(offset_x,offset_y))
        elif (node_name == "Barcode"):
            process_barcode_objects(config, element_object, page_height, c)
        else:
            print(f"Elemento no configurado: {node_name}") 