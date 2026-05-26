from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    filename: str = Field(..., description="Nome original do arquivo enviado")
    text: str = Field(..., description="Texto extraído do PDF")
    page_count: int = Field(..., ge=0, description="Quantidade de páginas processadas")
    table_count: int = Field(..., ge=0, description="Quantidade de tabelas extraídas")
