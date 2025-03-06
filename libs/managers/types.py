from typing import Optional, TypedDict


class Outline(TypedDict):
    id: int
    title: str
    page_num: int
    parent_id: Optional[int]


class Metadata(TypedDict):
    title: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    keywords: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]
    mod_date: Optional[str]
    trapped: Optional[str]
