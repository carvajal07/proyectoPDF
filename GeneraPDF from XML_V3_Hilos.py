import io
import re
import os
import sys
import json
import copy
import math
import fitz
import time

import qrcode
from reportlab.lib.units import mm

from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
import logging
import operator
import threading
from PIL import Image
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from reportlab.pdfbase import pdfdoc
from reportlab.lib.colors import HexColor
from decimal import Decimal
from xml.etree import ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Frame, Paragraph, Table, TableStyle

from reportlab.graphics.barcode import code39, code128, eanbc
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

inicio = time.time()
layout_container = "Layout/Layout/"
object_types = [
    "Variable",
    "Page",
    "Font",
    "FlowArea",
    "Flow",
    "FlowObject",
    "PathObject",
    "ImageObject",
    "Image",
    "Barcode",
    "Chart",
    "ParaStyle",
    "BorderStyle",
    "TextStyle",
    "FillStyle",
    "Color",
    "Table",
    "RowSet",
    "Cell"
]

#Objetos omitidos
#-Data
#-Group

class XMLToPDFConverter:
    def __init__(self, xml_content):
        self.workflow = ET.fromstring(xml_content)
        self.register = {}

        #_config son los elementos del arbol
        #Estos contienen el nombre y quien es su padre
        self.page_width = 0
        self.page_height = 0
        self.grouped_nodes = {}
        self.all_elements = {}
        self.images_cache = {}
        
        for object_type in object_types:
            setattr(self, f"{object_type}_data", {})
            setattr(self, f"{object_type}_config", {})
            setattr(self, f"{object_type}_reportlab", {})
        
        self.variables_system = []
                      
    def convert_units(self, value):
        """Convierte las unidades del XML de metros a puntos para ReportLab"""
        value = Decimal(value) 
        #return float(value * Decimal(1000) * Decimal(mm))
        return float(value * Decimal(72) * Decimal(39.3701))  # Convertir metros a puntos (72 puntos = 1 inch, 39.37 inches = 1 metro)
            
    def get_variable_value(self, var_id, context=None, default=None):
        """Obtiene el valor real de una variable desde el JSON (self.register) usando la jerarquía definida por ParentId."""
        def resolve_hierarchy_path(variable_id):
            """Construye la ruta jerárquica completa basada en los ParentId."""
            path = []
            current_id = variable_id
            variable_objects = getattr(self, "Variable_data")

            # current_id 0 es el nodo principal
            #while current_id and current_id != "0":
            while current_id:
                variable_object = variable_objects.get(current_id)
                if variable_object is None:
                    break

                name_elem = variable_object.find('Name')
                name = name_elem.text if name_elem is not None else None
                # 🚩 OMITE 'Value'
                if name and name != "Value":
                    path.insert(0, name)  # Insertamos al principio para construir la ruta

                parent_elem = variable_object.find('ParentId')
                current_id = parent_elem.text if parent_elem is not None else None

            return path

        def get_value_from_path(data, path):
            """Navega el diccionario usando la ruta para obtener el valor."""
            # Si el contexto no tiene las claves iniciales las omito
            while path and not (isinstance(data, dict) and path[0] in data):
                path.pop(0)

            for key in path:
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    # Retornar valor por defecto cuando no sea necesario validar la existencia del path
                    if default is not None:
                        return default
                    else:
                        raise ValueError(f"ERROR: No se encontró la clave '{key}' en el path '{' -> '.join(path)}'")
            # Transformar los valores numericos a String para evitar problemas en los join de los textos
            if isinstance(data, (int, float, Decimal)) and not isinstance(data, bool):        
                data = str(data)
            
            return data

        # Construimos el path desde la raíz hasta la variable actual
        full_path = resolve_hierarchy_path(var_id)
        if context is None:
            context = self.register

        return get_value_from_path(context, full_path)
    
    def evaluate_condition_v2(self, condition_str, context):
        """
        Evalúa condiciones complejas con operadores, métodos simulados,
        `not`, `and`, `or` y paréntesis.
        """

        ops = {
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            ">=": operator.ge,
            "<": operator.lt,
            "<=": operator.le,
        }

        simulated_methods = {
            "equalCaseInsensitive": lambda a, b: str(a).lower() == b.lower(),
            "beginWithCaseInsensitive": lambda a, b: str(a).lower().startswith(b.lower()),
            "endsWithCaseInsensitive": lambda a, b: str(a).lower().endswith(b.lower()),
            "contains": lambda a, b: b in str(a),
            "equalCase": lambda a, b: str(a) == b,
            "beginWith": lambda a, b: str(a).startswith(b),
            "endsWith": lambda a, b: str(a).endswith(b),
        }

        def get_value_from_path(path):
            parts = path.strip().split('.')
            val = context
            for p in parts:
                if isinstance(val, dict) and p in val:
                    val = val[p]
                else:
                    raise KeyError(f"No se encontró '{path}' en el contexto.")
            return val

        def eval_single(expr):
            expr = expr.strip()

            # Evalúa métodos simulados
            for method_name, method_func in simulated_methods.items():
                pattern = f".{method_name}("
                if pattern in expr:
                    try:
                        field_part, arg = expr.split(pattern, 1)
                        field = field_part.strip()
                        expected = arg.strip().rstrip(")").strip('"').strip("'")
                        actual = get_value_from_path(field)
                        return method_func(actual, expected)
                    except Exception as e:
                        raise ValueError(f"Error evaluando {method_name}: {expr} → {e}")

            # Evalúa operadores normales
            for op_str, op_func in ops.items():
                if op_str in expr:
                    left, right = expr.split(op_str, 1)
                    left = left.strip()
                    right = right.strip().strip('"').strip("'")
                    actual_value = get_value_from_path(left)
                    return op_func(str(actual_value), right)

            # Evalúa condición booleana directa
            val = get_value_from_path(expr)
            return bool(val)

        def safe_eval(expr):
            expr = expr.strip()
            if expr.startswith("not "):
                inner = expr[4:].strip()
                return not safe_eval(inner)
            elif expr.startswith("(") and expr.endswith(")"):
                return safe_eval(expr[1:-1])
            else:
                return eval_single(expr)

        def split_and_or(expression):
            """
            Divide la expresión preservando paréntesis (anidación).
            Retorna tokens conectados por `and` / `or`.
            """
            tokens = []
            depth = 0
            token = ''
            i = 0
            while i < len(expression):
                c = expression[i]
                if c == '(':
                    depth += 1
                    token += c
                elif c == ')':
                    depth -= 1
                    token += c
                elif depth == 0 and expression[i:i+4] == ' and':
                    tokens.append(token.strip())
                    token = ''
                    i += 3  # saltar 'and'
                elif depth == 0 and expression[i:i+3] == ' or':
                    tokens.append(token.strip())
                    token = ''
                    i += 2  # saltar 'or'
                else:
                    token += c
                i += 1
            if token:
                tokens.append(token.strip())
            return tokens

        # Normaliza espacios
        condition_str = re.sub(r'\s*or\s*', ' or ', condition_str)
        condition_str = re.sub(r'\s*and\s*', ' and ', condition_str)

        # Manejo de `or` y `and` de forma segura
        if ' or ' in condition_str:
            parts = split_and_or(condition_str)
            return any(safe_eval(p) for p in parts)

        if ' and ' in condition_str:
            parts = split_and_or(condition_str)
            return all(safe_eval(p) for p in parts)

        return safe_eval(condition_str)

    def evaluate_condition(self, condition_str,context):
        """
        Evalúa condiciones simples o múltiples (con 'and' / 'or') sobre un dict anidado.
        Ej: 'Documents.Direccion == "ERROR" or Documents.Channel == "OTRA"'
        Return True o False según la condición.
        """
        # Normalizar espacios alrededor de 'and' y 'or'
        condition_str = re.sub(r'\s*or\s*', ' or ', condition_str)
        condition_str = re.sub(r'\s*and\s*', ' and ', condition_str)
        # Normalizar el array principal Documents.
        condition_str = condition_str.replace(f"{principal_array}.", "")
        ops = {
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            ">=": operator.ge,
            "<": operator.lt,
            "<=": operator.le,
        }

        def get_value_from_path(path):
            parts = path.strip().split('.')
            val = context
            for p in parts:
                if isinstance(val, dict) and p in val:
                    val = val[p]
                else:
                    raise KeyError(f"No se encontró '{path}' en el contexto.")
            return val

        def eval_single(expr):
            for op_str, op_func in ops.items():
                if op_str in expr:
                    left, right = expr.split(op_str, 1)
                    left = left.strip()
                    right = right.strip().strip('"').strip("'")
                    actual_value = get_value_from_path(left)
                    return op_func(str(actual_value), right)
            # ⚠️ No hay operador: asumimos evaluación booleana directa
            try:
                val = get_value_from_path(expr.strip())
                return bool(val)
            except Exception as e:
                raise ValueError(f"No se puede evaluar la condición: '{expr}'. {e}")

        # Soporte para 'or' y 'and'
        if ' or ' in condition_str:
            parts = [p.strip() for p in condition_str.split(' or ')]
            return any(eval_single(p) for p in parts)

        if ' and ' in condition_str:
            parts = [p.strip() for p in condition_str.split(' and ')]
            return all(eval_single(p) for p in parts)

        # Solo una condición simple
        return eval_single(condition_str)

    def get_column_widths(self, columns_elements, table_width):
        col_widths = []
        for col_elem in columns_elements:
            percent_elem = col_elem.find("PercentWidth")
            min_width_elem = col_elem.find("MinWidth")
            pct = float(percent_elem.text) if percent_elem is not None else 0.0
            col_width = table_width * pct

            if min_width_elem is not None:
                min_width = self.convert_units(float(min_width_elem.text))
                col_width = max(col_width, min_width)
            col_widths.append(col_width)
        return col_widths

    def process_chart(self, chart_object, c, parent_offset=(0,0)):
        offset_x = parent_offset[0]
        offset_y = parent_offset[1]

        chart_object_id = chart_object.find('Id').text
        chart_objects = getattr(self,"Chart_config")
        chart_object = chart_objects.get(chart_object_id)
        
        # 1. Extraer posición y tamaño (en metros) y convertir a puntos
        pos = chart_object.find("Pos")
        size = chart_object.find("Size")
        x = self.convert_units(pos.get("X", 0))
        y = self.convert_units(pos.get("Y", 0))
        w = self.convert_units(size.get("X", 1))
        h = self.convert_units(size.get("Y", 1))

        # 2. Obtener el tipo de gráfico
        chart_type_elem = chart_object.find("Chart_Type")
        chart_type = chart_type_elem.text if chart_type_elem is not None else "Bar"
        
        # 3. Obtener el título del gráfico (opcional)
        title_elem = chart_object.find("Chart_Title")
        chart_title = title_elem.text if title_elem is not None else ""

        # 4. Obtener los datos de la(s) Serie(s)
        serie = chart_object.find("Serie")
        values = []
        labels = []
        if serie is not None:
            for item in serie.findall("SerieItem"):
                value_elem = item.find("Value")
                if value_elem is not None:
                    values.append(float(value_elem.text))
                label_elem = item.find("Label")
                labels.append(label_elem.text if label_elem is not None else "")

        # 5. Crear el Drawing (contenedor)
        drawing = Drawing(w, h)
        
        # 6. Construir el gráfico según el tipo
        if chart_type.lower() == "bar":
            bc = VerticalBarChart()
            bc.x = 0
            bc.y = 0
            bc.width = w
            bc.height = h
            bc.data = [values]
            bc.categoryAxis.categoryNames = labels if any(labels) else [str(i+1) for i in range(len(values))]
            bc.valueAxis.valueMin = 0
            drawing.add(bc)
        elif chart_type.lower() == "line":
            lc = HorizontalLineChart()
            lc.x = 0
            lc.y = 0
            lc.width = w
            lc.height = h
            lc.data = [values]
            lc.categoryAxis.categoryNames = labels if any(labels) else [str(i+1) for i in range(len(values))]
            lc.valueAxis.valueMin = 0
            drawing.add(lc)
        elif chart_type.lower() == "pie":
            pie = Pie()
            pie.x = w/2
            pie.y = h/2
            pie.width = w
            pie.height = h
            pie.data = values
            pie.labels = labels if any(labels) else [str(i+1) for i in range(len(values))]
            drawing.add(pie)
        else:
            # Puedes agregar más tipos según lo que permita reportlab o tus necesidades
            raise NotImplementedError(f"Tipo de gráfico no soportado: {chart_type}")

        # 7. Dibujar el chart en el PDF en la posición adecuada
        renderPDF.draw(drawing, c, x, y)

        # 8. Opcional: agregar el título si existe
        if chart_title:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x, y + h + 10, chart_title)

    def process_table(self, table_element, c=None, context=None,max_width=0):
        """Procesa una tabla del XML y la convierte a formato ReportLab"""
        #SubRowId
        #VariableId
        
        #Rowset llama a Row
        #Repeated llama a Row
        #InlCond llama a Row
        if context is None:
            context = self.register
        
        table_data = []
        table_style = self.create_table_style(table_element)
        rowset_id = table_element.find("RowSetId").text
        table_column_width_objects = table_element.findall("ColumnWidths")
        
        col_widths = self.get_column_widths(table_column_width_objects,max_width)


        if rowset_id == "341":
            print("Pausa")
        rowset_element = self.all_elements.get(rowset_id)
        
        rowset_type = rowset_element.find("RowSetType").text if rowset_element.find("RowSetType") is not None else ""
        rows = []
        row_index = 0
        row_heights = []

        if rowset_id == "435":
            print("Pausa")
        
        # Row
        # Repeated
        # InlCond
        # Rowset (Multiple)
        # Select by

        if rowset_type == 'Row':
            #Enviar directamente a process_rowset
            row, min_height, cell_styles = self.process_rowset(rowset_element,c=context,col_widths=col_widths)
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
                subrowset_element = self.all_elements.get(subrow.text)
                if subrowset_element is None:
                    continue
                subrowset_type = subrowset_element.find("RowSetType").text
                if subrowset_type == 'Repeated':
                    subrow_id_element = subrowset_element.find('SubRowId')
                    variable_id_element = subrowset_element.find('VariableId')

                    try:
                        #Capturar la variable que pertenece a un array dentro del json
                        #Hacer un len al array del json
                        repeat_array = self.get_variable_value(variable_id_element.text)
                        #repeat_array = self.register.get(variable_name, 1)
                        
                        if variable_id_element.text is None:
                            print("La tabla tiene configurado el rowset como Repeated pero no tiene configurado el array de repeticion")
                            #sys.exit(1)
                            # Dar manejo para que no genere error y los valores a pintar sean vacios
                            # Crear un solo elemento en el array
                            repeat_array = [None]
                        elif not isinstance(repeat_array, list):
                            raise ValueError(f"La variable con ID {variable_id_element.text} no es una lista válida.")

                        for item in repeat_array:

                            subrow_element = self.all_elements.get(subrow_id_element.text)
                            row, min_height, cell_styles = self.process_rowset(subrow_element,context=item,c=c,col_widths=col_widths)

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
                    row, min_height, cell_styles = self.process_rowset(self.all_elements.get(subrow.text),c=c,col_widths=col_widths)
                
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
                repeat_array = self.get_variable_value(variable_id_element.text)
                #repeat_array = self.register.get(variable_name, 1)
                if variable_id_element.text is None:
                    print("La tabla tiene configurado el rowset como Repeated pero no tiene configurado el array de repeticion")
                    #sys.exit(1)
                    # Dar manejo para que no genere error y los valores a pintar sean vacios
                    # Crear un solo elemento en el array
                    repeat_array = [None]
                elif not isinstance(repeat_array, list):
                    raise ValueError(f"La variable con ID {variable_id_element.text} no es una lista válida.")

                for item in repeat_array:

                    subrow_element = self.all_elements.get(subrow_id_element.text)
                    row, min_height, cell_styles = self.process_rowset(subrow_element,context=item,c=c,col_widths=col_widths)

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
                    row, min_height, cell_styles = self.process_rowset(self.all_elements.get(subrow.text),c=c,col_widths=col_widths)
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
                elif self.evaluate_condition_v2(condition, self.register):
                    row, min_height, cell_styles = self.process_rowset(self.all_elements.get(subrow.text),c=c,col_widths=col_widths)
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

    def process_rowset(self, rowset_element,context=None,c=None,col_widths=[]):
        """Procesa un RowSet del XML y lo convierte a formato ReportLab"""
        rowset_type = rowset_element.find("RowSetType").text
        min_height = 0
        row_index = 0
        cell_styles = []
        row = []
        # Cuando el RowSetType es InlCond no trae la informacion de SubRowId

        if context is None:
            context = self.register
        if rowset_type == "InlCond":
            rowset_conditions = rowset_element.findall('RowSetCondition')
            for rowset_condition in rowset_conditions:
                subrow = rowset_condition.find('SubRowId')
                condition = rowset_condition.find('Condition').text
                # El rowset por defecto se define por un nodo "Condition" vacio
                if condition is None:
                    row, min_height, cell_styles = self.process_rowset(self.all_elements.get(subrow.text),context=context,c=c,col_widths=col_widths)

                    return row, min_height, cell_styles
                elif self.evaluate_condition_v2(condition, self.register):
                    row, min_height, cell_styles = self.process_rowset(self.all_elements.get(subrow.text),context=context,c=c,col_widths=col_widths)
                    
                    return row, min_height, cell_styles
        elif rowset_type == "RowSet": 
            subrow_id_elements = rowset_element.findall('SubRowId')
            for subrow_id_element in subrow_id_elements:
                subrow_element = self.all_elements.get(subrow_id_element.text)
                row, min_height, cell_styles = self.process_rowset(subrow_element,context=context,c=c,col_widths=col_widths)
                
                return row, min_height, cell_styles
        elif rowset_type == "Row": #Single Row and Repeated
            subrow_id_elements = rowset_element.findall("SubRowId")            
            for col_index, subrow_id_element in enumerate(subrow_id_elements):
                subrow_id = subrow_id_element.text
                if subrow_id == "437": #Revisar desde aca
                    print("Pausa")
                cell_element = self.all_elements.get(subrow_id)
                if cell_element is not None:
                    cell, min_height_default = self.process_cell(cell_element,context=context,c=c,col_widths=col_widths,col_index=col_index)
                    
                    # Leer MinHeight si existe
                    min_height_str = cell_element.find("MinHeight").text                    
                    
                    if min_height_str:
                        # Antes de validar debo convertir las unidades
                        min_height_aux = self.convert_units(min_height_str)
                        min_height = max(min_height, float(min_height_aux))
                    
                    # Leer alineación vertical
                    valign = cell_element.find("CellVerticalAlignment", "").text.strip().upper()
                    if valign in ("TOP", "CENTER", "BOTTOM"):
                        cell_styles.append(("VALIGN", (col_index, 0), (col_index, 0), valign))

                    

                    border_id = cell_element.find("BorderId", "").text
                    if border_id and border_id in self.BorderStyle_config:
                        border_conf = self.BorderStyle_config[border_id]

                        # Fondo desde FillStyle asociado al BorderStyle (solo si lo tiene)
                        fill_id = border_conf.get("fill_style_id")
                        if fill_id and fill_id in self.FillStyle_config:
                            colors_reportlab = getattr(self,"Color_reportlab")
                            color_id = self.FillStyle_config[fill_id].find("ColorId").text
                            bg_color = colors_reportlab.get(color_id, "#000000")  # Default to black if not found

                            #bg_color = self.FillStyle_config[fill_id].get("color")
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

    def process_cell(self, cell_element,context=None,c=None,col_widths=[],col_index=0):
        """Procesa una celda dentro de una fila de la tabla"""
        if context is None:
            context = self.register
        flow_id = cell_element.find("FlowId").text if cell_element.find("FlowId") is not None else None
        max_width = col_widths[col_index]
        #print(f"Procesando celda con FlowId: {flow_id}")
        if flow_id == "293":
            print("Pausa")
        if flow_id:
            flow = self.all_elements.get(flow_id)
        
            if flow is not None:            
                return self.process_flow(flow,context=context,c=c,max_width=max_width)
        return ""  # Celda vacía

    def process_flow(self, flow_element,context=None, c=None, parent_offset=(0,0),max_width=0):
        """Procesa un objeto Flow dentro de una celda y lo convierte en texto o párrafo"""
        if context is None:
            context = self.register
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
                
                if self.evaluate_condition_v2(condition, self.register):
                    #Hacer cambio del flow element por el flow que cumple la condicion
                    new_flow_id = flow_condition_element.text
                    if new_flow_id is None:
                        print("❌ No se encontró el FlowId en la condición.")
                        # Debo retornar un string vacio para que no se pinte nada
                        return para, ""

                    flow_element = self.all_elements.get(new_flow_id)
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
                    flow_element = self.all_elements.get(default_flow_id)

        flow_content = flow_element.find('FlowContent')
        ids_flow_areas_by_pages = getattr(self,"FlowArea_data")
        para_style_dict = getattr(self,"ParaStyle_reportlab")
        fill_styles = getattr(self,"FillStyle_config")
        colors = getattr(self,"Color_reportlab")
        text_styles = self.TextStyle_config
        fonts_config_dict = self.Font_config
        
        p_elements = flow_content.findall('P')
        for i, p in enumerate(p_elements):
            #Crear los paragraph o usarlos
            p_id = p.get('Id')
            #print(f"Procesando Paragraph con Id: {p_id}")
            para_style = copy.copy(para_style_dict.get(p_id))
            space_after = para_style.spaceAfter
            leading_after = para_style.leading
            final_space_after = space_after
            final_leading = leading_after
            if p_id == "59999":
                print("PAusa")
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
                        #self.process_elements_by_object(object_id, self.c)
                        print("Pausa")
                    elif object_id == "349993":
                        print("Pausa")

                     
                    #print(object_id)
                    element = self.all_elements.get(object_id)
                    node_name = element.tag
                    #print(node_name)
                    if node_name == "Variable":
                        try:
                            var_value = self.get_variable_value(object_id,context=context,default="")
                        except Exception as e:
                            print(e)
                            exit(1)
                        if var_value is not None:
                            text_parts.append(var_value) 
                    elif node_name == "Table":
                        #continue
                        table = self.process_table(element,context=context,c=c,max_width=max_width)
                        
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
                        self.process_elements_by_object(object_id, c=c, parent_offset=(x,y), element=True)
                    
                    
                    if o.tail:  
                        text_parts.append(o.tail)  # Captura el texto después de <O>
                        
                # Unir todos los fragmentos en una sola cadena de texto
                text = ''.join(text_parts)
                #text = self.decode_entities(text)
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
                font_size = self.convert_units(text_style_delta.find("FontSize").text)

                
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
                        font_size = self.convert_units(font_size_text)  
                else:
                    font_size_text = font_size_content.text
                    font_size = self.convert_units(font_size_text)                              
                    
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
                    print("FirstFittingAuto")
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
                

            print(full_text)
            if "IVA 19%" in full_text:
                print("Pausa")

            para.append(Paragraph(full_text, para_style))
                #Reestablecer valor modificado
                #para_style.spaceAfter = space_after
        return para, font_size

    def bezier_curve(self, p0, p1, p2, p3, points, steps=20):
        t_values = [i / steps for i in range(steps + 1)]
        for t in t_values:
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
            points.append((x, y))

    def draw_path(self, points, c):
        if not points:
            return

        p = c.beginPath()
        p.moveTo(*points[0])
        for pt in points[1:]:
            p.lineTo(*pt)
        # Se dibuja el path en el canvas, con trazo (stroke) activado y sin relleno (fill)
        c.drawPath(p, stroke=1, fill=1)
        
    def transform_point(self, x, y, m0, m1, m2, m3, m4, m5, scale_x, scale_y, CONVERSION=2834.65):
        """
        Transforma un punto (x, y) usando una matriz de transformación lineal y factores de escala.

        Args:
            x (float): La coordenada x del punto a transformar.
            y (float): La coordenada y del punto a transformar.
            m0 (float): El elemento en la primera fila y primera columna de la matriz de transformación.
            m1 (float): El elemento en la primera fila y segunda columna de la matriz de transformación.
            m2 (float): El elemento en la segunda fila y primera columna de la matriz de transformación.
            m3 (float): El elemento en la segunda fila y segunda columna de la matriz de transformación.
            m4 (float): El elemento en la primera fila y tercera columna de la matriz de transformación (traslación en x).
            m5 (float): El elemento en la segunda fila y tercera columna de la matriz de transformación (traslación en y).
            scale_x (float): El factor de escala para la coordenada x.
            scale_y (float): El factor de escala para la coordenada y.

        Returns:
            tuple: Una tupla que contiene las coordenadas transformadas x e y (x_new, y_new).
        """
        x, y = x * scale_x * CONVERSION, y * scale_y * CONVERSION
        x_new = m0 * x + m2 * y + m4  # Transformación lineal
        y_new = (m1 * x + m3 * y + m5) * -1 + letter[1]  # INVERTIR Y
        return x_new, y_new
    
    def process_path_object(self, path_object_element, c, parent_offset=(0,0)):
        """
        Extrae y dibuja un objeto PathObject del XML.
        Args:
            element_to_process (Element): El elemento XML que contiene el objeto PathObject.
            c (Canvas): El lienzo sobre el cual se dibujará el objeto PathObject.
        Este método realiza las siguientes operaciones:
        1. Extrae las escalas X e Y del elemento XML.
        2. Extrae los valores de transformación del elemento XML.
        3. Extrae y transforma los puntos de los elementos MoveTo, LineTo, CurveTo y ArcTo del Path.
        4. Dibuja el camino transformado en el lienzo.
        """
        """Extrae y dibuja un objeto PathObject del XML"""
        offset_x = parent_offset[0]
        offset_y = parent_offset[1]
        id_path_object = path_object_element.find("Id").text
        path_objects = getattr(self,"PathObject_config")
        path_object = path_objects.get(id_path_object)
        scale_x = float(path_object.find("Scale").get("X", 1))
        scale_y = float(path_object.find("Scale").get("Y", 1))
     
        CONVERSION = 2834.65 #Valor en puntos
        m0 = float(path_object.find("Transformation_M0").text)
        m1 = float(path_object.find("Transformation_M1").text)
        m2 = float(path_object.find("Transformation_M2").text)
        m3 = float(path_object.find("Transformation_M3").text)
        m4 = float(path_object.find("Transformation_M4").text)
        m5 = float(path_object.find("Transformation_M5").text)
        path = path_object.find("Path")
        if path is not None:
            points = []
            for move in path.findall("MoveTo"):
                x, y = self.transform_point(float(move.get("X")), float(move.get("Y")), m0, m1, m2, m3, m4, m5, scale_x, scale_y)
                points.append((x, y))
            for line in path.findall("LineTo"):
                x, y = self.transform_point(float(line.get("X")), float(line.get("Y")), m0, m1, m2, m3, m4, m5, scale_x, scale_y)
                points.append((x, y))
            for curve in path.findall("BezierTo"):
                x1, y1 = self.transform_point(float(curve.get("X1")), float(curve.get("Y1")), m0, m1, m2, m3, m4, m5, scale_x, scale_y)
                x2, y2 = self.transform_point(float(curve.get("X2")), float(curve.get("Y2")), m0, m1, m2, m3, m4, m5, scale_x, scale_y)
                x, y = self.transform_point(float(curve.get("X")), float(curve.get("Y")), m0, m1, m2, m3, m4, m5, scale_x, scale_y)
                self.bezier_curve(points[-1], (x1, y1), (x2, y2), (x, y), points)
            for arc in path.findall("ArcTo"):
                x, y = self.transform_point(float(arc.get("X")), float(arc.get("Y")), m0, m1, m2, m3, m4, m5, scale_x, scale_y)
                points.append((x, y))
            if path.find("ClosePath") is not None:
                points.append(points[0])                                    
            
            
            
            # Se ajusta el path según el tamaño y la posición definidos en el XML:
            # 1. Se lee el tamaño deseado (en metros) y se convierte a puntos.
            size_elem = path_object.find("Size")
            if size_elem is not None:
                desired_width = float(size_elem.get("X", 1)) * CONVERSION
                desired_height = float(size_elem.get("Y", 1)) * CONVERSION
            else:
                desired_width = desired_height = 1  # Valores por defecto
            
            # 2. Se lee la posición deseada (en metros) y se convierte a puntos.
            pos_elem = path_object.find("Pos")
            if pos_elem is not None:
                pos_x = float(pos_elem.get("X", 0)) * CONVERSION + offset_x 
                pos_y = (letter[1] - float(pos_elem.get("Y", 0)) * CONVERSION) - offset_y
                

                #Uno:734.2499117708333
                #dos:1282.3998140708336

                #print(f"x:{offset_x}")
                #print(f"y:{offset_y}")
                #x:37.12502004750002
                #y:548.1499023000003
                #53.2500813541667
                #pos_x = 37.12502004750002
                #pos_y = 548.1499023000003
                #90.37510140166673

                #pos_x = offset_x
                #pos_y = letter[1] - offset_y
                
                #OFFSET del padre
                #x:37.12502004750002
                #y:548.1499023000003

                #print(f"posX1:{pos_x}")
                #print(f"posY1:{pos_x}")
                #pos_x += offset_x
                #pos_y += offset_y
                #print(f"posX2:{pos_x}")
                #print(f"posY2:{pos_x}")
            else:
                pos_x = 0
                pos_y = letter[1]
            
            # 3. Se calcula el "bounding box" del path original
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            current_width = max_x - min_x
            current_height = max_y - min_y
            if current_width == 0:
                current_width = 1
            if current_height == 0:
                current_height = 1
            
            # 4. Se calculan los factores de escala para que el path tenga el tamaño deseado
            scale_factor_x = desired_width / current_width
            scale_factor_y = desired_height / current_height
            
            # 5. Se reescala y se traslada el path:
            adjusted_points = [(((p[0] - min_x) * scale_factor_x) + pos_x,
                                ((p[1] - min_y) * scale_factor_y) + (pos_y- desired_height)) for p in points]
            
            
            fill_styles = {
                "53": (0.2, 0.4, 0.8),  # Ejemplo: azul
                # Agrega más estilos según tus necesidades
            }
            
            fill_elem = path_object.find("FillStyleId")
            if fill_elem is not None:
                fill_id = fill_elem.text.strip()
                if fill_id in fill_styles:
                    r, g, b = fill_styles[fill_id]
                    c.setFillColorRGB(r, g, b)
                    c.setStrokeColorRGB(r, g, b)
                else:
                    # Color por defecto (negro)
                    c.setFillColorRGB(0, 0, 0)
                    c.setStrokeColorRGB(0, 0, 0)
            else:
                c.setFillColorRGB(0, 0, 0)
                c.setStrokeColorRGB(0, 0, 0)
            
            
            self.draw_path(adjusted_points, c)

    def process_image_objects_Ant(self, element_object, c, parent_offset=(0,0)):
        """Procesa y dibuja objetos de imagen"""
        path = ""
        now = datetime.now()
        print(f"{now} Inicio creacion imagen")
        image_object_id = element_object.find('Id').text
        imageObject_objects = getattr(self,"ImageObject_config")
        image_objects = getattr(self,"Image_config")
        imageObject_object = imageObject_objects.get(image_object_id)
        
        pos = imageObject_object.find('Pos')
        size = imageObject_object.find('Size')
        
        #rotation = float(imageObject_object.find("Rotation").text or 0)
        #scale_x = float(imageObject_object.find("Scale").get("X", 1))
        #scale_y = float(imageObject_object.find("Scale").get("Y", 1))
        m0 = float(imageObject_object.find("Transformation_M0").text)
        m1 = float(imageObject_object.find("Transformation_M1").text)
        m2 = float(imageObject_object.find("Transformation_M2").text)
        m3 = float(imageObject_object.find("Transformation_M3").text)
        m4 = float(imageObject_object.find("Transformation_M4").text)
        m5 = float(imageObject_object.find("Transformation_M5").text)
        
        image_id = imageObject_object.find('ImageId').text
        image_object = image_objects.get(image_id)
        image_type = image_object.find('ImageType').text
        
        if image_type == "Variable":
            variable_id = image_object.find("VariableId").text
            path = self.get_variable_value(variable_id)
        if image_type == "Simple":
            image_location = image_object.find("ImageLocation").text
            _, path = image_location.split(',')
        print(path)
        if pos is not None and size is not None:
            x = self.convert_units(pos.get('X'))
            y = self.convert_units(pos.get('Y'))
            width = self.convert_units(size.get('X'))
            height = self.convert_units(size.get('Y'))
            
            
            if os.path.exists(path):
                c.saveState()
                c.translate(x, self.page_height - y)
                
                #Invertir la rotacion
                m1 = -m1
                m2 = -m2

                c.transform(m0, m1, m2, m3, m4, m5)
                
                if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    img = ImageReader(path)
                    c.drawImage(img, 0, -height, width, height)
                elif path.lower().endswith('.pdf'):
                    pdf_doc = fitz.open(path)
                    pdf_page = pdf_doc[0]  # Tomar la primera página

                    # Renderizar la página como una imagen
                    pix = pdf_page.get_pixmap(dpi=300)  # Controlar la calidad con DPI
                    img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)                

                    # Convertir PIL a formato compatible con ReportLab
                    img_reader = ImageReader(img_pil)

                    # Dibujar la imagen en el PDF
                    c.drawImage(img_reader, 0, -height, width, height)
                
                c.restoreState()
            else:
                print(f"Error: La imagen no existe en la ruta especificada: {path}")
                exit(1)
        now = datetime.now()
        print(f"{now} Fin creacion imagen")

    def process_image_objects(self, element_object, c, parent_offset=(0,0)):
        """Procesa y dibuja objetos de imagen"""
        now = datetime.now()
        print(f"{now}: Inicio carga de imagen")
        offset_x = parent_offset[0]
        offset_y = parent_offset[1]
        path = ""

        #print(f"{now} Inicio creacion imagen")
        image_object_id = element_object.find('Id').text
        imageObject_objects = getattr(self,"ImageObject_config")
        image_objects = getattr(self,"Image_config")
        imageObject_object = imageObject_objects.get(image_object_id)
        
        pos = imageObject_object.find('Pos')
        size = imageObject_object.find('Size')
        
        #rotation = float(imageObject_object.find("Rotation").text or 0)
        #scale_x = float(imageObject_object.find("Scale").get("X", 1))
        #scale_y = float(imageObject_object.find("Scale").get("Y", 1))
        m0 = float(imageObject_object.find("Transformation_M0").text)
        m1 = float(imageObject_object.find("Transformation_M1").text)
        m2 = float(imageObject_object.find("Transformation_M2").text)
        m3 = float(imageObject_object.find("Transformation_M3").text)
        m4 = float(imageObject_object.find("Transformation_M4").text)
        m5 = float(imageObject_object.find("Transformation_M5").text)
        
        image_id = imageObject_object.find('ImageId').text

        # ----> Revisa el cache antes de procesar
        if image_id in self.images_cache:            
            img_or_path = self.images_cache[image_id]
        else:
            image_object = image_objects.get(image_id)
            image_type = image_object.find('ImageType').text
            
            if image_type == "Variable":
                variable_id = image_object.find("VariableId").text
                path = self.get_variable_value(variable_id)
            elif image_type == "Simple":
                image_location = image_object.find("ImageLocation").text
                _, path = image_location.split(',')
            else:
                path = None

            img_or_path = None
            if isinstance(path, str):
                if path and os.path.exists(path):
                    if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                        img_or_path = ImageReader(path)
                    elif path.lower().endswith('.pdf'):
                        pdf_doc = fitz.open(path)
                        pdf_page = pdf_doc[0]  # Tomar la primera página
                        pix = pdf_page.get_pixmap(dpi=96)
                        img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        img_or_path = ImageReader(img_pil)
                    # Agrega más tipos según necesidad
                else:
                    print(f"Imagen no disponible: {path}")
                    sys.exit(1)
                # Guarda en el cache (sea imagen o None si no existe)
                self.images_cache[image_id] = img_or_path
            else:
                print(f"Error: El path de la imagen no es una cadena válida: {path}")
                sys.exit(1)
        
        if pos is not None and size is not None and img_or_path is not None:
            x = self.convert_units(pos.get('X')) + offset_x
            y = self.convert_units(pos.get('Y')) + offset_y
            width = self.convert_units(size.get('X'))
            height = self.convert_units(size.get('Y'))
            
            if img_or_path:
                c.saveState()
                c.translate(x, self.page_height - y)
                # Invertir la rotación si corresponde
                c.transform(m0, -m1, -m2, m3, m4, m5)
                c.drawImage(img_or_path, 0, -height, width, height)
                c.restoreState()
            else:
                print(f"Error: La imagen no existe en la ruta especificada: {path}")
                exit(1)
        now = datetime.now()
        print(f"{now} Fin creacion imagen")

    def generate_qr_Code(self, data, p_x, p_y, s_x, s_y, m_vals, module_width, error_level, c):
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
        c.translate(p_x, self.page_height - p_y)
        m0, m1, m2, m3, m4, m5 = m_vals
        m1 = -m1  # Igual que en process_image_objects
        m2 = -m2
        c.transform(m0, m1, m2, m3, m4, m5)
        c.drawImage(img, 0, -s_y, s_x, s_y, mask='auto')
        c.restoreState()        

    def generate_code128(self, data, p_x, p_y, s_x, s_y, m_vals, c, module_size=0.3, module_height=15):
        """
        Dibuja un Code128 en el PDF aplicando las transformaciones.
        """
       
        now = datetime.now()
        print(f"{now} Inicio creacion Code128")

        barcode = code128.Code128(data, barHeight=module_height, barWidth=module_size)

        c.saveState()
        c.translate(p_x, self.page_height - p_y)

        

        m0, m1, m2, m3, m4, m5 = m_vals
        m1 = -m1
        m2 = -m2
        c.transform(m0, m1, m2, m3, m4, m5)
        barcode.drawOn(c, 0, -module_height)
        c.restoreState()

        now = datetime.now()
        print(f"{now} Fin creacion Code128")

    def generate_ean128(self, data, p_x, p_y, s_x, s_y, m_vals, c, module_size=0.3, module_height=15):
        """
        Dibuja un EAN128 (usando Code128 como base) en el PDF aplicando las transformaciones.
        EAN128 se representa con Code128 usando el carácter FNC1, que en la mayoría de implementaciones
        se puede añadir como chr(202) delante del dato.
        """
        now = datetime.now()
        print(f"{now} Inicio creacion EAN128")

        # La mayoría de los sistemas representan EAN128 como FNC1 + datos.
        data_ean128 = chr(202) + data  # Puede variar según librería/barcode reader
        data_ean128 = data  # Puede variar según librería/barcode reader

        barcode = code128.Code128(data_ean128, barHeight=module_height, barWidth=module_size)
        c.saveState()
        c.translate(p_x, self.page_height - p_y)
        m0, m1, m2, m3, m4, m5 = m_vals
        m1 = -m1
        m2 = -m2
        c.transform(m0, m1, m2, m3, m4, m5)
        barcode.drawOn(c, 0, -module_height)
        c.restoreState()

        now = datetime.now()
        print(f"{now} Fin creacion EAN128")

    def generate_ean8(self, data, p_x, p_y, s_x, s_y, m_vals, c, module_size=0.3, module_height=15):
        """
        Dibuja un EAN8 en el PDF aplicando las transformaciones.
        """
        now = datetime.now()
        print(f"{now} Inicio creacion EAN8")

        barcode = eanbc.Ean8BarcodeWidget(data)
        bounds = barcode.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        scale_x = module_size / width if width else 1
        scale_y = module_height / height if height else 1

        c.saveState()
        c.translate(p_x, self.page_height - p_y)
        m0, m1, m2, m3, m4, m5 = m_vals
        m1 = -m1
        m2 = -m2
        c.transform(m0, m1, m2, m3, m4, m5)
        c.scale(scale_x, scale_y)
        barcode.drawOn(c, 0, -height)
        c.restoreState()

        now = datetime.now()
        print(f"{now} Fin creacion EAN8")

    def generate_ean13(self, data, p_x, p_y, s_x, s_y, m_vals, c, module_size=0.3, module_height=15):
        """
        Dibuja un EAN13 en el PDF aplicando las transformaciones.
        """
        now = datetime.now()
        print(f"{now} Inicio creacion EAN13")

        barcode = eanbc.Ean13BarcodeWidget(data)
        bounds = barcode.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        scale_x = module_size / width if width else 1
        scale_y = module_height / height if height else 1

        c.saveState()
        c.translate(p_x, self.page_height - p_y)
        m0, m1, m2, m3, m4, m5 = m_vals
        m1 = -m1
        m2 = -m2
        c.transform(m0, m1, m2, m3, m4, m5)
        c.scale(scale_x, scale_y)
        barcode.drawOn(c, 0, -height)
        c.restoreState()

        now = datetime.now()
        print(f"{now} Fin creacion EAN13")

    def generate_code39(self, data, p_x, p_y, s_x, s_y, m_vals, c, module_size=0.3, module_height=15):
        """
        Dibuja un Code39 en el PDF aplicando las transformaciones.
        """
        now = datetime.now()
        print(f"{now} Inicio creacion Code39")

        barcode = code39.Standard39(data, barHeight=module_height, barWidth=module_size, stop=1)
        c.saveState()
        c.translate(p_x, self.page_height - p_y)
        m0, m1, m2, m3, m4, m5 = m_vals
        m1 = -m1
        m2 = -m2
        c.transform(m0, m1, m2, m3, m4, m5)
        barcode.drawOn(c, 0, -module_height)
        c.restoreState()

        now = datetime.now()
        print(f"{now} Fin creacion Code39")

    def process_barcode_objects(self, barcode_element, c):
        # Tipos de codigos de barras
        # QRBarcodeGenerator
        # EAN8BarcodeGenerator
        # EAN13BarcodeGenerator
        # EAN128BarcodeGenerator
        # Code39BarcodeGenerator
        # Code128BarcodeGenerator        
        
        id_barcode = barcode_element.find("Id").text
        barcodes = getattr(self,"Barcode_config")
        barcode = barcodes.get(id_barcode)

        variable_id = barcode.find('VariableId').text
        fill_style_id = barcode.find('FillStyleId').text        
        code_text = self.get_variable_value(variable_id)
        
        pos = barcode.find('Pos')
        size = barcode.find('Size')

        p_x = self.convert_units(pos.get('X',0))
        p_y = self.convert_units(pos.get('Y',0))
        s_x = self.convert_units(size.get('X',0))
        s_y = self.convert_units(size.get('Y',0))
        
        #rotation = float(barcode.find("Rotation").text or 0)
        #scale_x = float(barcode.find("Scale").get("X", 1))
        #scale_y = float(barcode.find("Scale").get("Y", 1))
        m0 = float(barcode.find("Transformation_M0").text)
        m1 = float(barcode.find("Transformation_M1").text)
        m2 = float(barcode.find("Transformation_M2").text)
        m3 = float(barcode.find("Transformation_M3").text)
        m4 = float(barcode.find("Transformation_M4").text)
        m5 = float(barcode.find("Transformation_M5").text)
        m_vals = (m0, m1, m2, m3, m4, m5)

        barcode_generator_element = barcode.find('BarcodeGenerator')
        barcode_type = barcode_generator_element.find('Type').text
        
        # Codigo QR
        if barcode_type == "QRBarcodeGenerator":
            error_level = barcode_generator_element.find("ErrorLevel").text
            module_width = self.convert_units(barcode_generator_element.find('ModulWidth').text)    
            self.generate_qr_Code(code_text, p_x, p_y, s_x, s_y, m_vals, module_width, error_level, c)
        # Todos los codigos de barras
        else:
            module_size = self.convert_units(barcode_generator_element.find('ModulSize').text) if barcode_generator_element.find('ModulSize') is not None else 0.3
            module_height = self.convert_units(barcode_generator_element.find('Height').text) if barcode_generator_element.find('Height') is not None else 15

            if barcode_type == "EAN8BarcodeGenerator":
                self.generate_ean8(code_text, p_x, p_y, s_x, s_y, m_vals, c, module_size, module_height)
            elif barcode_type == "EAN13BarcodeGenerator":
                self.generate_ean13(code_text, p_x, p_y, s_x, s_y, m_vals, c, module_size, module_height)
            elif barcode_type == "EAN128BarcodeGenerator":
                self.generate_ean128(code_text, p_x, p_y, s_x, s_y, m_vals, c, module_size, module_height)
            elif barcode_type == "Code39BarcodeGenerator":
                self.generate_code39(code_text, p_x, p_y, s_x, s_y, m_vals, c, module_size, module_height)
            elif barcode_type == "Code128BarcodeGenerator":
                self.generate_code128(code_text, p_x, p_y, s_x, s_y, m_vals, c, module_size, module_height)
            else:
                print("Codigo no configurado")            

    def create_table_style(self, table_element):
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

    def parse_borderstyle_config(self,border_element):
        """
        Extrae configuraciones completas de un nodo BorderStyle incluyendo líneas, esquinas y corners.
        """
        border_config = {
            "sides": {},
            "corners": {},
            "corner_types": {},
            "fill_style_id": None
        }

        # Lados (Lineas)
        for tag, side in {
            "TopLine": "TOP",
            "BottomLine": "BOTTOM",
            "LeftLine": "LEFT",
            "RightLine": "RIGHT"
        }.items():
            elem = border_element.find(tag)
            if elem is not None:
                color = "#000000"  # predeterminado, ya que no se especifica en el FillStyle
                width = float(elem.findtext("LineWidth") or 0.25)
                border_config["sides"][side] = {
                    "color": color,
                    "width": width
                }

        # Esquinas (Corners visuales)
        for tag, corner in {
            "UpperLeftCorner": "TOPLEFT",
            "UpperRightCorner": "TOPRIGHT",
            "LowerRightCorner": "BOTTOMRIGHT",
            "LowerLeftCorner": "BOTTOMLEFT"
        }.items():
            elem = border_element.find(tag)
            if elem is not None:
                color = "#000000"  # por defecto
                width = float(elem.findtext("LineWidth") or 0.25)
                border_config["corners"][corner] = {
                    "color": color,
                    "width": width
                }

        # Tipo de esquina (rounded o no)
        for tag, corner in {
            "UpperLeftCornerType": "TOPLEFT",
            "UpperRightCornerType": "TOPRIGHT",
            "LowerRightCornerType": "BOTTOMRIGHT",
            "LowerLeftCornerType": "BOTTOMLEFT"
        }.items():
            elem = border_element.find(tag)
            if elem is not None:
                radius_elem = elem.find("CornerRadius")
                radius_x = float(radius_elem.get("X", 0)) if radius_elem is not None else 0
                radius_y = float(radius_elem.get("Y", 0)) if radius_elem is not None else 0
                border_config["corner_types"][corner] = {
                    "rounded": radius_x > 0 or radius_y > 0,
                    "radius_x": radius_x,
                    "radius_y": radius_y
                }

        # Relleno
        fill_elem = border_element.find("FillStyleId")
        if fill_elem is not None and fill_elem.text:
            border_config["fill_style_id"] = fill_elem.text

        return border_config

    def draw_border(self,c, x, y, width, height, border_conf):
        """
        Dibuja los bordes con lados, esquinas y redondeos si aplica.
        """
        sides = border_conf.get("sides", {})
        corners = border_conf.get("corners", {})
        corner_types = border_conf.get("corner_types", {})

        def draw_line(x1, y1, x2, y2, conf):
            c.setLineWidth(conf["width"])
            c.setStrokeColor(conf["color"])
            c.line(x1, y1, x2, y2)

        def draw_arc(cx, cy, rx, ry, start_ang, end_ang, conf):
            c.setLineWidth(conf["width"])
            c.setStrokeColor(conf["color"])
            c.arc(cx - rx, cy - ry, cx + rx, cy + ry, start_ang, end_ang)

        # Lados rectos
        if "TOP" in sides:
            draw_line(x, y + height, x + width, y + height, sides["TOP"])
        if "BOTTOM" in sides:
            draw_line(x, y, x + width, y, sides["BOTTOM"])
        if "LEFT" in sides:
            draw_line(x, y, x, y + height, sides["LEFT"])
        if "RIGHT" in sides:
            draw_line(x + width, y, x + width, y + height, sides["RIGHT"])

        # Esquinas redondeadas
        for key, angles in {
            "TOPLEFT": (90, 180, x, y + height),
            "TOPRIGHT": (0, 90, x + width, y + height),
            "BOTTOMLEFT": (180, 270, x, y),
            "BOTTOMRIGHT": (270, 360, x + width, y)
        }.items():
            if key in corners:
                conf = corners[key]
                rounded_conf = corner_types.get(key, {})
                if rounded_conf.get("rounded"):
                    rx = rounded_conf.get("radius_x", 4)
                    ry = rounded_conf.get("radius_y", 4)
                    draw_arc(angles[2], angles[3], rx, ry, angles[0], angles[1], conf)

    def draw_bordered_rect(self, c, x, y, width, height, border_conf):
        """
        Dibuja un rectángulo con bordes personalizados por lado (color y grosor)
        y opcionalmente esquinas redondeadas.

        Parámetros:
            c: canvas de ReportLab
            x, y: esquina inferior izquierda
            width, height: dimensiones del rectángulo
            border_conf: diccionario con configuración de bordes (incluye sides y corner_radius)
        """

        x0 = x
        y0 = y
        x1 = x + width
        y1 = y + height

        sides = border_conf.get("sides", {})
        corner_radius = float(border_conf.get("corner_radius", 0))

        # Si todos los lados son iguales y hay radio, usar roundRect
        if len(set((frozenset(props.items()) for props in sides.values()))) == 1 and corner_radius > 0:
            props = list(sides.values())[0]
            width_ = props.get("width", 0.5)
            color_ = props.get("color", "#000000")
            c.setStrokeColor(colors.HexColor(color_))
            c.setLineWidth(width_)
            c.roundRect(x0, y0, width, height, corner_radius, stroke=1, fill=0)
        else:
            # Dibujar cada lado individual
            for side, props in sides.items():
                line_width = props.get("width", 0.5)
                color = props.get("color", "#000000")
                color_obj = colors.HexColor(color)

                c.setStrokeColor(color_obj)
                c.setLineWidth(line_width)

                if side == "TOP":
                    c.line(x0 + corner_radius, y1, x1 - corner_radius, y1)
                elif side == "BOTTOM":
                    c.line(x0 + corner_radius, y0, x1 - corner_radius, y0)
                elif side == "LEFT":
                    c.line(x0, y0 + corner_radius, x0, y1 - corner_radius)
                elif side == "RIGHT":
                    c.line(x1, y0 + corner_radius, x1, y1 - corner_radius)

            # Dibujar esquinas redondeadas si corresponde
            if corner_radius > 0:
                c.setLineWidth(1)
                c.setStrokeColor(colors.black)

                # Esquinas con arcs
                c.arc(x0, y0, x0 + 2*corner_radius, y0 + 2*corner_radius, startAng=180, extent=90)  # Inferior izquierda
                c.arc(x1 - 2*corner_radius, y0, x1, y0 + 2*corner_radius, startAng=270, extent=90)  # Inferior derecha
                c.arc(x0, y1 - 2*corner_radius, x0 + 2*corner_radius, y1, startAng=90, extent=90)   # Superior izquierda
                c.arc(x1 - 2*corner_radius, y1 - 2*corner_radius, x1, y1, startAng=0, extent=90)    # Superior derecha

    def process_flows_areas(self, flow_area_element, c, parent_offset=(0,0),element=False):
        id_flow_area = flow_area_element.find("Id").text
        flow_areas = getattr(self,"FlowArea_config")
        if id_flow_area == "177": #Este es el element, se deben aplicar estos offset a todos sus hijos
            #Hijos:
            #    178,179,180 y 181 shape
            print(f"offset flowarea: {id_flow_area}")
            print(f"x:{parent_offset[0]}")
            print(f"y:{parent_offset[1]}")
        #x:37.12502004750002
        #y:548.1499023000003

        #ids_flow_areas = ids_flow_areas_by_pages.get(page_id)

        
        flow_area = flow_areas.get(id_flow_area)
        flow_area_id = flow_area.find('Id').text
        flow_id = flow_area.find('FlowId').text
        flow_border_id = flow_area.find("BorderStyleId").text        

        pos = flow_area.find('Pos')
        size = flow_area.find('Size')

        p_x = self.convert_units(pos.get('X',0)) + parent_offset[0]
        p_y = self.convert_units(pos.get('Y',0)) + parent_offset[1]
        s_x = self.convert_units(size.get('X',0))
        s_y = self.convert_units(size.get('Y',0))
        
        #border_conf = self.BorderStyle_config[flow_border_id]
        #self.draw_bordered_rect(c, p_x, (self.page_height - p_y - s_y), s_x, s_y, border_conf)

        if flow_border_id is not None:
            border_conf = self.BorderStyle_config[flow_border_id]
            sides = border_conf.get("sides", {})
            for side, props in sides.items():
                width = props.get("width", 0.5)
                color = props.get("color", "#000000")
                color_obj = colors.HexColor(color)
                c.setStrokeColor(color_obj)
                c.setLineWidth(width)
            c.rect(p_x, (self.page_height - p_y - s_y), s_x, s_y, fill=0)


        if element:
            offset_x = parent_offset[0]
            offset_y = parent_offset[1]
        else:
            offset_x = p_x
            offset_y = p_y
        
        
        frame = Frame(
            x1=p_x,
            y1=self.page_height - p_y - s_y,
            width=s_x,
            height=s_y,
            id=f"frame_{flow_area_id}",
            showBoundary=0,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0
        )

        
        ids_flow = getattr(self,"Flow_data")
        flows = getattr(self,"Flow_config")
        flow = flows.get(flow_id) 
        if flow_id == "180":
            print("Pausa")
            pass           
        

        #print(f"Procesando Flow con Id: {flow_id}")

        if flow is not None:
            para, min_height_default = self.process_flow(flow,c=c, parent_offset=(offset_x,offset_y),max_width=s_x)

        
            
        try:    
            frame.addFromList(para,c)
        except Exception as e:
            print(f"Error al agregar el frame: {e}")
            print(f"FlowArea Id: {flow_area_id}, Pos: ({p_x}, {p_y}), Size: ({s_x}, {s_y})")
            sys.exit(1)
     
    def process_elements_by_object(self, object_id, c, parent_offset=(0,0), element=False):
        #Proceso anterior
        '''
        frames_list = []
        ids_flow_areas_by_pages = getattr(self,"FlowArea_data")
        para_style_dict = getattr(self,"ParaStyle_reportlab")
        flow_areas = getattr(self,"FlowArea_config")
        fill_styles = getattr(self,"FillStyle_config")
        colors = getattr(self,"Color_reportlab")
        text_styles = self.TextStyle_config
        fonts_config_dict = self.Font_config
        
        ids_flow_areas = ids_flow_areas_by_pages.get(page_id)
        for id_flow_area in ids_flow_areas:            
            self.process_flows_areas()    
        '''
        offset_x = parent_offset[0]
        offset_y = parent_offset[1]
        elements_to_process = self.grouped_nodes.get(object_id) 
        for element_to_process in elements_to_process:
            #Obtener el nombre del nodo raiz
            node_name = element_to_process.tag
            element_name = element_to_process.find("Name")
            if element_name is not None:
                name = element_name.text
                print(f"Procesando elemento: {name}")
            
            if (name == "FlowArea 2"):
                print("Pausa")

            if (node_name == "FlowArea"):
                self.process_flows_areas(element_to_process, c, parent_offset=(offset_x,offset_y), element=element)
            elif (node_name == "PathObject"):
                self.process_path_object(element_to_process, c, parent_offset=(offset_x,offset_y))
            elif (node_name == "ImageObject"):                
                self.process_image_objects(element_to_process, c, parent_offset=(offset_x,offset_y))
                #pass
            #Creo que una hoja no puede tener una tabla como elemento raiz
            elif (node_name == "Chart"):
                self.process_chart(element_to_process, c, parent_offset=(offset_x,offset_y))
                
            elif (node_name == "Barcode"):
                self.process_barcode_objects(element_to_process, c)
            else:
                print(f"Elemento no configurado: {node_name}")                    

    #Los colores los usan los fillstyle
    #los fillstyle los usan los textStyle, formas, codigos barras
    #los textStyle los usan los parraghrapstyle y los flow
    #los parraghrapstyle los usan los flow
    
    def register_colors(self):
        now = datetime.now()
        print(f"{now} Inicio registro colores")
        colors = self.Color_config
        color_dict = getattr(self,"Color_reportlab")
        for id, color in colors.items():
            color_string = color.find("RGB").text
            color_name = color.find("RGB").text
            r, g, b = map(float, color_string.split(","))                                                           
            
            #Agregar color en hex
            r_hex, g_hex, b_hex = int(r * 255), int(g * 255), int(b * 255)
            hex_color = "#{:02x}{:02x}{:02x}".format(r_hex, g_hex, b_hex)
            color_dict[id] = hex_color
        now = datetime.now()
        print(f"{now} Fin registro colores")

    #TODO
    ###REVISAR SI SE VA A USAR
    def register_images(self):
        images = self.ImageObjects_config
        image_dict = getattr(self,"Images_reportlab")
        for id, image in images.items():
            pass
            #color_string = color.find("RGB").text
            #color_name = color.find("RGB").text
            
            #image_dict[id] = hex_color
    
    #TODO
    ###REVISAR SI SE VA A USAR
    def register_fillstyles(self):
        now = datetime.now()
        print(f"{now} Inicio registro filstyle")
        fills = self.FillStyle_config
        for id, fill in fills.items():
            color_string = fill.find("RGB").text
            color_name = fill.find("RGB").text
            r, g, b = map(float, color_string.split(","))

            color_dict = getattr(self,"Color_reportlab")
            color_dict[id] = Color(r, g, b)
            
            #color_name = color.find('')
        now = datetime.now()
        print(f"{now} Fin registro filstyle")

    #TODO
    ###REVISAR
    def register_borderstyles(self):
        """Registra todos los BorderStyle del XML con sus lados y colores"""
        now = datetime.now()
        print(f"{now} Inicio registro borderstyle")
        self.BorderStyle_config = {}

        border_elements = self.workflow.findall(".//BorderStyle")
        for bs in border_elements:
            border_id = bs.findtext("Id")
            fill_style_id_Element = bs.find("FillStyleId")
            if fill_style_id_Element is not None:
                fill_style_id = fill_style_id_Element.text
            else:
                continue
                fill_style_id = ""
            #borderId 350
            border_conf = {
                "fill_style_id": fill_style_id,
                "sides": {}  # Ej: 'LEFT': {'width': 0.5, 'color': '#000000'}
            }

            # Lados de la tabla que ReportLab entiende
            sides_map = {
                "LeftLine": "LEFT",
                "RightLine": "RIGHT",
                "TopLine": "TOP",
                "BottomLine": "BOTTOM"
            }

            for xml_tag, side in sides_map.items():
                line_elem = bs.find(xml_tag)
                if line_elem is not None:
                    fill_id = line_elem.findtext("FillStyle")
                    width = line_elem.findtext("LineWidth")

                    if fill_id and fill_id in self.FillStyle_config:
                        colors = getattr(self,"Color_reportlab")
                        color_id = self.FillStyle_config[fill_id].find("ColorId").text
                        color = colors.get(color_id, "#000000")  # Default to black if not found

                    else:
                        color = "#000000"  # Default

                    border_conf["sides"][side] = {
                        "width": float(width) if width else 0.25,
                        "color": color
                    }

            self.BorderStyle_config[border_id] = border_conf
        now = datetime.now()
        print(f"{now} Fin registro borderstyle")

    def get_node_text(self, xml, node_name, default=None):
        node = xml.find(node_name)
        return node.text if node is not None else default

    def register_parastyles(self):
        now = datetime.now()
        print(f"{now} Inicio registro parastyle")
        paras = self.ParaStyle_config
        for id, para in paras.items():
            if id == '63':
                print("Pausar")
            left_indent = self.get_node_text(para,"LeftIndent",0)
            right_indent = self.get_node_text(para,"RightIndent")
            first_line_left_indent = self.get_node_text(para,"FirstLineLeftIndent")
            space_before = self.get_node_text(para,"SpaceBefore",0)
            space_after = self.get_node_text(para,"SpaceAfter",0)
            line_spacing = self.get_node_text(para,"LineSpacing")
            widow = self.get_node_text(para,"Widow")
            orphan = self.get_node_text(para,"Orphan")
            keep_with_next = self.get_node_text(para,"KeepWithNext")
            keep_lines_together = self.get_node_text(para,"KeepLinesTogether")
            dont_wrap = self.get_node_text(para,"DontWrap")

            h_align = self.get_node_text(para,"HAlign","Left")  # Valor por defecto "Left" si no existe el nodo
            align = 0  # TA_LEFT por defecto
            if h_align == "Center":
                align = 1  # TA_CENTER
            elif h_align == "Right":
                align = 2  # TA_RIGHT
            elif "Justify" in h_align:
                align = 4  # TA_JUSTIFY

            style_args = {"alignment": align}

            if left_indent is not None:
                style_args["leftIndent"] = self.convert_units(left_indent)
            if right_indent is not None:
                style_args["rightIndent"] = self.convert_units(right_indent)
            if first_line_left_indent is not None:
                style_args["firstLineIndent"] = self.convert_units(first_line_left_indent)
            if space_before is not None:
                style_args["spaceBefore"] = self.convert_units(space_before)
            if space_after is not None:
                style_args["spaceAfter"] = self.convert_units(space_after)
            if line_spacing is not None:
                style_args["leading"] = self.convert_units(line_spacing)                
            if widow is not None:
                style_args["allowWidows"] = widow
            if orphan is not None:
                style_args["allowOrphans"] = orphan
            if keep_with_next is not None:
                style_args["keepWithNext"] = keep_with_next
            if keep_lines_together is not None:
                style_args["keepTogether"] = keep_lines_together

            style = ParagraphStyle(id, **style_args)
            para_dict = getattr(self,"ParaStyle_reportlab")
            para_dict[id] = style
            
            '''
            is_visible = para.find("IsVisible").text == "True"
            if not is_visible: continue
            left_indent = para.find("LeftIndent").text
            right_indent = para.find("RightIndent").text            
            first_line_left_indent = para.find("FirstLineLeftIndent").text
            space_before = para.find("SpaceBefore").text
            space_after = para.find("SpaceAfter").text
            line_spacing = para.find("LineSpacing").text
            
            widow = para.find("Widow").text
            orphan = para.find("Orphan").text
            keep_with_next = para.find("KeepWithNext").text
            keep_lines_together = para.find("KeepLinesTogether").text
            dont_wrap = para.find("DontWrap").text
            
            h_align = para.find("HAlign").text
            align = 0 #TA_LEFT #Por defecto            
            if h_align == "Center": align = 1 #TA_CENTER
            if h_align == "Right": align = 2 #TA_RIGHT
            if "Justify" in h_align: align = 4 #TA_JUSTIFY
            style = ParagraphStyle(
                id,
                leftIndent=self.convert_units(left_indent),
                rightIndent=self.convert_units(right_indent),
                firstLineIndent=self.convert_units(first_line_left_indent),
                spaceBefore=self.convert_units(space_before),
                spaceAfter=self.convert_units(space_after),
                leading=self.convert_units(line_spacing),  # "LineSpacing" es el interlineado
                alignment=align,  # "HAlign" -> Alineación a la izquierda
                allowWidows=widow,  # "Widow" -> Mínimo de líneas en la siguiente página
                allowOrphans=orphan,  # "Orphan" -> Mínimo de líneas en la página actual
                keepWithNext=keep_with_next,  # "KeepWithNext"
                keepTogether=keep_lines_together  # "KeepLinesTogether"                
            )
            #No usar de momento
            #wordWrap=None if dont_wrap else 'CJK'  # "DontWrap" -> No cortar palabras

            para_dict = getattr(self,"ParaStyle_reportlab")
            para_dict[id] = style
            '''
        now = datetime.now()
        print(f"{now} Fin registro parastyle")
                
    def register_fonts(self):
        """Registra las fuentes definidas en el XML"""
        now = datetime.now()
        print(f"{now} Inicio registro fuentes")
        fonts = self.Font_config
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
                            pdfmetrics.registerFont(TTFont(complete_name, f'{font_path}{font_file}'))
                    except:
                        print(f"No se pudo cargar la fuente: {complete_name}")
        print(pdfmetrics.getRegisteredFontNames())
        now = datetime.now()
        print(f"{now} Fin registro fuentes")

    def grouping_elements(self):
        now = datetime.now()
        print(f"{now} Inicio agrupacion elementos")
        #Se agrupan los elementos por el id del parent
        all_elements = self.workflow.findall(layout_container)
        #all_elements = self.workflow.find('Layout')        
        for element in all_elements:
            parent_element = element.find('ParentId')  # Obtener el valor de 'parent'
            if parent_element is not None:  # Verificar que tenga el atributo 'parent'
                parent = parent_element.text
                if parent not in self.grouped_nodes:
                    self.grouped_nodes[parent] = []
                self.grouped_nodes[parent].append(element)
            else:
                id_element = element.find('Id')
                if id_element is not None:
                    id = id_element.text
                    self.all_elements[id] = element
        now = datetime.now()
        print(f"{now} Fin agrupacion elementos")
                
    def process_page(self, page, c):
        """Procesa una página del XML y dibuja sus elementos"""
        # Configurar tamaño de página
        width = page.find('Width').text
        height = page.find('Height').text
        self.page_width = self.convert_units(width)
        self.page_height = self.convert_units(height)
        page_id = page.find('Id').text
        condition_type_page = page.find("ConditionType").text
        c.setPageSize((self.page_width,self.page_height))
  
        # Procesar elementos de la página
        # FlowArea
        
        #self.process_image_objects(page_id, pdf_canvas)
        self.process_elements_by_object(page_id, c)
        
        
        if (condition_type_page == "Simple"):
            next_page_id = page.find("NextPageId")
            if next_page_id is not None:
                #procesar pagina con id siguiente
                #volver a llamar "process_page"
                pass                                

    def map_elements(self,element_String):        
        path_to_find = f'{layout_container}{element_String}'
        elements = self.workflow.findall(path_to_find)
        parent_dict_data = getattr(self, f"{element_String}_data")
        parent_dict_config = getattr(self, f"{element_String}_config")
        for element in elements:
            #print(ET.fromstring(element))
            id = element.find("Id").text.strip()
 
            #id = element.get("Id")
            # Si existe el objeto "ParentId" quiere decir que el nodo corresponde al arbol de objetos
            if element.find('ParentId') is not None:
                '''
                Version anterior, no la estoy usando
                parent_id = element.find("ParentId").text.strip()
                if parent_id not in parent_dict_data:
                    parent_dict_data[parent_id] = []  # Inicializar lista si no existe
                parent_dict_data[parent_id].append(id)  # Agregar el Id a la lista
                '''
                parent_dict_data[id] = element
            else:                

                parent_dict_config[id] = element 
            
        #prueba = getattr(self, "Variable_config")
        #print(prueba.get('1')) 
                
    def create_pdf(self, output_filename, register):
        """Crea el archivo PDF"""
        self.register = register
        c = canvas.Canvas(output_filename)
                                
        # Procesar páginas

        pages = self.workflow.find(f'{layout_container}Pages')                
        selection_type = pages.find("SelectionType").text         
        page_dict = getattr(self,"Page_config")
        page_id = None
        # - Variable
        # - Simple
        if (selection_type == "Variable"):
            print("Inicio de proceso de paginas variables")
            condition_type_pages = pages.find("ConditionType").text
            # - Simple
            # - Condition
            # - InlCond
            
            if (condition_type_pages == "Simple"):
                page_id = pages.find("FirstPageId").text

            elif (condition_type_pages == "Condition"):
                page_condition_elements = pages.findall("PageCondition")
                for page_condition_element in page_condition_elements:
                    variable_condition_id = page_condition_element.find("ConditionId").text
                    condition_to_evaluate = self.get_variable_value(variable_condition_id)
                    if condition_to_evaluate:
                        page_id = page_condition_element.find("PageId").text
                        break
                
                if page_id is None:
                    page_id = pages.find("DefaultPageId").text                
                
            elif (condition_type_pages == "InlCond"):
                print("Inicio de proceso de paginas con InlCond")
            else:
                # - Integer
                # - Interval
                print(f'Condicion de tipo "{condition_type_pages}" no implementada')
            
            page_element = page_dict.get(page_id)
            self.process_page(page_element, c)
            c.showPage()

            #Probar la captura de la siguiente pagina
            next_page_id_element = page_element.find("NextPageId")
            if next_page_id_element is not None:                
                page_element = page_dict.get(next_page_id_element.text)
                self.process_page(page_element, c)
                c.showPage()
            
        elif (selection_type == "Simple"):
            #print("Inicio de proceso de paginas simples")
            for page_element in page_dict.values():                
                self.process_page(page_element, c)
                c.showPage()
            
        else:
            print(f'Metodo de Page order "{selection_type}" no disponible')
        try:                   
            c.save()
        except Exception as e:
            print(f"Error al guardar el PDF: {e}")
            sys.exit(1)
        #Esta optimizacion no funciono
        #doc = fitz.open(output_filename)
        #doc.save("D:\ProyectoComunicaciones\ProyectoPDF\salida_optimizada.pdf", deflate=True)

