from fastapi import APIRouter, HTTPException

from app.models.requests import AskRequest
from app.models.responses import AskResponse
from app.services.rag_service import answer_question

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    try:
        answer = answer_question(payload.document_id, payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return AskResponse(
        document_id=payload.document_id,
        question=payload.question,
        answer=answer,
    )
