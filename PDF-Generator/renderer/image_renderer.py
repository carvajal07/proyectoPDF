import os
from core.utils import convert_units
from core.utils import get_variable_value
from core.utils import evaluate_condition_v2
from reportlab.lib.utils import ImageReader
import core.constants as const
from PIL import Image
import fitz

def process_image_objects(config, imagearea_element, image_element, images_cache, page_height, c, parent_offset=(0,0)):
    """Procesa y dibuja objetos de imagen"""

    offset_x = parent_offset[0]
    offset_y = parent_offset[1]
    path = ""

    pos = imagearea_element.find('Pos')
    size = imagearea_element.find('Size')
    
    #rotation = float(imageObject_object.find("Rotation").text or 0)
    #scale_x = float(imageObject_object.find("Scale").get("X", 1))
    #scale_y = float(imageObject_object.find("Scale").get("Y", 1))
    m0 = float(imagearea_element.find("Transformation_M0").text)
    m1 = float(imagearea_element.find("Transformation_M1").text)
    m2 = float(imagearea_element.find("Transformation_M2").text)
    m3 = float(imagearea_element.find("Transformation_M3").text)
    m4 = float(imagearea_element.find("Transformation_M4").text)
    m5 = float(imagearea_element.find("Transformation_M5").text)
    
    image_type = image_element.find('ImageType').text 

    if image_type == "Variable":
        variable_id = image_element.find("VariableId").text
        variables = config.data_dicts['Variable']
        full_context = config.full_context
        path = get_variable_value(variable_id, variables, full_context)
        #path = get_variable_value(variable_id)
    elif image_type == "InlCond":
        pass
        '''
        image_conditions = image.findall("ImageCondition")
        for image_condition in image_conditions:
            object_condition = image_condition.find("Condition")
            image_id = image_condition.find("ImageId").text
            if object_condition is not None:
                condition = object_condition.text
                # Evaluar condicion de la  imagen
                full_context = config.full_context
                if evaluate_condition_v2(condition, register):
            else:
                image = images.get(image_id)
                image_type = image.find('ImageType').text
                path = get_path(image_type, image, images, variables, data)
        '''
    elif image_type == "Simple":
        image_location = image_element.find("ImageLocation").text
        _, path = image_location.split(',')
    else:
        print(f"Tipo de imagen desconocido: {image_type}")
        exit(1)

    img = images_cache.get(path)

    #Si no tengo imagen en cache, buscarla en el XML
    if img is None:                                               
        if os.path.exists(path):
            if path.lower().endswith(const.VALID_IMAGE_EXTENSIONS):
                img = ImageReader(path)
            elif path.lower().endswith('.pdf'):
                pdf_doc = fitz.open(path)
                pdf_page = pdf_doc[0]  # Tomar la primera página
                pix = pdf_page.get_pixmap(dpi=96)
                img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img = ImageReader(img_pil)
            images_cache[path] = img
    else:
        if pos is not None and size is not None:
            x = convert_units(pos.get('X')) + offset_x
            y = convert_units(pos.get('Y')) + offset_y
            width = convert_units(size.get('X'))
            height = convert_units(size.get('Y'))
            
            if img:
                c.saveState()
                c.translate(x, page_height - y)
                # Invertir la rotación si corresponde
                c.transform(m0, -m1, -m2, m3, m4, m5)
                c.drawImage(img, 0, -height, width, height)
                c.restoreState()
            else:
                print(f"Error: La imagen no existe en la ruta especificada: {path}")
                exit(1)
