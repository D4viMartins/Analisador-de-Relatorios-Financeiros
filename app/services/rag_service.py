from __future__ import annotations

import faiss
import numpy as np

from app.services.chunking import chunk_text
from app.services.document_store import document_exists, get_document_chunks, save_document
from app.services.openai_service import embed_texts, generate_answer


def _build_index(embeddings: list[list[float]]) -> faiss.IndexFlatIP:
    if not embeddings:
        raise ValueError("Não há embeddings para indexar.")

    matrix = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(matrix)
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)
    return index


def ingest_document(filename: str, text: str) -> str:
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("O documento não contém texto suficiente para chunking.")

    embeddings = embed_texts(chunks)
    if len(embeddings) != len(chunks):
        raise RuntimeError("A quantidade de embeddings não bate com os chunks gerados.")

    return save_document(filename=filename, text=text, chunks=chunks, embeddings=embeddings)


def retrieve_relevant_chunks(document_id: str, question: str, top_k: int = 4) -> list[str]:
    if not document_exists(document_id):
        raise ValueError("Documento não encontrado.")

    chunks = get_document_chunks(document_id)
    if not chunks:
        return []

    embeddings = [chunk["embedding"] for chunk in chunks]
    index = _build_index(embeddings)

    question_embedding = embed_texts([question])[0]
    query = np.array([question_embedding], dtype=np.float32)
    faiss.normalize_L2(query)

    k = min(top_k, len(chunks))
    scores, indices = index.search(query, k)

    relevant_chunks: list[str] = []
    for idx in indices[0]:
        if idx == -1:
            continue
        relevant_chunks.append(str(chunks[idx]["content"]))

    return relevant_chunks


def answer_question(document_id: str, question: str) -> str:
    chunks = retrieve_relevant_chunks(document_id, question)
    if not chunks:
        raise ValueError("Não foi possível recuperar contexto relevante para este documento.")

    context = "\n\n".join(chunks)
    return generate_answer(question=question, context=context)
