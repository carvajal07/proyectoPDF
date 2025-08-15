def register_colors(colors):
    #Los colores los usan los fillstyle
    #los fillstyle los usan los textStyle, formas, codigos barras
    #los textStyle los usan los parraghrapstyle y los flow
    #los parraghrapstyle los usan los flow

    color_reportlab = {}
    for id, color in colors.items():
        color_string = color.find("RGB").text
        color_name = color.find("RGB").text
        r, g, b = map(float, color_string.split(","))                                                           
        
        #Agregar color en hex
        r_hex, g_hex, b_hex = int(r * 255), int(g * 255), int(b * 255)
        hex_color = "#{:02x}{:02x}{:02x}".format(r_hex, g_hex, b_hex)
        color_reportlab[id] = hex_color

    return color_reportlab