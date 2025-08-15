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
            customer = "Pruebas"
            #customer = "Colsubsidio"
            product = "Factura"
            #product = "FacturasWS"

            #pathInput = "D:/ProyectoComunicaciones/ProyectoPDFGit/Datos/1_PE_860007336_FacturasWS_20250620_37F7155071DA4B57E0632A64A8C03854_Transform.json"
            pathInput = "D:/ProyectoComunicaciones/ProyectoPDFGit/Datos/PE_890904996_FacturasPrepago_20250627_DEEP10507508_2.json"
            
            pathOutput = "D:/ProyectoComunicaciones/ProyectoPDFGit/PDF-Generator\\tests\\data\\output.pdf"
            from loader.input_loader import load_input
            from pdf.process_document import process_document
            config = load_input(pathInput, customer, product)
            documents = config.documents
        
            # Generar PDF por cada documento (puede ser solo uno)
            for i in range(1):
                for document in documents:
                    process_document(config, document, i)
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
