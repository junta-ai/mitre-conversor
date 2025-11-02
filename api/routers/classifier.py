from fastapi import APIRouter, HTTPException, Request
from api.models.schemas import (
    ClassificationRequest, 
    ClassificationResponse,
    SearchRequest,
    SearchResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/classify", response_model=ClassificationResponse)
async def classify_narrative(
    request: Request,
    payload: ClassificationRequest
):
    try:
        rag_service = request.app.state.rag_service
        
        logger.info(f"Classificando narrativa (length: {len(payload.narrative)}, use_llm: {payload.use_llm})")
        
        result = await rag_service.classify_narrative(
            narrative=payload.narrative,
            top_k=payload.top_k
        )
        
        if payload.use_llm:
            try:
                llm_service = request.app.state.llm_service
                
                llm_result = await llm_service.generate_response_async(
                    narrative=payload.narrative,
                    techniques=result['techniques'],
                    language=payload.language
                )
                
                result['human_response'] = llm_result['response']
                result['llm_metadata'] = {
                    'model': llm_result['model'],
                    'language': llm_result['language'],
                    'generation_time': llm_result['generation_time']
                }
                
                logger.info(f"Resposta da LLM em {llm_result['generation_time']:.2f}s")
                
            except Exception as llm_error:
                logger.error(f"Erro ao gerar resposta da LLM: {llm_error}")
                result['human_response'] = None
                result['llm_metadata'] = {
                    'error': str(llm_error)
                }
        
        return ClassificationResponse(**result)
        
    except Exception as e:
        logger.error(f"Erro ao classificar narrativa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_techniques(
    request: Request,
    payload: SearchRequest
):
    try:
        rag_service = request.app.state.rag_service
        
        logger.info(f"Buscando técnicas para: {payload.query}")
        
        results = rag_service.search_techniques(
            query=payload.query,
            top_k=payload.top_k
        )
        
        return SearchResponse(
            query=payload.query,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Erro ao buscar técnicas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
