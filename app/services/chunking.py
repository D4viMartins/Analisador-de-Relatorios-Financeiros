from __future__ import annotations

import tiktoken

DEFAULT_CHUNK_TOKENS = 2000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_ENCODING = "o200k_base"


def chunk_text(text: str, chunk_tokens: int = DEFAULT_CHUNK_TOKENS, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
    if not text.strip():
        return []

    encoding = tiktoken.get_encoding(DEFAULT_ENCODING)
    token_ids = encoding.encode(text)
    if len(token_ids) <= chunk_tokens:
        return [text.strip()]

    chunks: list[str] = []
    start = 0

    while start < len(token_ids):
        end = min(start + chunk_tokens, len(token_ids))
        chunk = encoding.decode(token_ids[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(token_ids):
            break
        start = max(0, end - overlap)

    return chunks
