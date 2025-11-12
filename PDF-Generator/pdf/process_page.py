from core.utils import convert_units
from pdf.process_elements import process_elements_by_object
from core.utils import get_variable_value
from core.utils import evaluate_condition

def process_page(config, page, c):
        """Procesa una página del XML y dibuja sus elementos"""
        # Configurar tamaño de página
        width = page.find('Width').text
        height = page.find('Height').text
        page_width = convert_units(width)
        page_height = convert_units(height)
        page_id = page.find('Id').text
        page_name = config.data_dicts['Page'].get(page_id).find('Name').text
        condition_type_page = page.find("ConditionType").text
        print(f"{'-'*20} Procesando pagina {page_name} {'-'*20}")

        c.setPageSize((page_width,page_height))
  
        process_elements_by_object(config, page_id, page_width, page_height, c)
        c.showPage()
        # - Simple
        # - Condition
        # - InlCond
        # - Integer
        # - Interval
        if (condition_type_page == "Simple"):                        
            next_page_id = page.find("NextPageId")
            if next_page_id is not None:
                page_element = config.config_dicts['Page'].get(next_page_id.text)
                if page_element is not None:
                    process_page(config, page_element, c)

        elif (condition_type_page == "Condition"):
            page_condition_elements = page.findall("PageCondition")
            for page_condition_element in page_condition_elements:
                variable_condition_id = page_condition_element.find("ConditionId").text
                variables = config.data_dicts['Variable']
                full_context = config.full_context
                condition_to_evaluate = get_variable_value(variable_condition_id, variables, full_context)
                if condition_to_evaluate:
                    page_id = page_condition_element.find("PageId").text
                    break
            
            if page_id is None:
                page_id = page.find("DefaultPageId").text
            page_element = config.config_dicts['Page'].get(page_id.text)
            process_page(config, page_element, c)               
            
        elif (condition_type_page == "InlCond"):
            print("Inicio de proceso de paginas con InlCond")
            page_condition_elements = page.findall("PageCondition")
            for page_condition_element in page_condition_elements:
                condition = page_condition_element.find("Condition").text
                full_context = config.full_context
                if evaluate_condition(condition, full_context):                
                    page_id = page_condition_element.find("PageId").text
                    break
            page_element = config.config_dicts['Page'].get(page_id.text)
            process_page(config, page_element, c)
        else:
            # - Integer
            # - Interval
            print(f'Condicion de tipo "{condition_type_page}" no implementada')