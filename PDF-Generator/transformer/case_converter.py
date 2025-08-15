def convert_string(input_string: str, case_type: str) -> str:
    """
    Convierte una cadena de texto a mayúsculas, minúsculas, capitalizada o cada palabra capitalizada según el tipo especificado.

    Args:
        input_string (str): La cadena de texto a convertir.
        case_type (str): El tipo de conversión ('upper', 'lower', 'capitalize').

    Returns:
        str: La cadena convertida.
    """
    if case_type == 'UpperCase':
        return input_string.upper()
    elif case_type == 'LowerCase':
        return input_string.lower()
    elif case_type == 'TitleCase':
        return input_string.capitalize()
    elif case_type == 'TitleCaseEachWord':
        return input_string.title()
    else:
        raise ValueError("Tipo de conversión no válido. Use 'UpperCase', 'LowerCase', 'TitleCase' o 'TitleCaseEachWord'.")
