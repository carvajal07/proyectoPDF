import io
import qrcode
from core.utils import convert_units
from core.utils import get_variable_value
from reportlab.lib.utils import ImageReader
from reportlab.graphics.barcode import code39, code128, eanbc
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H


def generate_qr_Code(c, page_height, data, p_x, p_y, s_x, s_y, m_vals, module_width, error_level):
    def nivel_error_qr(level):
        return {
            "L": ERROR_CORRECT_L,
            "M": ERROR_CORRECT_M,
            "Q": ERROR_CORRECT_Q,
            "H": ERROR_CORRECT_H,
        }.get(level.upper(), ERROR_CORRECT_M)
    
    box_size = 10
    border = 4
    qr = qrcode.QRCode(
        version=None,  # Auto
        error_correction=nivel_error_qr(error_level),
        box_size=int(box_size),
        border=int(border),
    )

    qr.add_data(data)
    qr.make(fit=True)

    # Crear una imagen PIL del QR
    qr_img = qr.make_image(fill_color="black", back_color="white")#.resize((int(module_width * qr.modules_count), int(module_width * qr.modules_count)))
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    img = ImageReader(qr_buffer)

    #Debo restarle los bordes de mas al momento de hacer crecer el QR a la posicionn X y Y
    p_x = p_x - (s_y / 2)
    p_y = p_y - (s_x / 2)
    #p_y = p_y - (border * box_size)

    s_x = module_width * qr.modules_count
    s_y = module_width * qr.modules_count
    

    c.saveState()
    c.translate(p_x, page_height - p_y)
    m0, m1, m2, m3, m4, m5 = m_vals
    m1 = -m1  # Igual que en process_image_objects
    m2 = -m2
    c.transform(m0, m1, m2, m3, m4, m5)
    c.drawImage(img, 0, -s_y, s_x, s_y, mask='auto')
    c.restoreState()        

def generate_code128(c, page_height, data, p_x, p_y, s_x, s_y, m_vals, module_size=0.3, module_height=15):
    """
    Dibuja un Code128 en el PDF aplicando las transformaciones.
    """

    barcode = code128.Code128(data, barHeight=module_height, barWidth=module_size)

    c.saveState()
    c.translate(p_x, page_height - p_y)

    

    m0, m1, m2, m3, m4, m5 = m_vals
    m1 = -m1
    m2 = -m2
    c.transform(m0, m1, m2, m3, m4, m5)
    barcode.drawOn(c, 0, -module_height)
    c.restoreState()

def generate_ean128(c, page_height, data, p_x, p_y, s_x, s_y, m_vals, module_size=0.3, module_height=15):
    """
    Dibuja un EAN128 (usando Code128 como base) en el PDF aplicando las transformaciones.
    EAN128 se representa con Code128 usando el carácter FNC1, que en la mayoría de implementaciones
    se puede añadir como chr(202) delante del dato.
    """

    # La mayoría de los sistemas representan EAN128 como FNC1 + datos.
    data_ean128 = chr(202) + data  # Puede variar según librería/barcode reader
    data_ean128 = data  # Puede variar según librería/barcode reader

    barcode = code128.Code128(data_ean128, barHeight=module_height, barWidth=module_size)
    c.saveState()
    c.translate(p_x, page_height - p_y)
    m0, m1, m2, m3, m4, m5 = m_vals
    m1 = -m1
    m2 = -m2
    c.transform(m0, m1, m2, m3, m4, m5)
    barcode.drawOn(c, 0, -module_height)
    c.restoreState()

def generate_ean8(c, page_height, data, p_x, p_y, s_x, s_y, m_vals, module_size=0.3, module_height=15):
    """
    Dibuja un EAN8 en el PDF aplicando las transformaciones.
    """


    barcode = eanbc.Ean8BarcodeWidget(data)
    bounds = barcode.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    scale_x = module_size / width if width else 1
    scale_y = module_height / height if height else 1

    c.saveState()
    c.translate(p_x, page_height - p_y)
    m0, m1, m2, m3, m4, m5 = m_vals
    m1 = -m1
    m2 = -m2
    c.transform(m0, m1, m2, m3, m4, m5)
    c.scale(scale_x, scale_y)
    barcode.drawOn(c, 0, -height)
    c.restoreState()

