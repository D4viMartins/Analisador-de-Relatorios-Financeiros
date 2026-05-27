from __future__ import annotations

from uuid import uuid4

_DOCUMENTS: dict[str, str] = {}


def save_document(text: str) -> str:
    document_id = uuid4().hex
    _DOCUMENTS[document_id] = text
    return document_id


def get_document(document_id: str) -> str | None:
    return _DOCUMENTS.get(document_id)


def clear_documents() -> None:
    _DOCUMENTS.clear()
