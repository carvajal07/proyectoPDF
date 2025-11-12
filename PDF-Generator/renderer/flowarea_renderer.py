from renderer.flow_renderer import process_flow
from renderer.border_renderer import draw_border
from core.utils import convert_units
from reportlab.platypus import Frame

def process_flows_areas(config, flowarea_element, page_height, page_width, c, parent_offset=(0,0), element=False):
    flow_area_id = flowarea_element.find('Id').text
    if flow_area_id == "177": #Este es el element, se deben aplicar estos offset a todos sus hijos
        #Hijos:
        #    178,179,180 y 181 shape
        print(f"offset flowarea: {flow_area_id}")
        print(f"x:{parent_offset[0]}")
        print(f"y:{parent_offset[1]}")
    #x:37.12502004750002
    #y:548.1499023000003

    #ids_flow_areas = ids_flow_areas_by_pages.get(page_id)

    flowing = flowarea_element.find('FlowingToNextPage')
    
    flow_id = flowarea_element.find('FlowId').text
    flow_border_id = flowarea_element.find("BorderStyleId").text        

    pos = flowarea_element.find('Pos')
    size = flowarea_element.find('Size')

    p_x = convert_units(pos.get('X',0)) + parent_offset[0]
    p_y = convert_units(pos.get('Y',0)) + parent_offset[1]
    s_x = convert_units(size.get('X',0))
    s_y = convert_units(size.get('Y',0))
    
    ##############PROCESO ANTERIOR######################
    '''
    if flow_border_id is not None:
        border_conf = BorderStyle_config[flow_border_id]
        sides = border_conf.get("sides", {})
        for side, props in sides.items():
            width = props.get("width", 0.5)
            color = props.get("color", "#000000")
            color_obj = colors.HexColor(color)
            c.setStrokeColor(color_obj)
            c.setLineWidth(width)
        c.rect(p_x, (page_height - p_y - s_y), s_x, s_y, fill=0)
    '''
    ####################################################

    if flow_border_id is not None:
        border_conf = config.borderstyle_reportlabs[flow_border_id]

        fillstyle_config = config.config_dicts['FillStyle']
        colors_reportlab = config.colors_reportlabs

        draw_border(c, fillstyle_config, colors_reportlab, p_x, (page_height - p_y - s_y), s_x, s_y, border_conf)

    if element:
        offset_x = parent_offset[0]
        offset_y = parent_offset[1]
    else:
        offset_x = p_x
        offset_y = p_y
    
    
    frame = Frame(
        x1=p_x,
        y1=page_height - p_y - s_y,
        width=s_x,
        height=s_y,
        id=f"frame_{flow_area_id}",
        showBoundary=0,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0
    )
    flows = config.config_dicts['Flow']
    flow = flows.get(flow_id) 
    if flow_id == "180":
        #print("Pausa")
        pass           
    

    #print(f"Procesando Flow con Id: {flow_id}")

    if flow is not None:
        para, min_height_default = process_flow(config, flow, page_height, page_width, c=c, parent_offset=(offset_x,offset_y),max_width=s_x)

    
        
    try:    
        frame.addFromList(para,c)
    except Exception as e:
        print(f"Error al agregar el frame: {e}")
        print(f"FlowArea Id: {flow_area_id}, Pos: ({p_x}, {p_y}), Size: ({s_x}, {s_y})")