def generate_ean13(c, page_height, data, p_x, p_y, s_x, s_y, m_vals, module_size=0.3, module_height=15):
    """
    Dibuja un EAN13 en el PDF aplicando las transformaciones.
    """

    barcode = eanbc.Ean13BarcodeWidget(data)
    bounds = barcode.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    scale_x = module_size / width if width else 1
    scale_y = module_height / height if height else 1

    c.saveState()
    c.translate(p_x, page_height - p_y)
    m0, m1, m2, m3, m4, m5 = m_vals
    m1 = -m1
    m2 = -m2
    c.transform(m0, m1, m2, m3, m4, m5)
    c.scale(scale_x, scale_y)
    barcode.drawOn(c, 0, -height)
    c.restoreState()

def generate_code39(c, page_height, data, p_x, p_y, s_x, s_y, m_vals, module_size=0.3, module_height=15):
    """
    Dibuja un Code39 en el PDF aplicando las transformaciones.
    """

    barcode = code39.Standard39(data, barHeight=module_height, barWidth=module_size, stop=1)
    c.saveState()
    c.translate(p_x, page_height - p_y)
    m0, m1, m2, m3, m4, m5 = m_vals
    m1 = -m1
    m2 = -m2
    c.transform(m0, m1, m2, m3, m4, m5)
    barcode.drawOn(c, 0, -module_height)
    c.restoreState()

def process_barcode_objects(config, barcode_element, page_height, c):
    # Tipos de codigos de barras
    # QRBarcodeGenerator
    # EAN8BarcodeGenerator
    # EAN13BarcodeGenerator
    # EAN128BarcodeGenerator
    # Code39BarcodeGenerator
    # Code128BarcodeGenerator        

    variable_id = barcode_element.find('VariableId').text
    fill_style_id = barcode_element.find('FillStyleId').text
    variables = config.data_dicts['Variable']
    full_context = config.full_context
    code_text = get_variable_value(variable_id, variables, full_context)       
    
    pos = barcode_element.find('Pos')
    size = barcode_element.find('Size')

    p_x = convert_units(pos.get('X',0))
    p_y = convert_units(pos.get('Y',0))
    s_x = convert_units(size.get('X',0))
    s_y = convert_units(size.get('Y',0))
    
    #rotation = float(barcode.find("Rotation").text or 0)
    #scale_x = float(barcode.find("Scale").get("X", 1))
    #scale_y = float(barcode.find("Scale").get("Y", 1))
    m0 = float(barcode_element.find("Transformation_M0").text)
    m1 = float(barcode_element.find("Transformation_M1").text)
    m2 = float(barcode_element.find("Transformation_M2").text)
    m3 = float(barcode_element.find("Transformation_M3").text)
    m4 = float(barcode_element.find("Transformation_M4").text)
    m5 = float(barcode_element.find("Transformation_M5").text)
    m_vals = (m0, m1, m2, m3, m4, m5)

    barcode_generator_element = barcode_element.find('BarcodeGenerator')
    barcode_type = barcode_generator_element.find('Type').text
    
    # Codigo QR
    if barcode_type == "QRBarcodeGenerator":
        error_level = barcode_generator_element.find("ErrorLevel").text
        module_width = convert_units(barcode_generator_element.find('ModulWidth').text)    
        generate_qr_Code(c, page_height, code_text, p_x, p_y, s_x, s_y, m_vals, module_width, error_level)
    # Todos los codigos de barras
    else:
        module_size = convert_units(barcode_generator_element.find('ModulSize').text) if barcode_generator_element.find('ModulSize') is not None else 0.3
        module_height = convert_units(barcode_generator_element.find('Height').text) if barcode_generator_element.find('Height') is not None else 15

        if barcode_type == "EAN8BarcodeGenerator":
            generate_ean8(c, page_height, code_text, p_x, p_y, s_x, s_y, m_vals, module_size, module_height)
        elif barcode_type == "EAN13BarcodeGenerator":
            generate_ean13(c, page_height, code_text, p_x, p_y, s_x, s_y, m_vals, module_size, module_height)
        elif barcode_type == "EAN128BarcodeGenerator":
            generate_ean128(c, page_height, code_text, p_x, p_y, s_x, s_y, m_vals, module_size, module_height)
        elif barcode_type == "Code39BarcodeGenerator":
            generate_code39(c, page_height, code_text, p_x, p_y, s_x, s_y, m_vals, module_size, module_height)
        elif barcode_type == "Code128BarcodeGenerator":
            generate_code128(c, page_height, code_text, p_x, p_y, s_x, s_y, m_vals, module_size, module_height)
        else:
            print("Codigo no configurado")   