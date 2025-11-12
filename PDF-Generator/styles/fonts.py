import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from fontTools.ttLib import TTFont as FTFont

def register_fonts(fonts, include_bytes):
    """Registra las fuentes definidas en el XML"""
    from datetime import datetime
    print(f"{datetime.now()} Inicio registro fuentes")
    font_reportlab = {}
    initial_path = r"\\Cad-fsx-eks.cadena.com.co\c$\trident_pvc_75f19d79_8dc5_4cdb_9aa1_67e850e1425d\Resources\Fonts"
    for id, font in fonts.items():
        font_name = font.find('FontName').text
        sub_fonts = font.findall('SubFont')
        
        # Si no tiene subfont quiere decir que son fuentes del sistema, demo registrarlas igual
        if len(sub_fonts) == 0:
            system_subfonts = ['Regular','Bold','Narrow']
            system_root = r"C:\Windows\Fonts"
            for system_subfunt in system_subfonts:
                complete_name = f'{font_name}-{system_subfunt}'
                if font_reportlab.get(complete_name) is not None:
                    continue
                ruta_completa = os.path.join(system_root, complete_name + ".ttf")
                if not os.path.exists(ruta_completa):
                    ruta_completa = os.path.join(initial_path, "Arial.ttf")
                
                pdfmetrics.registerFont(TTFont(complete_name, ruta_completa))
                font_reportlab[complete_name] = ruta_completa
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
                    if font_reportlab.get(complete_name) is not None:
                        continue
                    #Pruebas buscando las fuentes en font                    
                    path = ""
                    if "Helvetica" in font_name:
                        path = os.path.join(initial_path,"Helvetica Completa")
                    font_container = "OtraRuta"
                    font_path = path
                    #Fin pruebas
                    
                    if font_container == 'VCSLocation':
                        print("Realizar la busqueda de la fuente en el VCS")
                        #TODO
                        #Realizar descarga desde el VCS o revisar como manejar las fuentes
                    else:
                        print(f"Realizar la busqueda de la fuente {font_file}")
                        # Asumimos que las fuentes están en un directorio 'fonts'
                        if include_bytes:
                            # Leer las fuentes desde el disco y guardar los bytes en un BytesIO 
                            ruta_completa = os.path.join(font_path, font_file)                  
                            with open(ruta_completa, 'rb') as f:
                                font_data = f.read()
                                # Registrar la fuente en ReportLab
                                font_reportlab[complete_name] = font_data
                        else:
                            ruta_completa = os.path.join(font_path, font_file)

                            if os.path.exists(ruta_completa):
                                f = FTFont(ruta_completa)
                                if 'glyf' not in f:
                                    ###TEMPORAL###
                                    #Reemplazar fuentes no existentes o OTF con fuente Arial
                                    ruta_completa = os.path.join(initial_path, "Arial.ttf")
                            else:
                                ruta_completa = os.path.join(initial_path, "Arial.ttf")

                            pdfmetrics.registerFont(TTFont(complete_name, ruta_completa))
                        font_reportlab[complete_name] = ruta_completa
                except Exception as e:
                    print(f"No se pudo cargar la fuente: {e}")
    #print(pdfmetrics.getRegisteredFontNames())
    print(f"{datetime.now()} Fin registro fuentes")
    return font_reportlab
