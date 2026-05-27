from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    document_id: str = Field(..., description="Identificador do documento armazenado em memória")
    filename: str = Field(..., description="Nome original do arquivo enviado")
    text: str = Field(..., description="Texto extraído do PDF")
    page_count: int = Field(..., ge=0, description="Quantidade de páginas processadas")
    table_count: int = Field(..., ge=0, description="Quantidade de tabelas extraídas")


class AskResponse(BaseModel):
    document_id: str = Field(..., description="Identificador do documento consultado")
    question: str = Field(..., description="Pergunta enviada pelo usuário")
    answer: str = Field(..., description="Resposta gerada pela LLM")