def configurar_logger_por_hilo():
    thread_id = threading.get_ident()
    logger = logging.getLogger(f"thread_{thread_id}")
    logger.setLevel(logging.DEBUG)

    # Evita agregar múltiples handlers si ya fue creado
    
    handler = logging.FileHandler(f"D:/ProyectoComunicaciones/ProyectoPDF/logs/pdf_{thread_id}.log", mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# 1- Realizo la lectura de la plantilla (Configuracion de diseño) desde el XML
# 2- Realizo la lectura del JSON con los datos a procesar (Procesar cada uno de los registros)
# 3- Realizo la conversion de cada registro a PDF
# 4- Recorro cada uno de los tipos de objetos que tengo en el XML y los mapeo a listas
# 4.1- Divido los elementos en dos tipos (configuracion y datos)
# 4.1.1- Configuracion (parent_dict_config): Objetos sin parentId (Pertenecen al diseño de las hojas)
# 4.1.2- Datos (parent_dict_data): Objetos con parentId (Pertenecen al arbol de objetos)
# 5- Registro los objetos de estilo para reutilizarlos (colores, fuentes, estilos de parrafos, estilos de texto, estilos de relleno)
# 6- Agrupo cada uno de los elementos por el id del parent (grouped_nodes) Para saber a que elemento pertenece cada objeto
# 7- Realizo el procesamiento de las paginas y los elementos que tengo en el XML
# 8- Reviso cada condicion de cada pagina para evaluar que tipo de pagina es (variable o fija)
# 8.1- Para cada pagina se deben procesar los diferentes elementos fijos de la tabla (FlowArea, PathObject, ImageObject, Table)
# 8.1.1 FlowArea: Cada flowArea tiene un flowId, con el cual se puede identificar el flujo de datos que se debe procesar
# 8.1.2 PathObject: Procesar los objetos de tipo Path
# 8.1.3 ImageObject: Procesar los objetos de tipo Imagen
# 8.1.4 Table: Procesar los objetos de tipo Tabla
# 9- Para cada flowId se debe procesar el contenido del flujo, que puede ser un texto o una variable
# 10- 

def main():
    path_json = "D:/ProyectoComunicaciones/ProyectoPDFGit/Datos/1_PE_860007336_FacturasWS_20250620_37F7155071DA4B57E0632A64A8C03854_Transform.json"
    path_xml = "D:\\ProyectoComunicaciones\\ProyectoPDFGit\\Colsubsidio_Compose_FacturasWS.xml"

    json_string = ""
    with open(path_json, 'r', encoding="UTF-8") as f_j:
        json_string = f_j.read()
    json_data = json.loads(json_string)

    with open(path_xml, 'r', encoding="UTF-8") as f_x:
        xml_string = f_x.read()
        
    principal_array = "Documents"  # Nombre del array principal en el JSON

    docs = json_data.get(principal_array)


    #########PRUEBAS###########
    ###########################
    converter = XMLToPDFConverter(xml_string)
    #Realizar el mapeo de todos los elementos en el XML para pasarlos a listas
    now = datetime.now()
    print(f"{now} Inicio mapeo elementos")
    for object_type in object_types:
        converter.map_elements(object_type)
    now = datetime.now()
    print(f"{now} Fin mapeo elementos") 
    converter.register_colors()       

    # Registrar fuentes
    converter.register_fonts()
    # Realizar el agrupamiento de los elementos para poder tenerlos a disposicion cuando se procesen las hojas
    converter.grouping_elements()
    converter.register_parastyles()
    converter.register_borderstyles()
    #converter.parse_borderstyle_config()

    #Poner proteccion
    #if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=5) as executor:
        if isinstance(docs, dict):
            documents = [docs]  # Lo convertimos a lista
        elif isinstance(docs, list):
            documents = docs
        else:
            raise ValueError("Formato de 'Documents' no reconocido")

        for document in documents:
            # Copiamos todos los datos del nivel raíz
            full_context = json_data.copy()
            # Sobrescribimos "Documents" con el documento individual actual
            full_context["Documents"] = document

            pdf_name = document.get("NombrePDF",None)
            print(pdf_name)
            if pdf_name is None:
                print("No se encontro la variable para el nombre del PDF")
                sys.exit()
            pdf_path = f"D:\\ProyectoComunicaciones\\ProyectoPDF\\{pdf_name}"
            executor.submit(converter.create_pdf,pdf_path,full_context)

    ###########################
    ###########################


    # Guarda el tiempo de finalización
    fin = time.time()
    # Calcula la diferencia de tiempo
    tiempo_transcurrido = (fin - inicio) * 1000
    # Imprime el tiempo transcurrido en segundos
    print("Tiempo transcurrido:", round(tiempo_transcurrido, 2), "milisegundos")

if __name__ == "__main__":
    # Configurar el logger para el hilo principal
    logger = configurar_logger_por_hilo()
    main()