from core.utils import convert_units
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

def process_chart(chart_element, c, parent_offset=(0,0)):
    offset_x = parent_offset[0]
    offset_y = parent_offset[1]      
    
    # 1. Extraer posición y tamaño (en metros) y convertir a puntos
    pos = chart_element.find("Pos")
    size = chart_element.find("Size")
    x = convert_units(pos.get("X", 0))
    y = convert_units(pos.get("Y", 0))
    w = convert_units(size.get("X", 1))
    h = convert_units(size.get("Y", 1))

    # 2. Obtener el tipo de gráfico
    chart_type_elem = chart_element.find("Chart_Type")
    chart_type = chart_type_elem.text if chart_type_elem is not None else "Bar"
    
    # 3. Obtener el título del gráfico (opcional)
    title_elem = chart_element.find("Chart_Title")
    chart_title = title_elem.text if title_elem is not None else ""

    # 4. Obtener los datos de la(s) Serie(s)
    serie = chart_element.find("Serie")
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
        raise NotImplementedError(f"Tipo de gráfico no soportado: {chart_type}")

    # 7. Dibujar el chart en el PDF en la posición adecuada
    renderPDF.draw(drawing, c, x, y)

    # 8. Opcional: agregar el título si existe
    if chart_title:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y + h + 10, chart_title)