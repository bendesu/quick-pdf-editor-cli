from typing import Optional, cast, TypedDict, Self
from itertools import chain
from json import dumps, loads

from pypdf import PdfReader, PdfWriter
from pypdf.generic import IndirectObject
from pypdf.types import OutlineType

from libs.managers._page_manager import _PageManager
from libs.managers.types import Outline


class _JSONOutlineNode(TypedDict):
    title: str
    page_num: int
    child_nodes: Optional[list[Self]]


class _CreatedOutline(Outline):
    indirect_ref: IndirectObject


def _organize_outlines(outlines: list[Outline]):
    next_available_id = 1

    def sort_outlines(_outlines: list[Outline]):
        _sorted_outline_page_num_set = sorted(set([ol.get("page_num") for ol in _outlines]))
        _sorted_outlines_list = [
            [ol for ol in _outlines if ol.get("page_num") == page_num] for page_num in _sorted_outline_page_num_set
        ]

        _sorted_id_ranked_outlines_list = [sorted(ols, key=lambda _: _.get('id')) for ols in _sorted_outlines_list]
        return cast(list[Outline], list(chain(*_sorted_id_ranked_outlines_list)))

    def organize_outlines(_outlines: list[Outline]):
        nonlocal next_available_id
        _new_outlines: list[Outline] = []
        _id_map: list[tuple[int, int]] = []
        for _outline in _outlines:
            _new_parent_ids = [
                _id_pair for _id_pair in _id_map if
                _outline.get("parent_id") is not None and _id_pair[1] == _outline.get("parent_id")
            ]

            _new_parent_id = _new_parent_ids[0][0] if len(_new_parent_ids) > 0 else None
            _new_outline_id = next_available_id
            _id_map.append((_new_outline_id, _outline.get("id")))
            _new_outlines.append(Outline(**{**_outline, "id": _new_outline_id, "parent_id": _new_parent_id}))
            next_available_id += 1

        return _new_outlines

    return organize_outlines(sort_outlines(outlines))


def _process_raw_outlines(raw_outlines: list[Outline]):
    def process_title(_title: str):
        return "".join([c for c in _title if c.isprintable()]).strip()

    def process_outlines(_new_outlines: list[Outline], _outlines: list[Outline], _parent_id: Optional[int] = None):
        if _parent_id is None:
            for _outline in [
                ol for ol in _outlines if ol.get("parent_id") is None and len(process_title(ol.get("title"))) > 0
            ]:
                _new_outlines.append(_outline)
                process_outlines(_new_outlines, _outlines, _parent_id=_outline.get("id"))
            return _new_outlines

        _parent_outlines = [ol for ol in _new_outlines if ol.get("id") == _parent_id]
        _parent_outline = _parent_outlines[0] if len(_parent_outlines) > 0 else None
        if _parent_outline is None:
            return _new_outlines

        for _outline in [
            ol for ol in _outlines if
            ol.get("parent_id") == _parent_id and ol.get("page_num") >= _parent_outline.get("page_num") and len(
                process_title(ol.get("title"))) > 0
        ]:
            _new_outlines.append(_outline)
            process_outlines(_new_outlines, _outlines, _parent_id=_outline.get("id"))

        return _new_outlines

    outlines = process_outlines([], raw_outlines)
    for outline in outlines:
        outline.update({"title": process_title(outline.get("title")), "parent_id": outline.get("parent_id")})

    return outlines


