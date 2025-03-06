from typing import Optional, cast, Union, Literal
from datetime import datetime

from pypdf import PdfReader, PdfWriter
from pypdf.constants import DocumentInformationAttributes as DocInfo

from libs.managers.types import Metadata

_MetaProp = Literal[
    "title",
    "author",
    "subject",
    "keywords",
    "creator",
    "producer",
    "creation_date",
    "mod_date",
    "trapped"
]

_RAW_METADATA_MAP: dict[str, _MetaProp] = {
    DocInfo.TITLE: "title",
    DocInfo.AUTHOR: "author",
    DocInfo.SUBJECT: "subject",
    DocInfo.KEYWORDS: "keywords",
    DocInfo.CREATOR: "creator",
    DocInfo.PRODUCER: "producer",
    DocInfo.CREATION_DATE: "creation_date",
    DocInfo.MOD_DATE: "mod_date",
    DocInfo.TRAPPED: "trapped",
}


def _parse_raw_metadata(metadata: dict[str, str]):
    parsed_metadata = {_RAW_METADATA_MAP.get(k): v for k, v in metadata.items()}
    metadata_args_completed = {k: parsed_metadata.get(k) or None for k in _RAW_METADATA_MAP.values()}
    return Metadata(**metadata_args_completed)


def _output_raw_metadata(metadata: Metadata):
    metadata_map_reversed = {v: k for k, v in _RAW_METADATA_MAP.items()}
    return {metadata_map_reversed.get(k): v for k, v in metadata.items() if v is not None}


class _MetadataManager:
    def __init__(self, reader: PdfReader, version: str):
        self._metadata = _parse_raw_metadata(reader.metadata or {})
        self.update("producer", f"Quick PDF Editor ({version})")

    def get(self, meta_prop: _MetaProp):
        return cast(dict[str, Optional[str]], self._metadata).get(meta_prop)

    def update(self, meta_prop: _MetaProp, meta_value: Union[str, None]):
        self._metadata.update({meta_prop: meta_value})

    def save(self, writer: PdfWriter):
        current_time = datetime.now().strftime("D\072%Y%m%d%H%M%S-05'00'")
        self.update("creation_date", current_time)
        self.update("mod_date", current_time)
        writer.add_metadata(_output_raw_metadata(self._metadata))
