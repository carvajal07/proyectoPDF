def bezier_curve(p0, p1, p2, p3, points, steps=20):
    t_values = [i / steps for i in range(steps + 1)]
    for t in t_values:
        x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
        y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
        points.append((x, y))

def draw_path(points, c):
    if not points:
        return

    p = c.beginPath()
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    # Se dibuja el path en el canvas, con trazo (stroke) activado y sin relleno (fill)
    c.drawPath(p, stroke=1, fill=1)

def transform_point(x, y, m0, m1, m2, m3, m4, m5, scale_x, scale_y, page_height, CONVERSION=2834.65):
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
    y_new = (m1 * x + m3 * y + m5) * -1 + page_height  # INVERTIR Y
    return x_new, y_new

def process_path_object(path_element, page_height, c, parent_offset=(0,0)):
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

    scale_x = float(path_element.find("Scale").get("X", 1))
    scale_y = float(path_element.find("Scale").get("Y", 1))
    
    CONVERSION = 2834.65 #Valor en puntos
    m0 = float(path_element.find("Transformation_M0").text)
    m1 = float(path_element.find("Transformation_M1").text)
    m2 = float(path_element.find("Transformation_M2").text)
    m3 = float(path_element.find("Transformation_M3").text)
    m4 = float(path_element.find("Transformation_M4").text)
    m5 = float(path_element.find("Transformation_M5").text)
    path = path_element.find("Path")
    if path is not None:
        points = []
        for move in path.findall("MoveTo"):
            x, y = transform_point(float(move.get("X")), float(move.get("Y")), m0, m1, m2, m3, m4, m5, scale_x, scale_y, page_height)
            points.append((x, y))
        for line in path.findall("LineTo"):
            x, y = transform_point(float(line.get("X")), float(line.get("Y")), m0, m1, m2, m3, m4, m5, scale_x, scale_y, page_height)
            points.append((x, y))
        for curve in path.findall("BezierTo"):
            x1, y1 = transform_point(float(curve.get("X1")), float(curve.get("Y1")), m0, m1, m2, m3, m4, m5, scale_x, scale_y, page_height)
            x2, y2 = transform_point(float(curve.get("X2")), float(curve.get("Y2")), m0, m1, m2, m3, m4, m5, scale_x, scale_y, page_height)
            x, y = transform_point(float(curve.get("X")), float(curve.get("Y")), m0, m1, m2, m3, m4, m5, scale_x, scale_y, page_height)
            bezier_curve(points[-1], (x1, y1), (x2, y2), (x, y), points)
        for arc in path.findall("ArcTo"):
            x, y = transform_point(float(arc.get("X")), float(arc.get("Y")), m0, m1, m2, m3, m4, m5, scale_x, scale_y, page_height)
            points.append((x, y))
        if path.find("ClosePath") is not None:
            points.append(points[0])                                    
        
        
        
        # Se ajusta el path según el tamaño y la posición definidos en el XML:
        # 1. Se lee el tamaño deseado (en metros) y se convierte a puntos.
        size_elem = path_element.find("Size")
        if size_elem is not None:
            desired_width = float(size_elem.get("X", 1)) * CONVERSION
            desired_height = float(size_elem.get("Y", 1)) * CONVERSION
        else:
            desired_width = desired_height = 1  # Valores por defecto
        
        # 2. Se lee la posición deseada (en metros) y se convierte a puntos.
        pos_elem = path_element.find("Pos")
        if pos_elem is not None:
            pos_x = float(pos_elem.get("X", 0)) * CONVERSION + offset_x 
            pos_y = (page_height - float(pos_elem.get("Y", 0)) * CONVERSION) - offset_y
            

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
            #pos_y = page_height - offset_y
            
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
            pos_y = page_height
        
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
        
        fill_elem = path_element.find("FillStyleId")
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
        
        
        draw_path(adjusted_points, c)