def _parse_and_get_raw_outlines(
        pdf_reader: PdfReader,
        next_outline_id: int = 1,
        next_origin_outlines: Optional[OutlineType] = None,
        parent_id: Optional[int] = None,
        page_indirect_refs: Optional[list[IndirectObject | None]] = None
):
    outlines: list[Outline] = []
    outline_id = next_outline_id
    origin_outlines = next_origin_outlines or pdf_reader.outline or []
    page_indirect_references = page_indirect_refs or [page.indirect_reference for page in pdf_reader.pages]

    for i in range(0, len(origin_outlines)):
        origin_outline = origin_outlines[i]

        if type(origin_outline) is not list:
            title = origin_outline.title
            page_num = page_indirect_references.index(origin_outline.page) if (
                    page_indirect_references and origin_outline.page in page_indirect_references) else None

            if title is not None and page_num is not None:
                outlines.append(Outline(id=outline_id, title=title, page_num=page_num, parent_id=parent_id))
                outline_id += 1
        else:
            children = _parse_and_get_raw_outlines(
                pdf_reader,
                next_outline_id=outline_id,
                next_origin_outlines=origin_outline,
                parent_id=outline_id - 1 if outline_id > 1 else None,
                page_indirect_refs=page_indirect_references
            )

            outlines = [*outlines, *children]
            outline_id += len(children)

    return outlines


