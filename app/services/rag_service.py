from __future__ import annotations

import math

import numpy as np

from app.services.chunking import chunk_text
from app.services.document_store import document_exists, get_document_chunks, save_document
from app.services.openai_service import embed_texts, generate_answer


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return matrix / norms


def _rank_by_similarity(embeddings: list[list[float]], query_embedding: list[float], top_k: int) -> list[int]:
    matrix = np.array(embeddings, dtype=np.float32)
    query = np.array(query_embedding, dtype=np.float32).reshape(1, -1)

    matrix = _normalize_rows(matrix)
    query = _normalize_rows(query)

    similarities = matrix @ query.T
    ranked = np.argsort(similarities[:, 0])[::-1]
    return ranked[:top_k].tolist()


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
    question_embedding = embed_texts([question])[0]
    k = min(top_k, len(chunks))
    indices = _rank_by_similarity(embeddings, question_embedding, k)

    relevant_chunks: list[str] = []
    for idx in indices:
        relevant_chunks.append(str(chunks[idx]["content"]))

    return relevant_chunks


def answer_question(document_id: str, question: str) -> str:
    chunks = retrieve_relevant_chunks(document_id, question)
    if not chunks:
        raise ValueError("Não foi possível recuperar contexto relevante para este documento.")

    context = "\n\n".join(chunks)
    return generate_answer(question=question, context=context)
