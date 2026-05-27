from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    document_id: str = Field(..., min_length=1, description="Identificador do documento carregado")
    question: str = Field(..., min_length=1, description="Pergunta em linguagem natural")
