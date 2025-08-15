import xml.etree.ElementTree as ET
import re
from decimal import Decimal, InvalidOperation, getcontext, ROUND_DOWN

def parse_fcv_props(xml_content_string):
    """
    Parsea el XML de FCVProps para extraer las propiedades de formateo.
    """
    try:
        root = ET.fromstring(xml_content_string)
        props = {}
        props['InDecimalSeparator'] = root.findtext('InDecimalSeparator', default='.')
        props['OutDecimalSeparator'] = root.findtext('OutDecimalSeparator', default=',')
        props['OutGroupSeparator'] = root.findtext('OutGroupSeparator', default='.')
        props['OutDigitsAfterDecimal'] = int(root.findtext('OutDigitsAfterDecimal', default='0'))
        props['OutDigitsBeforeDecimal'] = int(root.findtext('OutDigitsBeforeDecimal', default='0'))
        props['OutPadding'] = root.findtext('OutPadding', default='Blank')
        props['OutSignPosition'] = root.findtext('OutSignPosition', default='Sign before number')
        props['PrintZeroValue'] = root.findtext('PrintZeroValue', default='Input Dependent')
        props['EmptyOutput'] = root.findtext('EmptyOutput', default='LikePrintNet3')
        props['OutPrintPlus'] = root.findtext('OutPrintPlus', default='Never')
        return props
    except (ET.ParseError, ValueError) as e:
        print(f"Error al parsear el XML o convertir el tipo de dato: {e}")
        return None

def format_number_string_final(input_str, props):
    """
    Formatea un string numérico de acuerdo a las propiedades dadas,
    aplicando truncamiento en lugar de redondeo.
    """
    if not isinstance(input_str, str) or not input_str:
        return ""

    in_decimal_separator = props.get('InDecimalSeparator', '.')
    temp_str = input_str.strip()
    
    in_group_separator = props.get('InGroupSeparator', '')
    if in_group_separator:
        temp_str = temp_str.replace(in_group_separator, '')
    
    temp_str = temp_str.replace(in_decimal_separator, '.')

    try:
        # Usamos Decimal para una precisión fija y control sobre el truncamiento
        num = Decimal(temp_str)
    except (ValueError, TypeError, InvalidOperation):
        return ""

    out_digits_after_decimal = props.get('OutDigitsAfterDecimal', 0)
    out_group_separator = props.get('OutGroupSeparator', '.')
    out_decimal_separator = props.get('OutDecimalSeparator', ',')
    out_digits_before_decimal = props.get('OutDigitsBeforeDecimal', 0)
    out_print_plus = props.get('OutPrintPlus', 'Never')

    sign = ""
    if num < 0:
        sign = "-"
        num = abs(num)
    elif num > 0 and out_print_plus != 'Never':
        sign = "+"

    # Truncamos el número a la cantidad de decimales deseada
    quantizer = Decimal(10) ** -out_digits_after_decimal
    truncated_num = num.quantize(quantizer, rounding=ROUND_DOWN)

    formatted_num = str(truncated_num)
    
    if '.' in formatted_num:
        integer_part, decimal_part = formatted_num.split('.')
    else:
        integer_part = formatted_num
        decimal_part = ""
    
    # Aseguramos que la parte decimal tenga el largo correcto con ceros
    if out_digits_after_decimal > 0:
        decimal_part = decimal_part.ljust(out_digits_after_decimal, '0')
    
    integer_part_with_groups = ""
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            integer_part_with_groups = out_group_separator + integer_part_with_groups
        integer_part_with_groups = digit + integer_part_with_groups
        
    padding_length = out_digits_before_decimal - len(integer_part)
    padding = " " * max(0, padding_length)
    
    final_output = f"{padding}{integer_part_with_groups}"
    
    if decimal_part:
        final_output += out_decimal_separator + decimal_part
        
    if sign and props.get('OutSignPosition') == 'Sign before number':
        final_output = f"{sign}{final_output.strip()}"
    elif sign and props.get('OutSignPosition') == 'Sign after number':
        final_output = f"{final_output.strip()}{sign}"
    
    return final_output.strip() if not sign else final_output.strip()


# --- Uso del script con la configuración XML y ejemplos ---

fcv_props_xml = """
<FCVProps>
    <InputType>String</InputType>
    <OutputType>String</OutputType>
    <InGroupSeparator/>
    <InDecimalSeparator>.</InDecimalSeparator>
    <InUnit>1</InUnit>
    <OutLeadingZeroes>No modification</OutLeadingZeroes>
    <OutPrintPlus>Never</OutPrintPlus>
    <OutDigitsAfterDecimal>2</OutDigitsAfterDecimal>
    <OutDigitsBeforeDecimal>3</OutDigitsBeforeDecimal>
    <OutGroupSeparator>.</OutGroupSeparator>
    <OutDecimalSeparator>,</OutDecimalSeparator>
    <OutPadding>Blank</OutPadding>
    <OutSignPosition>Sign before number</OutSignPosition>
    <PrintZeroValue>Input Dependent</PrintZeroValue>
    <EmptyOutput>LikePrintNet3</EmptyOutput>
</FCVProps>
"""

props = parse_fcv_props(fcv_props_xml)

if props:
    ejemplos = {
        "123456,789": "123.456,78",
        "123,4": "123,40",
        "1000": "1.000,00",
        "-500": "-500,00",
        "0": "0,00",
        "12": "12,00",
        "123": "123,00",
        "": ""
    }

    print("Resultados de la transformación:")
    for entrada, expected in ejemplos.items():
        resultado = format_number_string_final(entrada, props)
        print(f"Entrada: '{entrada}' -> Salida: '{resultado}' (Esperado: '{expected}', Coincide: {resultado == expected})")
else:
    print("No se pudo ejecutar la transformación debido a un error en el parsing.")