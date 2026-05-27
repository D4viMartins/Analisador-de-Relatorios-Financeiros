from __future__ import annotations

import json
from uuid import uuid4

from app.db.models import Document, DocumentChunk
from app.db.session import SessionLocal


def save_document(filename: str, text: str, chunks: list[str], embeddings: list[list[float]]) -> str:
    document_id = uuid4().hex
    with SessionLocal() as session:
        document = Document(id=document_id, filename=filename, text=text)
        session.add(document)
        session.flush()

        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
            session.add(
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=index,
                    content=chunk,
                    embedding_json=json.dumps(embedding),
                )
            )

        session.commit()

    return document_id


def get_document_text(document_id: str) -> str | None:
    with SessionLocal() as session:
        document = session.get(Document, document_id)
        return None if document is None else document.text


def get_document_chunks(document_id: str) -> list[dict[str, object]]:
    with SessionLocal() as session:
        chunks = (
            session.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

        return [
            {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "embedding": json.loads(chunk.embedding_json),
            }
            for chunk in chunks
        ]


def document_exists(document_id: str) -> bool:
    with SessionLocal() as session:
        return session.get(Document, document_id) is not None


def clear_database() -> None:
    with SessionLocal() as session:
        session.query(DocumentChunk).delete()
        session.query(Document).delete()
        session.commit()
