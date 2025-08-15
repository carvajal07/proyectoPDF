from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_fonts(fonts, include_bytes):
    """Registra las fuentes definidas en el XML"""
    font_reportlab = {}
    for id, font in fonts.items():
        font_name = font.find('FontName').text
        sub_fonts = font.findall('SubFont')
        for sub_font in sub_fonts:
            font_location = sub_font.find('FontLocation').text
            if font_location:
                # Extraer el nombre del archivo de la ruta
                font_container = font_location.split(',')[0]
                font_path= font_location.split(',')[-1]
                font_file = font_path.split('/')[-1]
                sub_font_name = sub_font.get('Name')

                try:
                    complete_name = f'{font_name}-{sub_font_name}'
                    #Pruebas buscando las fuentes en font
                    path = "C:\\Windows\\Fonts\\"
                    font_container = "OtraRuta"
                    font_path = path
                    #Fin pruebas
                    
                    if font_container == 'VCSLocation':
                        print("Realizar la busqueda de la fuente en el VCS")
                        #TODO
                        #Realizar descarga desde el VCS o revisar como manejar las fuentes
                    else:
                        print(f"Realizar la busqueda de la fuente {font_file} en el directorio {font_path}")
                        # Asumimos que las fuentes están en un directorio 'fonts'
                        if include_bytes:
                            # Leer las fuentes desde el disco y guardar los bytes en un BytesIO                    
                            with open(f'{font_path}{font_file}', 'rb') as f:
                                font_data = f.read()
                                # Registrar la fuente en ReportLab
                                font_reportlab[complete_name] = font_data
                        else:
                            pdfmetrics.registerFont(TTFont(complete_name, f'{font_path}{font_file}'))
                except:
                    print(f"No se pudo cargar la fuente: {complete_name}")
    #print(pdfmetrics.getRegisteredFontNames())
    return font_reportlab
