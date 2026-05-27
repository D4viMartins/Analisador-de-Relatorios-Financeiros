from __future__ import annotations

import os

from app.services.document_store import get_document

SYSTEM_PROMPT = (
    "Você é um analista financeiro sênior. "
    "Responda apenas com base no documento fornecido. "
    "Se a informação não estiver clara no documento, diga isso explicitamente."
)
DEFAULT_MODEL = "claude-sonnet-4-20250514"


def get_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Configure a variável de ambiente ANTHROPIC_API_KEY.")

    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Instale a dependência anthropic para usar o endpoint /ask.") from exc

    return anthropic.Anthropic(api_key=api_key)


def answer_question(document_id: str, question: str) -> str:
    document_text = get_document(document_id)
    if document_text is None:
        raise ValueError("Documento não encontrado.")

    client = get_anthropic_client()
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Use o texto abaixo para responder a pergunta.\n\n"
                    f"TEXTO DO DOCUMENTO:\n{document_text}\n\n"
                    f"PERGUNTA: {question}"
                ),
            }
        ],
    )

    text_parts = []
    for block in response.content:
        block_text = getattr(block, "text", None)
        if block_text:
            text_parts.append(block_text)

    answer = "\n".join(text_parts).strip()
    if not answer:
        raise RuntimeError("A resposta da Anthropic veio vazia.")

    return answer
