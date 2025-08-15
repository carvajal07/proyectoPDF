from reportlab.pdfgen import canvas
from types import SimpleNamespace
import core.constants as const
from pdf.process_page import process_page
from core.utils import get_variable_value

def process_document(config, document, i):
    """Función auxiliar para generar un PDF en un proceso separado"""
    layout = config.layout
    full_context = config.full_context

    pages = layout.find('Pages') 

    full_context["Documents"] = document

    
    pdf_name = document.get("NombrePDF", None)
    print(pdf_name)
    if pdf_name is None:
        print("No se encontro la variable para el nombre del PDF")
        return

    pdf_path = f"D:\\ProyectoComunicaciones\\ProyectoPDFGit\\{i}_{pdf_name}"
    c = canvas.Canvas(pdf_path)
                                
    # Procesar páginas

                    
    selection_type = pages.find("SelectionType").text         

    page_id = None
    # - Variable
    # - Simple
    if (selection_type == "Variable"):
        print("Inicio de proceso de paginas variables")
        condition_type_pages = pages.find("ConditionType").text
        # - Simple
        # - Condition
        # - InlCond
        
        if (condition_type_pages == "Simple"):
            page_id = pages.find("FirstPageId").text

        elif (condition_type_pages == "Condition"):
            page_condition_elements = pages.findall("PageCondition")
            for page_condition_element in page_condition_elements:
                variable_condition_id = page_condition_element.find("ConditionId").text
                variables = config.data_dicts['Variable']
                full_context = config.full_context
                condition_to_evaluate = get_variable_value(variable_condition_id, variables, full_context)
                if condition_to_evaluate:
                    page_id = page_condition_element.find("PageId").text
                    break
            
            if page_id is None:
                page_id = pages.find("DefaultPageId").text                
            
        elif (condition_type_pages == "InlCond"):
            print("Inicio de proceso de paginas con InlCond")
        else:
            # - Integer
            # - Interval
            print(f'Condicion de tipo "{condition_type_pages}" no implementada')
        
        page_element = config.config_dicts['Page'].get(page_id)
        process_page(config, page_element, c, config)
        c.showPage()

        #Probar la captura de la siguiente pagina
        next_page_id_element = page_element.find("NextPageId")
        if next_page_id_element is not None:                
            page_element = config.config_dicts['Page'].get(next_page_id_element.text)
            process_page(config, page_element, c, config)
            c.showPage()
        
    elif (selection_type == "Simple"):
        #print("Inicio de proceso de paginas simples")
        for page_element in config.config_dicts['Page'].values():                
            process_page(config, page_element, c)
            c.showPage()
        
    else:
        print(f'Metodo de Page order "{selection_type}" no disponible')
    try:                   
        c.save()
    except Exception as e:
        print(f"Error al guardar el PDF: {e}")

    #Esta optimizacion no funciono
    #doc = fitz.open(output_filename)
    #doc.save("D:\ProyectoComunicaciones\ProyectoPDF\salida_optimizada.pdf", deflate=True)