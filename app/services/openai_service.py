from __future__ import annotations

import os
from functools import lru_cache

from openai import OpenAI

from app.services.env_loader import load_dotenv_file

load_dotenv_file()

CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4-mini")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
SYSTEM_PROMPT = (
    "Você é um analista financeiro sênior. "
    "Responda apenas com base no contexto recuperado dos relatórios. "
    "Se faltar informação, diga isso explicitamente. "
    "Responda em texto simples, sem markdown, sem listas formatadas e sem negrito."
)


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Configure a variável de ambiente OPENAI_API_KEY.")
    return OpenAI(api_key=api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def generate_answer(question: str, context: str) -> str:
    client = get_openai_client()
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Use o contexto abaixo para responder a pergunta.\n\n"
                    f"CONTEXTO:\n{context}\n\n"
                    f"PERGUNTA: {question}\n\n"
                    "Escreva uma resposta direta, em texto simples, sem markdown."
                ),
            },
        ],
        temperature=0.2,
    )
    answer = response.choices[0].message.content or ""
    answer = answer.strip()
    if not answer:
        raise RuntimeError("A resposta da OpenAI veio vazia.")
    return answer
