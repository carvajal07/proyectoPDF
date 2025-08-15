from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loader.input_loader import load_input
from pdf.process_document import process_document
import xml.etree.ElementTree as ET
import json
import logging
import os

app = FastAPI()

class PDFRequest(BaseModel):
    customer: str
    product: str
    pathInput: str
    pathOutput: str

@app.post("/generar-pdf")
async def generar_pdf_endpoint(req: PDFRequest):
    try:
        # Verificar que el archivo JSON exista
        if not os.path.exists(req.pathInput):
            raise HTTPException(status_code=400, detail="El archivo JSON no existe")

        config = load_input(req.pathInput,req.customer,req.product)
        documents = config.documents
        
        # Generar PDF por cada documento (puede ser solo uno)
        for i in range(1):
            for document in documents:
                process_document(config, document, i)

        return {"status": "ok", "message": "PDF generado correctamente", "output": req.pathOutput}

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.exception("Error interno al generar el PDF")
        raise HTTPException(status_code=500, detail=str(e))

def run_http_server():
    import uvicorn
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        reload=False,      # ❌ evita recarga automática (solo para desarrollo)
        workers=1          # Puedes cambiar a más workers en producción
    )
    server = uvicorn.Server(config)
    logging.info("Servidor HTTP iniciado en http://0.0.0.0:5000")
    server.run()
    
