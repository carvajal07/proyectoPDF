class PDFContext:
    """Contexto global del proceso de generación de PDF."""
    def __init__(self):
        self.globalPageCounter = 0
        self.pageCounter = 0
        self.pagesPerRecord = 0
        self.overflow = False
        self.currentRecordId = None
        self.metadata = {}
        self.fonts = {}

    def reset_record(self):
        """Resetea contadores al iniciar un nuevo registro (cliente, factura, etc.)."""
        self.pageCounter = 0
        self.pagesPerRecord = 0
        self.overflow = False

    def next_page(self):
        """Incrementa contadores de página."""
        self.globalPageCounter += 1
        self.pageCounter += 1
        self.pagesPerRecord += 1

    def __repr__(self):
        return (
            f"<PDFContext global={self.globalPageCounter} "
            f"record={self.pageCounter}/{self.pagesPerRecord} overflow={self.overflow}>"
        )
