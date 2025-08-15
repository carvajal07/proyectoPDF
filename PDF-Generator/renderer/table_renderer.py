from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

from core.utils import convert_units
from core.utils import get_variable_value
from core.utils import evaluate_condition_v2
from renderer.rowset_renderer import process_rowset

def create_table_style(table_element):
    """
    Crea un TableStyle a partir de los atributos XML del nodo <Table>.
    """
    style_commands = []

    # ─────────── Bordes (según BordersType) ───────────
    borders_type = table_element.findtext('BordersType', '').strip()
    if borders_type == "MergeBorders":
        #style_commands.append(('BOX', (0, 0), (-1, -1), 0.5, colors.black))
        #style_commands.append(('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey))
        pass
    elif borders_type == "All":
        style_commands.append(('GRID', (0, 0), (-1, -1), 0.25, colors.black))
    elif borders_type == "None":
        pass  # No se aplican bordes
    else:
        #style_commands.append(('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey))
        pass

    # ─────────── Espaciado entre celdas ───────────
    h_spacing = table_element.findtext('HorizontalCellSpacing')
    v_spacing = table_element.findtext('VerticalCellSpacing')
    if h_spacing is not None:
        style_commands.append(('LEFTPADDING', (0, 0), (-1, -1), float(h_spacing)))
        style_commands.append(('RIGHTPADDING', (0, 0), (-1, -1), float(h_spacing)))
    if v_spacing is not None:
        style_commands.append(('TOPPADDING', (0, 0), (-1, -1), float(v_spacing)))
        style_commands.append(('BOTTOMPADDING', (0, 0), (-1, -1), float(v_spacing)))

    # ─────────── Alineación ───────────
    alignment = table_element.findtext('TableAlignment', '').strip().lower()
    if alignment == "center":
        style_commands.append(('ALIGN', (0, 0), (-1, -1), 'CENTER'))
    elif alignment == "right":
        style_commands.append(('ALIGN', (0, 0), (-1, -1), 'RIGHT'))
    else:
        style_commands.append(('ALIGN', (0, 0), (-1, -1), 'LEFT'))

    # Devuelve el estilo para aplicar al objeto Table
    return TableStyle(style_commands) 

def get_column_widths(columns_elements, table_width):
    col_widths = []
    for col_elem in columns_elements:
        percent_elem = col_elem.find("PercentWidth")
        min_width_elem = col_elem.find("MinWidth")
        pct = float(percent_elem.text) if percent_elem is not None else 0.0
        col_width = table_width * pct

        if min_width_elem is not None:
            min_width = convert_units(float(min_width_elem.text))
            col_width = max(col_width, min_width)
        col_widths.append(col_width)
    return col_widths

