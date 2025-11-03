from fastapi import APIRouter, HTTPException, Request
from api.models.schemas import (
    ClassificationRequest,
    ClassificationResponse,
    SearchRequest,
    SearchResponse,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/classify", response_model=ClassificationResponse)
async def classify_narrative(request: Request, payload: ClassificationRequest):
    try:
        rag_service = getattr(request.app.state, "rag_service", None)

        if not rag_service:
            raise HTTPException(
                status_code=503,
                detail="Serviço RAG não disponível. API em modo degradado.",
            )

        logger.info(
            f"Classificando narrativa (length: {len(payload.narrative)}, use_llm: {payload.use_llm})"
        )

        result = await rag_service.classify_narrative(
            narrative=payload.narrative, top_k=payload.top_k
        )

        if payload.use_llm:
            try:
                llm_service = getattr(request.app.state, "llm_service", None)

                if llm_service:
                    llm_result = await llm_service.generate_response_async(
                        narrative=payload.narrative,
                        techniques=result["techniques"],
                        language=payload.language,
                    )

                    result["human_response"] = llm_result["response"]
                    result["llm_metadata"] = {
                        "model": llm_result["model"],
                        "language": llm_result["language"],
                        "generation_time": llm_result["generation_time"],
                    }

                    logger.info(
                        f"Resposta da LLM em {llm_result['generation_time']:.2f}s"
                    )
                else:
                    result["human_response"] = (
                        "Serviço LLM não está disponível no momento."
                    )
                    result["llm_metadata"] = {"error": "LLM service not available"}

            except Exception as llm_error:
                logger.error(f"Erro ao gerar resposta da LLM: {llm_error}")
                result["human_response"] = None
                result["llm_metadata"] = {"error": str(llm_error)}

        return ClassificationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao classificar narrativa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_techniques(request: Request, payload: SearchRequest):
    try:
        rag_service = getattr(request.app.state, "rag_service", None)

        if not rag_service:
            raise HTTPException(
                status_code=503,
                detail="Serviço RAG não disponível. API em modo degradado.",
            )

        logger.info(f"Buscando técnicas para: {payload.query}")

        results = rag_service.search_techniques(
            query=payload.query, top_k=payload.top_k
        )

        return SearchResponse(query=payload.query, results=results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar técnicas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
