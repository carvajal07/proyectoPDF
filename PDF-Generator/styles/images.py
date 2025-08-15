import os
import fitz
from PIL import Image
from reportlab.lib.utils import ImageReader
from core.utils import get_variable_value

def register_images(images, variables, data):
    image_reportlab = {}
    for id, image in images.items():
        image_id = image.find('Id').text
        image_type = image.find('ImageType').text
        
        if image_type == "Variable":
            variable_id = image.find("VariableId").text
            path = get_variable_value(variable_id, variables, data)
        elif image_type == "Simple":
            image_location = image.find("ImageLocation").text
            _, path = image_location.split(',')
            print("Pendiente configurar la descarga de imagenes desde el vcs")
            if "vcs" in path:
                path = path.replace("vcs://Produccion/Epm/FacturasPrepago/Resources/Imagenes/", "D:\\ProyectoComunicaciones\\ProyectoPDFGit\\Imagenes\\")
        else:
            path = None

        img = None
        if isinstance(path, str):
            if path and os.path.exists(path):                   
                if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    img = ImageReader(path)
                elif path.lower().endswith('.pdf'):
                    pdf_doc = fitz.open(path)
                    pdf_page = pdf_doc[0]  # Tomar la primera página
                    pix = pdf_page.get_pixmap(dpi=96)
                    img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img = ImageReader(img_pil)
                
            else:
                print(f"Imagen no disponible: {path}")

            # Guarda en el cache (sea imagen o None si no existe)
            image_reportlab[path] = img
        else:
            print(f"Error: El path de la imagen no es una cadena válida: {path}")

    return image_reportlab