def process_table(config, table_element, page_height, page_width, c=None, context=None, max_width=0):
    """Procesa una tabla del XML y la convierte a formato ReportLab"""
    #SubRowId
    #VariableId
    
    #Rowset llama a Row
    #Repeated llama a Row
    #InlCond llama a Row
    register = config.full_context
    if context is None:
        context = config.full_context
    all_elements = config.all_elements
    table_data = []
    table_style = create_table_style(table_element)
    rowset_id = table_element.find("RowSetId").text
    table_column_width_objects = table_element.findall("ColumnWidths")
    
    col_widths = get_column_widths(table_column_width_objects,max_width)


    if rowset_id == "341":
        pass
        #print("Pausa")
    rowset_element = all_elements.get(rowset_id)
    
    rowset_type = rowset_element.find("RowSetType").text if rowset_element.find("RowSetType") is not None else ""
    rows = []
    row_index = 0
    row_heights = []

    if rowset_id == "435":
        pass
        #print("Pausa")
    
    # Row
    # Repeated
    # InlCond
    # Rowset (Multiple)
    # Select by

    if rowset_type == 'Row':
        #Enviar directamente a process_rowset
        row, min_height, cell_styles = process_rowset(config,rowset_element,page_height,page_width,c=context,col_widths=col_widths)
        if row:
            rows.append(row)
            row_heights.append(min_height if min_height > 0 else None)
            row_index = len(rows) - 1
            for style in cell_styles:
                cmd = style[0]
                if cmd in ("VALIGN", "BACKGROUND"):
                    _, (col, _), (_, _), value = style
                    table_style.add(cmd, (col, row_index), (col, row_index), value)
                elif cmd in ("LINEBEFORE", "LINEAFTER", "LINEABOVE", "LINEBELOW"):
                    _, (col, _), (_, _), width, color = style
                    table_style.add(cmd, (col, row_index), (col, row_index), width, color)
                else:
                    print("Estilo desconocido:", style)
    elif rowset_type == 'RowSet' or rowset_type == "HeaderFooter":
        #No lleva variable
        
        subrows = rowset_element.findall('SubRowId')
        for subrow in subrows:
            #Validar que tipo de rowset es
            subrowset_element = all_elements.get(subrow.text)
            if subrowset_element is None:
                continue
            subrowset_type = subrowset_element.find("RowSetType").text
            if subrowset_type == 'Repeated':
                subrow_id_element = subrowset_element.find('SubRowId')
                variable_id_element = subrowset_element.find('VariableId')

                try:
                    #Capturar la variable que pertenece a un array dentro del json
                    #Hacer un len al array del json
                    variables = config.data_dicts['Variable']
                    full_context = config.full_context
                    repeat_array = get_variable_value(variable_id_element.text, variables, full_context)
                    #repeat_array = get_variable_value(variable_id_element.text)
                    #repeat_array = register.get(variable_name, 1)
                    
                    if variable_id_element.text is None:
                        print("La tabla tiene configurado el rowset como Repeated pero no tiene configurado el array de repeticion")
                        #sys.exit(1)
                        # Dar manejo para que no genere error y los valores a pintar sean vacios
                        # Crear un solo elemento en el array
                        repeat_array = [None]
                    elif not isinstance(repeat_array, list):
                        raise ValueError(f"La variable con ID {variable_id_element.text} no es una lista válida.")

                    for item in repeat_array:

                        subrow_element = all_elements.get(subrow_id_element.text)
                        row, min_height, cell_styles = process_rowset(config,subrow_element,page_height,page_width,context=item,c=c,col_widths=col_widths)

                        if row:
                            rows.append(row)  # row es una lista con una única fila
                            row_heights.append(min_height if min_height > 0 else None)

                            for style in cell_styles:
                                cmd = style[0]
                                if cmd in ("VALIGN", "BACKGROUND"):
                                    _, (col, _), (_, _), value = style
                                    table_style.add(cmd, (col, row_index), (col, row_index), value)
                                elif cmd in ("LINEBEFORE", "LINEAFTER", "LINEABOVE", "LINEBELOW"):
                                    _, (col, _), (_, _), width, color = style
                                    table_style.add(cmd, (col, row_index), (col, row_index), width, color)
                                else:
                                    print("Estilo desconocido:", style)

                            row_index += 1


                except Exception as e:
                    print(f"Error al procesar RowSet Repeated con variable {variable_id_element.text}: {e}")
            else:
                row, min_height, cell_styles = process_rowset(config,all_elements.get(subrow.text),page_height,page_width,c=c,col_widths=col_widths)
            
            if row:
                rows.append(row)
                row_heights.append(min_height if min_height > 0 else None)
                row_index = len(rows) - 1
                for style in cell_styles:
                    cmd = style[0]
                    if cmd in ("VALIGN", "BACKGROUND"):
                        _, (col, _), (_, _), value = style
                        table_style.add(cmd, (col, row_index), (col, row_index), value)
                    elif cmd in ("LINEBEFORE", "LINEAFTER", "LINEABOVE", "LINEBELOW"):
                        _, (col, _), (_, _), width, color = style
                        table_style.add(cmd, (col, row_index), (col, row_index), width, color)
                    else:
                        print("Estilo desconocido:", style)
            
    elif rowset_type == 'Repeated':
        #Solo lleva un Subrow y un variableId
        subrow_id_element = rowset_element.find('SubRowId')
        variable_id_element = rowset_element.find('VariableId')
        
        try:
            #Capturar la variable que pertenece a un array dentro del json
            #Hacer un len al array del json
            variables = config.data_dicts['Variable']
            full_context = config.full_context
            repeat_array = get_variable_value(variable_id_element.text, variables, full_context)
            #repeat_array = get_variable_value(variable_id_element.text)
            #repeat_array = register.get(variable_name, 1)
            if variable_id_element.text is None:
                print("La tabla tiene configurado el rowset como Repeated pero no tiene configurado el array de repeticion")
                #sys.exit(1)
                # Dar manejo para que no genere error y los valores a pintar sean vacios
                # Crear un solo elemento en el array
                repeat_array = [None]
            elif not isinstance(repeat_array, list):
                raise ValueError(f"La variable con ID {variable_id_element.text} no es una lista válida.")

            for item in repeat_array:

                subrow_element = all_elements.get(subrow_id_element.text)
                row, min_height, cell_styles = process_rowset(config,subrow_element,page_height,page_width,context=item,c=c,col_widths=col_widths)

                if row:
                    rows.append(row)  # row es una lista con una única fila
                    row_heights.append(min_height if min_height > 0 else None)

                    for style in cell_styles:
                        cmd = style[0]
                        if cmd in ("VALIGN", "BACKGROUND"):
                            _, (col, _), (_, _), value = style
                            table_style.add(cmd, (col, row_index), (col, row_index), value)
                        elif cmd in ("LINEBEFORE", "LINEAFTER", "LINEABOVE", "LINEBELOW"):
                            _, (col, _), (_, _), width, color = style
                            table_style.add(cmd, (col, row_index), (col, row_index), width, color)
                        else:
                            print("Estilo desconocido:", style)

                    row_index += 1


        except Exception as e:
            print(f"Error al procesar RowSet Repeated con variable {variable_id_element.text}: {e}")

    elif rowset_type == 'InlCond':
        #Puede llevar varios Rowset condition
        rowset_conditions = rowset_element.findall('RowSetCondition')
        for rowset_condition in rowset_conditions:
            subrow = rowset_condition.find('SubRowId')
            condition = rowset_condition.find('Condition').text
            # El rowset por defecto se define por un nodo "Condition" vacio
            if condition is None:
                row, min_height, cell_styles = process_rowset(config,all_elements.get(subrow.text),page_height,page_width,c=c,col_widths=col_widths)
                if row:
                    rows.append(row)
                    row_heights.append(min_height if min_height > 0 else None)
                    #row_index = len(rows) - 1
                    for style in cell_styles:
                        cmd = style[0]
                        if cmd in ("VALIGN", "BACKGROUND"):
                            _, (col, _), (_, _), value = style
                            table_style.add(cmd, (col, row_index), (col, row_index), value)
                        elif cmd in ("LINEBEFORE", "LINEAFTER", "LINEABOVE", "LINEBELOW"):
                            _, (col, _), (_, _), width, color = style
                            table_style.add(cmd, (col, row_index), (col, row_index), width, color)
                        else:
                            print("Estilo desconocido:", style)
                    row_index += 1
                break
            elif evaluate_condition_v2(condition, register):
                row, min_height, cell_styles = process_rowset(config,all_elements.get(subrow.text),page_height,page_width,c=c,col_widths=col_widths)
                if row:
                    rows.append(row)
                    row_heights.append(min_height if min_height > 0 else None)
                    #row_index = len(rows) - 1
                    for style in cell_styles:
                        cmd = style[0]
                        if cmd in ("VALIGN", "BACKGROUND"):
                            _, (col, _), (_, _), value = style
                            table_style.add(cmd, (col, row_index), (col, row_index), value)
                        elif cmd in ("LINEBEFORE", "LINEAFTER", "LINEABOVE", "LINEBELOW"):
                            _, (col, _), (_, _), width, color = style
                            table_style.add(cmd, (col, row_index), (col, row_index), width, color)
                        else:
                            print("Estilo desconocido:", style)
                    row_index += 1
    
    table_data.extend(rows)

    return Table(table_data, style=table_style,rowHeights=row_heights,colWidths=col_widths)
