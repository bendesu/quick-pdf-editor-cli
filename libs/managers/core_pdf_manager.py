from io import BytesIO

from pypdf import PdfReader, PdfWriter
from pypdfium2 import PdfDocument

from libs.managers._metadata_manager import _MetadataManager
from libs.managers._outline_manager import _OutlineManager
from libs.managers._page_manager import _PageManager


class CorePdfManager:
    def __init__(self, pdf_path: str, version: str):
        with open(pdf_path, "rb") as f:
            self._pdf_buffer = BytesIO(f.read())
            self._pdf_reader = PdfReader(self._pdf_buffer)
            self._pdfium_document = PdfDocument(self._pdf_buffer)
            self.pages = _PageManager(self._pdfium_document, self._pdf_reader)
            self.outlines = _OutlineManager(self.pages, self._pdf_reader)
            self.metadata = _MetadataManager(self._pdf_reader, version)

    def save(self, path: str):
        writer = PdfWriter()
        self.pages.save(writer)
        self.outlines.save(writer)
        self.metadata.save(writer)
        with open(path, "wb") as f:
            writer.write(f)
