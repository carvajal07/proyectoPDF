

def draw_border_fill_path(c, x, y, width, height, rx_tl, ry_tl, rx_tr, ry_tr, rx_br, ry_br, rx_bl, ry_bl, fill_color):
    p = c.beginPath()

    # Punto inicial: esquina inferior izquierda (después del arco)
    p.moveTo(x + rx_bl, y)

    # Lado inferior
    p.lineTo(x + width - rx_br, y)
    # Arco inferior derecho
    p.arcTo(x + width - 2*rx_br, y, x + width, y + 2*ry_br, startAng=270, extent=90)

    # Lado derecho
    p.lineTo(x + width, y + height - ry_tr)
    # Arco superior derecho
    p.arcTo(x + width - 2*rx_tr, y + height - 2*ry_tr, x + width, y + height, startAng=0, extent=90)

    # Lado superior
    p.lineTo(x + rx_tl, y + height)
    # Arco superior izquierdo
    p.arcTo(x, y + height - 2*ry_tl, x + 2*rx_tl, y + height, startAng=90, extent=90)

    # Lado izquierdo
    p.lineTo(x, y + ry_bl)
    # Arco inferior izquierdo
    p.arcTo(x, y, x + 2*rx_bl, y + 2*ry_bl, startAng=180, extent=90)

    # Cierra el path
    p.close()

    c.setFillColor(fill_color)
    c.drawPath(p, fill=1, stroke=0)

def draw_border(c, fillstyle_config, colors_reportlab, x, y, width, height, border_conf):
    """
    Dibuja bordes redondeados completos con líneas y arcos adaptados a los radios.
    """

    sides = border_conf.get("sides", {})
    corners = border_conf.get("corners", {})
    corner_types = border_conf.get("corner_types", {})
    fill_style_id = border_conf.get("fill_style_id")

    def draw_line(x1, y1, x2, y2, conf):
        c.setLineWidth(conf["width"])
        c.setStrokeColor(conf["color"])
        c.line(x1, y1, x2, y2)

    def draw_arc(cx, cy, rx, ry, start_ang, conf):
        c.setLineWidth(conf["width"])
        c.setStrokeColor(conf["color"])
        c.arc(cx - rx, cy - ry, cx + rx, cy + ry, start_ang, 90)

    # === Radios por esquina con valores mínimos por defecto
    #rx_tl, ry_tl = 20, 40  # Top-Left
    #rx_tr, ry_tr = 40, 40  # Top-Right
    #rx_br, ry_br = 20, 40  # Bottom-Right
    #rx_bl, ry_bl = 40, 40  # Bottom-Left

    min_rx = width / 2
    min_ry = height / 2
    # Aplicar radios reales si están definidos
    def safe_radius(corner):
        ct = corner_types.get(corner, {})
        if ct.get("rounded"):
            rx = ct.get("radius_x", 0)
            ry = ct.get("radius_y", 0)
            equal_corners = ry == rx
            min_rx_aux = min(rx, min_rx)
            min_ry_aux = min(ry, min_ry)
            if equal_corners:
                rx = ry = min(min_rx_aux, min_ry_aux)
            else:
                rx,ry = min_rx_aux, min_ry_aux
            return rx, ry
        return 0, 0

    rx_tl, ry_tl = safe_radius("TOPLEFT")
    rx_tr, ry_tr = safe_radius("TOPRIGHT")
    rx_br, ry_br = safe_radius("BOTTOMRIGHT")
    rx_bl, ry_bl = safe_radius("BOTTOMLEFT")

    x0, y0 = x, y
    x1, y1 = (x + width), (y + height)

    # === FONDO (si lo deseas, aquí podrías usar roundRect con el mayor radio)
    if fill_style_id and fill_style_id in fillstyle_config:
        fill_elem = fillstyle_config[fill_style_id]
        color_id = fill_elem.findtext("ColorId")
        if color_id and color_id in colors_reportlab:
            fill_color = colors_reportlab[color_id]
            c.setFillColor(fill_color)
            c.setStrokeColor(fill_color)
            c.setLineWidth(0)
            draw_border_fill_path(
                c, x0, y0, width, height,
                rx_tl, ry_tl, rx_tr, ry_tr, rx_br, ry_br, rx_bl, ry_bl,
                fill_color
            )
            #c.rect(x0, y0, width, height, fill=1, stroke=0)

    # === ESQUINAS (arcos)
    if "TOPLEFT" in corners:
        draw_arc(x0 + rx_tl, y1 - ry_tl, rx_tl, ry_tl, 90, corners["TOPLEFT"])
    if "TOPRIGHT" in corners:           
        draw_arc(x1 - rx_tr, y1 - ry_tr, rx_tr, ry_tr, 0, corners["TOPRIGHT"])
    if "BOTTOMRIGHT" in corners:
        draw_arc(x1 - rx_br, y0 + ry_br, rx_br, ry_br, 270, corners["BOTTOMRIGHT"])
    if "BOTTOMLEFT" in corners:
        draw_arc(x0 + rx_bl, y0 + ry_bl, rx_bl, ry_bl, 180, corners["BOTTOMLEFT"])
    

    # === LADOS rectos (ajustados a los radios)
    if "TOP" in sides:
        draw_line(x0 + rx_tl, y1, x1 - rx_tr, y1, sides["TOP"])
    if "BOTTOM" in sides:
        draw_line(x1 - rx_br, y0, x0 + rx_bl, y0, sides["BOTTOM"])
    if "LEFT" in sides:
        draw_line(x0, y0 + ry_bl, x0, y1 - ry_tl, sides["LEFT"])
    if "RIGHT" in sides:
        draw_line(x1, y1 - ry_tr, x1, y0 + ry_br, sides["RIGHT"])

    # LEFTRIGHT: de esquina inferior izquierda a esquina superior derecha
    if "LEFTRIGHT" in sides:
        #draw_line(x0, y0, x1, y1, sides["LEFTRIGHT"])
        start_x = x0 + (rx_bl/2)
        start_y = y0 + (ry_bl/2)
        end_x   = x1 - (rx_tr/2)
        end_y   = y1 - (ry_tr/2)
        draw_line(start_x, start_y, end_x, end_y, sides["LEFTRIGHT"])

    # RIGHTLEFT: de esquina inferior derecha a esquina superior izquierda
    if "RIGHTLEFT" in sides:
        #draw_line(x1, y0, x0, y1, sides["RIGHTLEFT"])
        start_x = x1 - (rx_br/2)
        start_y = y0 + (ry_br/2)
        end_x   = x0 + (rx_tl/2)
        end_y   = y1 - (ry_tl/2)
        draw_line(start_x, start_y, end_x, end_y, sides["RIGHTLEFT"])