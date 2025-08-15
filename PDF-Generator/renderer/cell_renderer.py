def process_cell(config, cell_element, page_height, page_width, context=None, c=None, col_widths=[], col_index=0):
    from renderer.flow_renderer import process_flow
    """Procesa una celda dentro de una fila de la tabla"""
    if context is None:
        context = config.full_context
    all_elements = config.all_elements
    borderstyle_config = config.config_dicts['BorderStyle']
    flow_id = cell_element.find("FlowId").text if cell_element.find("FlowId") is not None else None
    max_width = col_widths[col_index]
    
    # Aplicar el borde a la celda segun los tamaños de ancho y alto
    # Varificar si tiene un BorderId
    if cell_element.find("BorderId") is not None:
        border_id = cell_element.find("BorderId").text
        if border_id in borderstyle_config:
            border_conf = borderstyle_config[border_id]
            # Obtener el ancho del borde
            width = border_conf.get("width", 0.25)
        

    if flow_id == "293":
        pass
        #print("Pausa")
    if flow_id:
        flow = all_elements.get(flow_id)
    
        if flow is not None:            
            return process_flow(config,flow,page_height,page_width,context=context,c=c,max_width=max_width)
    return ""  # Celda vacía