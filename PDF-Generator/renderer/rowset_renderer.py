from core.utils import convert_units
from core.utils import evaluate_condition_v2
from renderer.cell_renderer import process_cell

from reportlab.lib import colors

def process_rowset(config, rowset_element, page_height, page_width, context=None, c=None, col_widths=[]):
    """Procesa un RowSet del XML y lo convierte a formato ReportLab"""
    rowset_type = rowset_element.find("RowSetType").text
    min_height = 0
    row_index = 0
    cell_styles = []
    row = []
    # Cuando el RowSetType es InlCond no trae la informacion de SubRowId
    register = config.full_context
    if context is None:
        context = config.full_context
    all_elements = config.all_elements
    borderstyle_reportlab = config.borderstyle_reportlabs
    fillstyle_config = config.config_dicts['FillStyle']
    colors_reportlab = config.colors_reportlabs
    if rowset_type == "InlCond":
        rowset_conditions = rowset_element.findall('RowSetCondition')
        for rowset_condition in rowset_conditions:
            subrow = rowset_condition.find('SubRowId')
            condition = rowset_condition.find('Condition').text
            # El rowset por defecto se define por un nodo "Condition" vacio
            if condition is None:
                row, min_height, cell_styles = process_rowset(config,all_elements.get(subrow.text),page_height,page_width,context=context,c=c,col_widths=col_widths)

                return row, min_height, cell_styles
            elif evaluate_condition_v2(condition, register):
                row, min_height, cell_styles = process_rowset(config,all_elements.get(subrow.text),page_height,page_width,context=context,c=c,col_widths=col_widths)
                
                return row, min_height, cell_styles
    elif rowset_type == "RowSet": 
        subrow_id_elements = rowset_element.findall('SubRowId')
        for subrow_id_element in subrow_id_elements:
            subrow_element = all_elements.get(subrow_id_element.text)
            row, min_height, cell_styles = process_rowset(config,subrow_element,page_height,page_width,context=context,c=c,col_widths=col_widths)
            
            return row, min_height, cell_styles
    elif rowset_type == "Row": #Single Row and Repeated
        subrow_id_elements = rowset_element.findall("SubRowId")            
        for col_index, subrow_id_element in enumerate(subrow_id_elements):
            subrow_id = subrow_id_element.text
            if subrow_id == "437": #Revisar desde aca
                pass
                #print("Pausa")
            cell_element = all_elements.get(subrow_id)
            if cell_element is not None:
                cell, min_height_default = process_cell(config,cell_element,page_height,page_width,context=context,c=c,col_widths=col_widths,col_index=col_index)
                
                # Leer MinHeight si existe
                min_height_str = cell_element.find("MinHeight").text                    
                
                if min_height_str:
                    # Antes de validar debo convertir las unidades
                    min_height_aux = convert_units(min_height_str)
                    min_height = max(min_height, float(min_height_aux))
                
                # Leer alineación vertical
                valign = cell_element.find("CellVerticalAlignment", "").text.strip().upper()
                if valign in ("TOP", "CENTER", "BOTTOM"):
                    cell_styles.append(("VALIGN", (col_index, 0), (col_index, 0), valign))

                

                border_id = cell_element.find("BorderId", "").text
                if border_id and border_id in borderstyle_reportlab:
                    border_conf = borderstyle_reportlab[border_id]

                    # Fondo desde FillStyle asociado al BorderStyle (solo si lo tiene)
                    fill_id = border_conf.get("fill_style_id")
                    if fill_id and fill_id in fillstyle_config:
                        color_id = fillstyle_config[fill_id].find("ColorId").text
                        bg_color = colors_reportlab.get(color_id, "#000000")  # Default to black if not found

                        #bg_color = FillStyle_config[fill_id].get("color")
                        if bg_color:
                            cell_styles.append(("BACKGROUND", (col_index, 0), (col_index, 0), colors.HexColor(bg_color)))

                    # Bordes por lado
                    for side, props in border_conf["sides"].items():
                        width = props.get("width", 0.25)
                        color = props.get("color", "#000000")
                        if color:
                            try:
                                color_obj = colors.HexColor(color)
                            except Exception as e:
                                print(f"Color inválido: {color} → {e}")
                                color_obj = colors.black  # color por defecto
                        else:
                            color_obj = colors.black  # o None si prefieres no aplicar


                        if side == "LEFT":
                            cell_styles.append(("LINEBEFORE", (col_index, 0), (col_index, 0), width, color_obj))
                        elif side == "RIGHT":
                            cell_styles.append(("LINEAFTER", (col_index, 0), (col_index, 0), width, color_obj))
                        elif side == "TOP":
                            cell_styles.append(("LINEABOVE", (col_index, 0), (col_index, 0), width, color_obj))
                        elif side == "BOTTOM":
                            cell_styles.append(("LINEBELOW", (col_index, 0), (col_index, 0), width, color_obj))


                row.append(cell)
                
            else:
                row.append("")  # Celda vacía si no existe el elemento
        #Reasignar el min_height cuando es 0 (Para dar solucion a las filas que tienen todas sus celdas vacias)          
        if min_height == 0:
            min_height = min_height_default

        return row, min_height, cell_styles
    
    else:
        raise ValueError(f"Tipo de RowSet desconocido: {rowset_type}")