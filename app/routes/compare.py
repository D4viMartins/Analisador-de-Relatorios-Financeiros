from fastapi import APIRouter, HTTPException

from app.models.analysis import CompareRequest, CompareResponse
from app.services.financial_analysis import compare_documents

router = APIRouter(prefix="/compare", tags=["analysis"])


@router.post("", response_model=CompareResponse)
def compare(payload: CompareRequest) -> CompareResponse:
    try:
        return compare_documents(payload.document_id_a, payload.document_id_b)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
