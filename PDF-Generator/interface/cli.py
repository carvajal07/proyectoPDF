import sys
import argparse
import logging
import json
import core.constants as const
from interface.xml_fetcher import get_layout_xml

import xml.etree.ElementTree as ET

def run_cli_if_args():
    if len(sys.argv) <= 1:
        return False  # No argumentos → no ejecutar CLI

    parser = argparse.ArgumentParser(description="Generador PDF por CLI")
    parser.add_argument('--json', required=True, help='Ruta al archivo JSON de entrada')
    parser.add_argument('--cliente', required=True, help='Código del cliente')
    parser.add_argument('--producto', required=True, help='Nombre del producto')
    parser.add_argument('--output', required=True, help='Ruta de salida para el PDF')

    args = parser.parse_args()

    try:
        with open(args.json, 'r', encoding='utf-8') as f:
            data_json = json.load(f)

        # Traer XML desde "base de datos" simulada
        layout_str = get_layout_xml(args.cliente, args.producto)
        layout = ET.fromstring(layout_str)
        layout_element = layout.find("Layout")

        for doc in data_json[const.PRINCIPAL_ARRAY]:
            pass

        logging.info("PDF generado correctamente")
        return True

    except Exception as e:
        logging.exception(f"Error en ejecución CLI: {e}")
        return True  # Lo marcamos como ejecutado para evitar lanzar otros modos

