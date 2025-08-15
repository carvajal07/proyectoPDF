from core.utils import convert_units
from pdf.process_elements import process_elements_by_object

def process_page(config, page, c):
        """Procesa una página del XML y dibuja sus elementos"""
        # Configurar tamaño de página
        width = page.find('Width').text
        height = page.find('Height').text
        page_width = convert_units(width)
        page_height = convert_units(height)
        page_id = page.find('Id').text
        condition_type_page = page.find("ConditionType").text
        c.setPageSize((page_width,page_height))
  
        process_elements_by_object(config, page_id, page_width, page_height, c)
                
        if (condition_type_page == "Simple"):
            next_page_id = page.find("NextPageId")
            if next_page_id is not None:
                #procesar pagina con id siguiente
                #volver a llamar "process_page"
                pass 