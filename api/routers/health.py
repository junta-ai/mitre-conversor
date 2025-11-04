from fastapi import APIRouter, Request
from api.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    rag_service = getattr(request.app.state, "rag_service", None)
    llm_service = getattr(request.app.state, "llm_service", None)

    status = "healthy"
    if not rag_service:
        status = "degraded"

    response_data = {"status": status}

    if rag_service:
        response_data["rag_loaded"] = rag_service.is_loaded()
        response_data["techniques_count"] = rag_service.get_techniques_count()
    else:
        response_data["rag_loaded"] = False
        response_data["techniques_count"] = 0

    if llm_service:
        response_data["llm_available"] = llm_service.is_available()
        response_data["llm_model"] = llm_service.model_name
    else:
        response_data["llm_available"] = False
        response_data["llm_model"] = None

    return HealthResponse(**response_data)
