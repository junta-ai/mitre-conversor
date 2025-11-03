from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import classifier, health
from api.services.rag_service import RAGService
from api.services.llm_service import LLMService
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MITRE ATT&CK Classifier API",
    description="API para classificar narrativas de segurança em técnicas MITRE ATT&CK usando RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando API de classificação MITRE ATT&CK...")

    try:
        from api.services.rag_service import RAGService

        rag_service = RAGService()
        app.state.rag_service = rag_service
        logger.info("RAG Service principal iniciado com sucesso")
    except Exception as rag_error:
        logger.warning(f"Falha ao inicializar RAG Service principal: {rag_error}")
        try:

            from api.services.fallback_rag_service import FallbackRAGService

            rag_service = FallbackRAGService()
            app.state.rag_service = rag_service
            logger.info("RAG Service de fallback iniciado com sucesso")
        except Exception as fallback_error:
            logger.error(
                f"Falha ao inicializar RAG Service de fallback: {fallback_error}"
            )
            app.state.rag_service = None

    from config import settings

    if getattr(settings, "LLM_ENABLED", True):
        try:
            llm_service = LLMService()
            app.state.llm_service = llm_service
            logger.info("LLM Service iniciado com sucesso")
        except Exception as llm_error:
            logger.warning(f"Inicialização do serviço LLM falhou: {llm_error}")
            logger.warning(
                "Os recursos do LLM não estarão disponíveis. Para habilitar, certifique-se de que o Ollama esteja em execução."
            )
            app.state.llm_service = None
    else:
        app.state.llm_service = None
        logger.info("LLM desabilitado por configuração")

    if app.state.rag_service is None:
        logger.error("Nenhum serviço RAG disponível - API não funcionará corretamente")
    else:
        service_type = type(app.state.rag_service).__name__
        if "Fallback" in service_type:
            logger.warning(
                "API rodando com serviço RAG de fallback - precisão reduzida"
            )
        else:
            logger.info("API iniciada com todos os serviços principais")


app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(classifier.router, prefix="/api", tags=["classifier"])


@app.get("/")
async def root():
    return {
        "message": "MITRE ATT&CK Classifier API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
