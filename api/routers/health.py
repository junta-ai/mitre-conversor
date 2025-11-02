from fastapi import APIRouter, Request
from api.models.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    rag_service = request.app.state.rag_service
    llm_service = getattr(request.app.state, 'llm_service', None)
    
    response_data = {
        "status": "healthy",
        "rag_loaded": rag_service.is_loaded(),
        "techniques_count": rag_service.get_techniques_count()
    }
    
    if llm_service:
        response_data["llm_available"] = llm_service.is_available()
        response_data["llm_model"] = llm_service.model_name
    else:
        response_data["llm_available"] = False
        response_data["llm_model"] = None
    
    return HealthResponse(**response_data)