class _OutlineManager:
    def __init__(self, page_manager: _PageManager, initial_reader: PdfReader):
        self._page_manager = page_manager
        self._outlines = _organize_outlines(_process_raw_outlines(_parse_and_get_raw_outlines(initial_reader)))

    def _find(self, outline_id: int):
        outlines: list[Outline] = list(filter(lambda outline: outline.get('id') == outline_id, self._outlines))
        return outlines[0] if len(outlines) > 0 else None

    def get_all(self):
        return cast(list[Outline], [{**ol, "page_num": ol.get("page_num") + 1} for ol in self._outlines])

    def get(self, outline_id: int, error_message: Optional[str] = None):
        outline = self._find(outline_id)
        assert outline is not None, error_message or "outline id not found"
        return cast(Outline, {**outline, "page_num": outline.get("page_num") + 1})

    def jsonify(self):
        outline_id_map: list[tuple[int, list[int]]] = []
        json_obj: list[_JSONOutlineNode] = []
        for outline in self.get_all():
            current_node = _JSONOutlineNode(
                page_num=outline.get("page_num"),
                title=outline.get("title"),
                child_nodes=None
            )

            parent_id_mapped_temp = [id_map for id_map in outline_id_map if id_map[0] == outline.get("parent_id")]
            parent_id_mapped = parent_id_mapped_temp[0] if len(parent_id_mapped_temp) > 0 else None
            if parent_id_mapped is not None:
                parent_obj: Optional[_JSONOutlineNode] = None
                for idx in parent_id_mapped[1]:
                    parent_obj = parent_obj.get("child_nodes")[idx] if parent_obj is not None else json_obj[idx]

                if parent_obj is not None:
                    parent_obj_child_nodes = parent_obj.get("child_nodes") or []
                    outline_id_map.append((outline.get("id"), [*parent_id_mapped[1], len(parent_obj_child_nodes)]))
                    parent_obj.update({"child_nodes": [*parent_obj_child_nodes, current_node]})
            else:
                outline_id_map.append((outline.get("id"), [len(json_obj)]))
                json_obj.append(current_node)

        return dumps(json_obj, indent=2)

    def load_from_json(self, json_str: str):
        next_outline_id = 0
        raw_outlines: list[Outline] = []

        def build_outlines(json_nodes: list[_JSONOutlineNode], parent_id: Optional[int] = None):
            nonlocal next_outline_id
            for json_node in json_nodes:
                page_num = min(int(json_node.get("page_num")), self._page_manager.count()) - 1
                next_outline_id = next_outline_id + 1
                raw_outlines.append(
                    Outline(
                        id=next_outline_id,
                        title=json_node.get("title"),
                        page_num=page_num,
                        parent_id=parent_id
                    )
                )

                if json_node.get("child_nodes") is not None:
                    build_outlines(json_node.get("child_nodes"), next_outline_id)

        json_obj: list[_JSONOutlineNode] = loads(json_str)
        build_outlines(json_obj)
        self._outlines = _organize_outlines(_process_raw_outlines(raw_outlines))

    def insert(self, title: str, page_num: int, parent_id: Optional[int] = None):
        def increase_outlines_id(_outlines: list[Outline], _additional_value: Optional[int] = 1):
            _new_outlines: list[Outline] = []
            _outline_ids = [_ol.get("id") for _ol in _outlines]
            for _outline in _outlines:
                _parent_id_temp = _outline.get("parent_id")
                _parent_id = _parent_id_temp + _additional_value if \
                    (_parent_id_temp is not None and _parent_id_temp in _outline_ids) else _parent_id_temp

                _outline_id = _outline.get("id") + _additional_value
                _new_outlines.append(Outline(**{**_outline, "id": _outline_id, "parent_id": _parent_id}))

            return _new_outlines

        assert 0 < page_num <= self._page_manager.count(), "page number exceeds the document page limit"
        real_page_num = page_num - 1
        parent = self._find(parent_id) if parent_id is not None else None
        assert (parent is not None and parent_id is not None) or (
                parent is None and parent_id is None), 'parent id not found'

        assert (parent is not None and parent.get('page_num') <= real_page_num) or (
                parent is None), 'page number should be greater or equal to parent\'s page number'

        smaller_page_num_outlines = [outline for outline in self._outlines if outline.get("page_num") <= real_page_num]
        greater_page_num_outlines = [outline for outline in self._outlines if outline.get("page_num") > real_page_num]
        new_outline_id_temp = max([0, *[outline.get('id') for outline in smaller_page_num_outlines]]) + 1
        new_outline_id = min([new_outline_id_temp, *[outline.get('id') for outline in greater_page_num_outlines]])
        self._outlines = _organize_outlines([
            *smaller_page_num_outlines,
            Outline(id=new_outline_id, title=title, page_num=real_page_num, parent_id=parent_id),
            *increase_outlines_id(greater_page_num_outlines)
        ])

        return self.get(new_outline_id, error_message="inserting outline failed")

    def update(self, outline_id: int, title: Optional[str] = None, page_num: Optional[int] = None,
               parent_id: Optional[int] = None):
        outline = self._find(outline_id)
        page_num = page_num or outline.get("page_num") + 1
        parent = self._find(parent_id) if parent_id is not None else None
        assert 0 < page_num <= self._page_manager.count(), "page number exceeds the document page limit"
        assert outline is not None, "outline id not found"
        assert (parent is not None and parent_id is not None) or (
                parent is None and parent_id is None), 'parent id not found'

        real_page_num = page_num - 1
        assert (parent is not None and parent.get('page_num') <= real_page_num) or (
                parent is None), 'page number should be greater or equal to parent\'s page number'

        outline.update({
            "title": title or outline.get("title"),
            "page_num": real_page_num,
            "parent_id": parent_id
        })

        return self.get(outline_id, error_message="updating outline failed")

    def remove(self, outline_id: int):
        def remove_outline_helper(_outline_id: int):
            _outline_ids_to_remove: list[int] = []
            for _child in [_outline for _outline in self._outlines if _outline_id == _outline.get('parent_id')]:
                _outline_ids_to_remove = [*_outline_ids_to_remove, *remove_outline_helper(_child.get('id'))]

            _outline_ids_to_remove.append(_outline_id)
            return _outline_ids_to_remove

        removed_outline = self._find(outline_id)
        assert removed_outline is not None, "outline id not found"
        self._outlines = _organize_outlines([outline for outline in self._outlines if
                                             outline.get("id") not in remove_outline_helper(outline_id)])

    def save(self, writer: PdfWriter):
        created_outlines: list[_CreatedOutline] = []
        for outline in sorted(self._outlines, key=lambda _: _.get('id')):
            page_num = outline.get('page_num')
            assert 0 <= page_num < self._page_manager.count(), "page number exceeds the document page limit"
            title = outline.get('title')
            parent_id = outline.get('parent_id')
            parents = list(
                filter(
                    lambda parent_outline: parent_id is not None and parent_outline.get('id') == parent_id,
                    created_outlines
                )
            )

            parent = cast(_CreatedOutline, parents[0]).get('indirect_ref') if len(parents) > 0 else None
            outline_indirect_ref = writer.add_outline_item(title, page_num, parent)
            created_outlines.append(_CreatedOutline(**outline, indirect_ref=outline_indirect_ref))
