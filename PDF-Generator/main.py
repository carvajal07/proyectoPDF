import threading
import logging
import time

from interface.cli import run_cli_if_args
from interface.http_handler import run_http_server
from interface.queue_listener import start_queue_listener

# Configurar logging
logging.basicConfig(
    filename='pdf_service.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

pruebas = True
test = "TEST2"

def main():
    logging.info("Inicio del servicio Generador PDF")

    try:
        # Si se ejecuta con argumentos CLI, procesar y salir
        if run_cli_if_args():
            logging.info("Ejecución por CLI completada")
            return

        if pruebas:
            logging.info("Ejecutando en modo pruebas, no se iniciará el servidor HTTP ni la cola")
            inicio = time.time()
            test_path = r"D:/Proyectos/proyectoPDF/Tests"         
            
            match test:
                case "TEST1":
                    # ---TEST 1--- OK
                    # Generacion de formas, bordes, codigo QR...
                    customer = "Colsubsidio"
                    product = "FacturasWS"
                    file = "1_PE_860007336_FacturasWS_20250620_37F7155071DA4B57E0632A64A8C03854_Transform.json"
                    # ---TEST 1---

                case "TEST2":
                    # ---TEST 2---
                    customer = "Pruebas"
                    product = "Factura"
                    file = "PE_890904996_FacturasPrepago_20250627_DEEP10507508_2.json"
                    # ---TEST 2---

                case "TEST3":
                    # ---TEST 3---
                    customer = "Colfondos"
                    product = "PensionesObligatorias"
                    file = "Colfondos_1Registro_Formateado.json"
                    # ---TEST 3---
            
            pathInput = f"{test_path}/{test}/{file}"
            path_output = f"{test_path}/{test}/Salida"

            from loader.input_loader import load_input
            from pdf.process_document import process_document
            # En pruebas no se carga el xml con el esquema desde la BD, se usa el que esta en la ruta local del test
            config = load_input(pathInput, customer, product, pruebas)
            documents = config.documents
        
            # Generar PDF por cada documento (puede ser solo uno)
            for i in range(1):
                for document in documents:
                    process_document(config, document, path_output, i)
            # Guarda el tiempo de finalización
            fin = time.time()
            # Calcula la diferencia de tiempo
            tiempo_transcurrido = (fin - inicio) * 1000
            # Imprime el tiempo transcurrido en segundos
            print("Tiempo transcurrido:", round(tiempo_transcurrido, 2), "milisegundos")
        else:
            # Lanzar HTTP y Cola en paralelo
            http_thread = threading.Thread(target=run_http_server, daemon=True)
            queue_thread = threading.Thread(target=start_queue_listener, daemon=True)

            http_thread.start()
            logging.info("Servidor HTTP iniciado")

            queue_thread.start()
            logging.info("Escucha de cola iniciada")

            # Mantener el hilo principal vivo
            while True:
                time.sleep(60)
    except KeyboardInterrupt:
        print("Servicio detenido por el usuario")
    except Exception as e:
        logging.exception(f"Error en la ejecución del servicio: {e}")
    finally:
        logging.info("Servicio finalizado")


if __name__ == "__main__":
    main()
