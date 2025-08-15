from core.utils import convert_units

def register_parastyles(paras):
    def get_node_text(xml, node_name, default=None):
        node = xml.find(node_name)
        return node.text if node is not None else default
        
    ParaStyle_reportlab = {}

    for id, para in paras.items():
        left_indent = get_node_text(para,"LeftIndent",0)
        right_indent = get_node_text(para,"RightIndent")
        first_line_left_indent = get_node_text(para,"FirstLineLeftIndent")
        space_before = get_node_text(para,"SpaceBefore",0)
        space_after = get_node_text(para,"SpaceAfter",0)
        line_spacing = get_node_text(para,"LineSpacing")
        widow = get_node_text(para,"Widow")
        orphan = get_node_text(para,"Orphan")
        keep_with_next = get_node_text(para,"KeepWithNext")
        keep_lines_together = get_node_text(para,"KeepLinesTogether")
        dont_wrap = get_node_text(para,"DontWrap")

        h_align = get_node_text(para,"HAlign","Left")  # Valor por defecto "Left" si no existe el nodo
        align = 0  # TA_LEFT por defecto
        if h_align == "Center":
            align = 1  # TA_CENTER
        elif h_align == "Right":
            align = 2  # TA_RIGHT
        elif "Justify" in h_align:
            align = 4  # TA_JUSTIFY

        style_args = {"alignment": align}

        if left_indent is not None:
            style_args["leftIndent"] = convert_units(left_indent)
        if right_indent is not None:
            style_args["rightIndent"] = convert_units(right_indent)
        if first_line_left_indent is not None:
            style_args["firstLineIndent"] = convert_units(first_line_left_indent)
        if space_before is not None:
            style_args["spaceBefore"] = convert_units(space_before)
        if space_after is not None:
            style_args["spaceAfter"] = convert_units(space_after)
        if line_spacing is not None:
            style_args["leading"] = convert_units(line_spacing)                
        if widow is not None:
            style_args["allowWidows"] = widow
        if orphan is not None:
            style_args["allowOrphans"] = orphan
        if keep_with_next is not None:
            style_args["keepWithNext"] = keep_with_next
        if keep_lines_together is not None:
            style_args["keepTogether"] = keep_lines_together

        ParaStyle_reportlab[id] = style_args
                
    return ParaStyle_reportlab