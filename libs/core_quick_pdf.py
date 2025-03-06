from typing import Optional

from libs.managers.core_pdf_manager import CorePdfManager


class CoreQuickPdf:
    def __init__(self, version: str):
        self._version = version
        self._pdf_manager: Optional[CorePdfManager] = None

    @property
    def pages(self):
        assert self._pdf_manager is not None
        return self._pdf_manager.pages

    @property
    def outlines(self):
        assert self._pdf_manager is not None
        return self._pdf_manager.outlines

    @property
    def metadata(self):
        assert self._pdf_manager is not None
        return self._pdf_manager.metadata

    def load_pdf_content(self, path: str):
        with open(path, "r") as f:
            self.outlines.load_from_json(f.read())

    def export_pdf_content(self, path: str):
        with open(path, "w") as f:
            f.write(self.outlines.jsonify())

    def load_pdf(self, path: str):
        self._pdf_manager = CorePdfManager(path, self._version)

    def export_pdf(self, path: str):
        assert self._pdf_manager is not None
        self._pdf_manager.save(path)
