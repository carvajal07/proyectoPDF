import re
import copy
from core.utils import convert_units
from core.utils import evaluate_condition_v2
from core.utils import get_variable_value
from renderer.table_renderer import process_table

from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth

def process_flow(config, flow_element, page_height, page_width, context=None, c=None, parent_offset=(0,0), max_width=0):
        """Procesa un objeto Flow dentro de una celda y lo convierte en texto o párrafo"""
        register = config.full_context
        if context is None:
            context = config.full_context
        all_elements = config.all_elements
        para = []
        flow_type = flow_element.find('Type').text
        #tipos de flow
        #-Simple
        #-First fitting auto
        #-First fitting
        #print(flow_type)
        default_flow = True
        if flow_type == "InlCond":
            #Evaluar la condicion para verificar que flow debo procesar
            flow_condition_elements = flow_element.findall('Condition')
            for flow_condition_element in flow_condition_elements:
                #Capturar la condicion del atributo Value
                condition = flow_condition_element.get('Value')
                
                if evaluate_condition_v2(condition, register):
                    #Hacer cambio del flow element por el flow que cumple la condicion
                    new_flow_id = flow_condition_element.text
                    if new_flow_id is None:
                        print("❌ No se encontró el FlowId en la condición.")
                        # Debo retornar un string vacio para que no se pinte nada
                        return para, ""

                    flow_element = all_elements.get(new_flow_id)
                    #print("✔ Se cumple la condición.")
                    default_flow = False
                    break
            if default_flow:
                #print("❌ No se cumple la condición, se usará el flow por defecto.")
                default_flow_id = flow_element.find('Default').text
                if default_flow_id is None:
                    print("❌ No se encontró el FlowId por defecto.")
                    # Debo retornar un string vacio para que no se pinte nada
                    return para, ""
                else:
                    flow_element = all_elements.get(default_flow_id)

        flow_content = flow_element.find('FlowContent')
        
        para_style_dict = config.parastyle_reportlabs
        fill_styles = config.config_dicts['FillStyle']
        colors = config.colors_reportlabs
        text_styles = config.config_dicts['TextStyle']
        fonts_config_dict = config.config_dicts['Font']
        
        p_elements = flow_content.findall('P')
        for i, p in enumerate(p_elements):
            #Crear los paragraph o usarlos
            p_id = p.get('Id')
            #print(f"Procesando Paragraph con Id: {p_id}")
            para_style_ant = copy.copy(para_style_dict.get(p_id))
            
            para_style = ParagraphStyle(p_id,**para_style_ant)
            
            
            space_after = para_style.spaceAfter
            leading_after = para_style.leading
            final_space_after = space_after
            final_leading = leading_after
            if p_id == "59999":
                pass
                #print("PAusa")
            if para_style is None:
                print(f"Paragraph vacio: {p_id}")
            
            t_elements = p.findall('.//T')

            full_text = ""
            for j, t in enumerate(t_elements):
                text_parts = []
                text = ""
                                        
                  
                if t.text:
                    text_parts.append(t.text)
                # Procesar variables si existen
                for o in t.findall('O'):
                    object_id = o.get('Id')
                    #Los elementos pueden ser variables, Tables, Elements, Image
                    #id 343 es una tabla
                    #id 98 es una variable
                    #print(f"Procesando Object con Id: {object_id}") 
                    var_value = ""
                    
                    #TODO
                    #Revisar porque la 7 fila de la tabla al no tener datos en una de las celdas no conservo el espacio
                    #Y lo ocupo con la data de la celda que seguia

                    if object_id == "79": 
                        #Flow 271
                        #El id 174 es un element (El element se comporta como un flowarea pero dentro de un flow)
                        #Debo consultar los Id de este elemento para hacer un for como con las hojas
                        #process_elements_by_object(object_id, c)
                        pass
                        #print("Pausa")
                    elif object_id == "349993":
                        pass
                        #print("Pausa")

                     
                    #print(object_id)
                    element = all_elements.get(object_id)
                    if element is None:
                        print(f"❌ No se encontró el elemento con Id: {object_id}")
                        continue
                    node_name = element.tag
                    #print(node_name)
                    if node_name == "Variable":
                        try:
                            variables = config.data_dicts['Variable']
                            full_context = config.full_context
                            var_value = get_variable_value(object_id, variables, full_context,context=context,default="")
                            #var_value = get_variable_value(object_id,context=context,default="")
                        except Exception as e:
                            print(e)
                            exit(1)
                        if var_value is not None:
                            text_parts.append(var_value) 
                    elif node_name == "Table":
                        #continue
                        table = process_table(config,element,page_height,page_width,context=context,c=c,max_width=max_width)
                        
                        # Agregar la tabla como flowable directo, no como texto
                        if text_parts:
                            # Cerrar cualquier texto previo antes de la tabla
                            texto_con_nbsp = re.sub(r' {2,}', lambda match: '&nbsp;' * len(match.group()), ''.join(text_parts).strip())
                            full_text = f'<font name="{font_name}" size="{font_size}" color="{text_color}">{texto_con_nbsp}</font>'
                            para.append(Paragraph(full_text, para_style))
                            text_parts = []

                        para.append(table)  # Añadir la tabla como flowable
                        #PRUEBAS
                        return para, "" # Salir para evitar procesar como texto
                        #continue  # Saltar para evitar procesar como texto
                    elif node_name == "FlowObject":
                        x = parent_offset[0]
                        y = parent_offset[1]
                        #Siempre que se llame de aca es porque el Element ya trae el offset del padre
                        #Se debe marcar la peticion a la funcion para que no sume nuevos offset
                        from pdf.process_elements import process_elements_by_object
                        process_elements_by_object(config, object_id, page_width, page_height, c=c, parent_offset=(x,y), element=True)                    
                    
                    if o.tail:  
                        text_parts.append(o.tail)  # Captura el texto después de <O>
                        
                # Unir todos los fragmentos en una sola cadena de texto
                text = ''.join(text_parts)
                #text = decode_entities(text)
                #Valores por defecto (Creo que no los voy a usar)
                text_color = "black"
                #font_size = float(10) 
                font_id = "Def.Font"
                sub_fonts_text = "Regular"
                font_size_content_ancestor = None
                fill_style_id_content_ancestor = None
                font_id_content_ancestor = None
                sub_font_content_ancestor = None
                fill_style_id = None
                
                t_id = t.get('Id')
                #if text:
                    
                #Def.TextStyleDelta
                text_style_delta = text_styles.get("Def.TextStyle")
                font_size = convert_units(text_style_delta.find("FontSize").text)

                
                text_style = text_styles.get(t_id)
                font_size_content = text_style.find("FontSize")
                fill_style_id_content = text_style.find("FillStyleId")
                font_id_content = text_style.find("FontId")
                sub_font_content = text_style.find("SubFont")
                #Usar el fontsize de la fuente si lo tiene, si no uso el del ancestor

                ancestor_id = text_style.find('AncestorId').text
                #print(t_id)
                if ancestor_id is not None:
                    #ancestor_id = ancestor_id_content.text
                    text_style_ancestor = text_styles.get(ancestor_id)
                    font_size_content_ancestor = text_style_ancestor.find("FontSize")
                    fill_style_id_content_ancestor = text_style_ancestor.find("FillStyleId")
                    font_id_content_ancestor = text_style_ancestor.find("FontId")
                    sub_font_content_ancestor = text_style_ancestor.find("SubFont")

                #Si tengo un ancestor y no tengo font size o fill style uso los datos del ancestor
                #No tengo font content y el ancestor es NONE que debo hacer?
                #Debo tomar el fontsize del default font
                if font_size_content is None:
                    if font_size_content_ancestor is not None:
                        font_size_text = font_size_content_ancestor.text
                        font_size = convert_units(font_size_text)  
                else:
                    font_size_text = font_size_content.text
                    font_size = convert_units(font_size_text)                              
                    
                if fill_style_id_content is None:
                    if fill_style_id_content_ancestor is not None:
                        fill_style_id = fill_style_id_content_ancestor.text
                else:
                    fill_style_id = fill_style_id_content.text
                                                    
                if font_id_content is None:
                    if font_id_content_ancestor is not None:
                        font_id = font_id_content_ancestor.text
                else:
                    font_id = font_id_content.text
                    
                if sub_font_content is None:
                    if sub_font_content_ancestor is not None:
                        sub_fonts_text = sub_font_content_ancestor.text
                else:
                    sub_fonts_text = sub_font_content.text
                    

                        
                #Buscar el fill
                if fill_style_id is not None:
                    fill_style = fill_styles.get(fill_style_id)
                    #Buscar el ColorId
                    color_id_content = fill_style.find("ColorId")
                    
                    #hay unos fillStyle que no tienen ColorId porque son de tipo gradient <Type>Gradient</Type>                        
                    if color_id_content is not None:
                        #buscar id de color en Color_Reportlab
                        color_id = color_id_content.text
                        text_color = colors.get(color_id)
                    #TODO
                    #Revisar el Type del fillStyle, si es gradient debo manejarlo
                

                fonts_config_xml = fonts_config_dict.get(font_id)
                font_name_text = fonts_config_xml.find('FontName').text                        
                font_name = f"{font_name_text}-{sub_fonts_text}"
                                                            

                #print(f"font2: {font_size_text}")                                                       
                #print(f"font: {font_size}")   
                    
                '''
                if len(p_elements) > 1:
                    if space_after == 0.0:
                        final_space_after = font_size + 1.8
                    else: 
                        final_space_after = space_after + font_size + 1.8
                '''
                if flow_type == "FirstFittingAuto":
                    #print("FirstFittingAuto")
                    text_width = stringWidth(text, font_name, font_size)
                    if text_width > max_width:
                        use_percent_decent = flow_element.find("UsePercentDecent")
                        use_percent_decent = use_percent_decent is not None and use_percent_decent.text.lower() == "true"
                        iteration_count_element = flow_element.find("IterationCount")
                        max_iterations = int(iteration_count_element.text) if iteration_count_element is not None else 10
                        # Realizar reduccion de fuente por porcentajes
                        if use_percent_decent:
                            percent_font_decent_elem = flow_element.find("PercentFontDecent")
                            percent_font_decent = float(percent_font_decent_elem.text) if percent_font_decent_elem is not None else 90.0
                            percent_font_decent = percent_font_decent / 100.0  # e.g. 90 -> 0.9
                        
                        # Realizar reduccion de fuente por puntos
                        else:
                            font_point_decent_elem = flow_element.find("PointFontDecent")
                            font_point_decent = float(font_point_decent_elem.text) if font_point_decent_elem is not None else 1.0

                        #text_width = stringWidth(text, font_name, font_size)
                        iterations = 0
                        min_font_size = 4  # Define un mínimo para evitar fuentes ilegibles

                        while text_width > max_width and font_size > min_font_size and iterations < max_iterations:
                            if use_percent_decent:
                                new_font_size = font_size - (font_size * percent_font_decent)
                                font_size = max(new_font_size, min_font_size)
                            else:
                                font_size = max(font_size - font_point_decent, min_font_size)
                            text_width = stringWidth(text, font_name, font_size)
                            iterations += 1
                    
                
                
                #if (len(t_elements) == 1):
                if leading_after == 0.0:
                    final_leading = font_size + 1.5
                    #final_leading = font_size + 1.8
                    '''
                    if text_width <= s_x:
                        final_leading = leading_after                                
                        print("Texto cabe")
                    else:
                        #final_leading = font_size * 1.2
                        final_leading = font_size + 1.5
                        print("Texto No cabe")
                    '''
                
                para_style.spaceAfter = final_space_after
                para_style.leading = final_leading

                #Dar manejo a los espacios en blanco
                #Reemplazar los espacios en blanco por &nbsp; para evitar que se colapse
                texto_con_nbsp = re.sub(r' {2,}', lambda match: '&nbsp;' * len(match.group()), text)

                full_text += f'<font name="{font_name}" size="{font_size}" color="{text_color}">{texto_con_nbsp}</font>'
                

            #print(full_text)
            if "IVA 19%" in full_text:
                pass
                #print("Pausa")

            para.append(Paragraph(full_text, para_style))
                #Reestablecer valor modificado
                #para_style.spaceAfter = space_after
        return para, font_size