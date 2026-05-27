from fastapi import APIRouter, HTTPException

from app.models.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.financial_analysis import analyze_document

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze_document(payload.document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
