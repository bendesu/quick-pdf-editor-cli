from typing import Optional, cast, Union, Callable
from dataclasses import dataclass

from PIL import Image
from pypdf import PdfReader, PageObject, PdfWriter
from pypdfium2 import PdfDocument


@dataclass()
class _Page:
    object: PageObject
    image: Image


class _PageManager:
    def __init__(self, pdfium_document: PdfDocument, reader: PdfReader):
        self._lazy_pages: list[Union[Callable[[], _Page], _Page]] = [
            (lambda page_num:
             lambda: _Page(reader.pages[page_num],
                           pdfium_document[page_num].render(scale=1, optimize_mode='lcd').to_pil())
             )(page_num)
            for page_num in range(len(reader.pages))
        ]

    def count(self):
        return len(self._lazy_pages)

    def get(self, page_num: int):
        assert 0 < page_num <= self.count(), "page number exceeds the document page limit"
        real_page_num = page_num - 1
        if callable(self._lazy_pages[real_page_num]):
            self._lazy_pages[real_page_num] = self._lazy_pages[real_page_num]()

        return cast(_Page, self._lazy_pages[real_page_num])

    def move(self, from_page_num: int, to_page_num: int):
        assert 0 < from_page_num <= self.count(), "page number (from) exceeds the document page limit"
        assert 0 < to_page_num <= self.count(), "page number (to) exceeds the document page limit"
        real_from = from_page_num - 1
        real_to = to_page_num - 1
        start_page_num, end_page_num = min(real_from, real_to), max(real_from, real_to)
        start_page = self._lazy_pages[start_page_num]
        for page_num in range(start_page_num, end_page_num):
            self._lazy_pages[page_num] = self._lazy_pages[page_num + 1]

        self._lazy_pages[end_page_num] = start_page

    def insert(self, page: _Page, page_num: Optional[int] = None):
        real_page_num = page_num or self.count()
        assert 0 <= real_page_num <= self.count(), "page number exceeds the document page limit"
        self._lazy_pages.insert(real_page_num, page)

    def remove(self, page_num: int):
        assert 0 < page_num <= self.count(), "page number exceeds the document page limit"
        del self._lazy_pages[page_num - 1]

    def save(self, writer: PdfWriter):
        for page_num in range(1, self.count() + 1):
            writer.add_page(self.get(page_num).object)
