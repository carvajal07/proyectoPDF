from core.utils import convert_units

def register_borderstyles(borderstyle_elements, fillstyle_config, color_reportlab):
    """
    Convierte todos los BorderStyle XML en un diccionario usable en ReportLab.
    """
    from datetime import datetime
    print(f"{datetime.now()} Inicio registro borderstyle")

    borderstyle_reportlab = {}

    for border_id, border_elem in borderstyle_elements.items():
        border_config = {
            "sides": {},           # LEFT, RIGHT, TOP, BOTTOM, LEFTRIGHT, RIGHTLEFT
            "corners": {},         # TOPLEFT, TOPRIGHT, BOTTOMRIGHT, BOTTOMLEFT
            "corner_types": {},    # radios de esquina
            "fill_style_id": None
        }

        # LADOS
        side_map = {
            "TopLine": "TOP",
            "BottomLine": "BOTTOM",
            "LeftLine": "LEFT",
            "RightLine": "RIGHT",
            "LeftRightLine": "LEFTRIGHT",
            "RightLeftLine": "RIGHTLEFT"
        }
        # ESQUINAS
        corner_map = {
            "UpperLeftCorner": "TOPLEFT",
            "RightTopCorner": "TOPRIGHT",
            "LowerRightCorner": "BOTTOMRIGHT",
            "LowerLeftCorner": "BOTTOMLEFT"
        }
        # RADIOS DE ESQUINA
        corner_type_map = {
            "UpperLeftCornerType": "TOPLEFT",
            "UpperRightCornerType": "TOPRIGHT",
            "LowerRightCornerType": "BOTTOMRIGHT",
            "LowerLeftCornerType": "BOTTOMLEFT"
        }

        for xml_tag, side in side_map.items():
            line_elem = border_elem.find(xml_tag)
            if line_elem is not None:
                fillstyle_id = line_elem.findtext("FillStyle")
                width = float(line_elem.findtext("LineWidth"))

                color = "#000000"
                if fillstyle_id and fillstyle_id in fillstyle_config:
                    color_id = fillstyle_config[fillstyle_id].findtext("ColorId")
                    if color_id and color_id in color_reportlab:
                        color = color_reportlab[color_id]

                
                    border_config["sides"][side] = {
                        "width": width,
                        "color": color
                    }        

        for xml_tag, corner in corner_map.items():
            corner_elem = border_elem.find(xml_tag)
            if corner_elem is not None:
                fillstyle_id = corner_elem.findtext("FillStyle")
                width = float(corner_elem.findtext("LineWidth") or 0.25)

                color = "#000000"
                if fillstyle_id and fillstyle_id in fillstyle_config:
                    color_id = fillstyle_config[fillstyle_id].findtext("ColorId")
                    if color_id and color_id in color_reportlab:
                        color = color_reportlab[color_id]

                border_config["corners"][corner] = {
                    "width": width,
                    "color": color
                }

        for xml_tag, corner in corner_type_map.items():
            elem = border_elem.find(xml_tag)
            if elem is not None:
                radius_elem = elem.find("CornerRadius")
                if radius_elem is not None:
                    rx = convert_units(radius_elem.get("X", 0))
                    ry = convert_units(radius_elem.get("Y", 0))
                    border_config["corner_types"][corner] = {
                        "rounded": rx > 0 or ry > 0,
                        "radius_x": rx,
                        "radius_y": ry
                    }

        # FillStyleId general (por si aplica)
        fsid_elem = border_elem.find("FillStyleId")
        if fsid_elem is not None and fsid_elem.text:
            border_config["fill_style_id"] = fsid_elem.text

        borderstyle_reportlab[border_id] = border_config

    print(f"{datetime.now()} Fin registro borderstyle")
    return borderstyle_reportlab