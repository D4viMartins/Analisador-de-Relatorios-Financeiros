from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.responses import UploadResponse
from app.services.pdf_extractor import extract_pdf_content
from app.services.rag_service import ingest_document

router = APIRouter(prefix="/upload", tags=["upload"])
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)) -> UploadResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="O arquivo excede o limite de 10MB.")

    try:
        extracted = extract_pdf_content(file_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Não foi possível ler o PDF enviado.")

    if not extracted["text"]:
        raise HTTPException(status_code=400, detail="O PDF foi lido, mas não contém texto extraível.")

    try:
        document_id = ingest_document(filename=file.filename or "documento.pdf", text=extracted["text"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return UploadResponse(
        document_id=document_id,
        filename=file.filename or "documento.pdf",
        text=extracted["text"],
        page_count=extracted["page_count"],
        table_count=extracted["table_count"],
    )
