import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from api.models.schemas import TechniqueMatch, SearchResult
from config import settings

logger = logging.getLogger(__name__)


class RAGService:

    def __init__(
        self, model_name: Optional[str] = None, data_path: Optional[str] = None
    ):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.data_path = Path(data_path) if data_path else settings.MITRE_DATA_PATH
        self.model = None
        self.index = None
        self.techniques = []
        self.loaded = False

        logger.info(f"Iniciando serviço RAG com modelo: {self.model_name}")
        logger.info(f"Usando dados de: {self.data_path}")

        self._load_model()
        self._load_data()
        self._build_index()

    def _load_model(self):
        try:
            logger.info(f"Carregando modelo de embedding: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Modelo de embedding carregado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            raise

    def _load_data(self):
        try:
            logger.info(f"Carregando técnicas MITRE de: {self.data_path}")

            if not self.data_path.exists():
                raise FileNotFoundError(
                    f"Arquivo de dados não encontrado: {self.data_path}"
                )

            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                technique = {
                    "technique_id": item["output"]["technique_id"],
                    "technique_name": item["output"]["technique_name"],
                    "tactic": item["output"]["tactic"],
                    "description": item["input"],
                }
                self.techniques.append(technique)

            logger.info(f"Carregado {len(self.techniques)} técnicas MITRE")

        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            raise

    def _build_index(self):
        try:
            logger.info("Construindo índice FAISS...")

            descriptions = [t["description"] for t in self.techniques]
            embeddings = self.model.encode(
                descriptions, show_progress_bar=True, convert_to_numpy=True
            )

            faiss.normalize_L2(embeddings)

            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(embeddings)

            self.loaded = True
            logger.info(
                f"Índice FAISS construído com sucesso com {self.index.ntotal} vetores"
            )

        except Exception as e:
            logger.error(f"Erro ao construir índice: {e}")
            raise

    def search_techniques(self, query: str, top_k: int = 10) -> List[SearchResult]:
        try:
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)

            scores, indices = self.index.search(query_embedding, top_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if float(score) >= 0.7:
                    technique = self.techniques[idx]
                    results.append(
                        SearchResult(
                            technique_id=technique["technique_id"],
                            technique_name=technique["technique_name"],
                            tactic=technique["tactic"],
                            description=(
                                technique["description"][:500] + "..."
                                if len(technique["description"]) > 500
                                else technique["description"]
                            ),
                            similarity_score=float(score),
                        )
                    )

            return results

        except Exception as e:
            logger.error(f"Erro ao buscar técnicas: {e}")
            raise

    async def classify_narrative(self, narrative: str, top_k: int = 5) -> Dict:
        start_time = time.time()

        try:
            search_results = self.search_techniques(narrative, top_k=top_k)

            techniques = []
            for result in search_results:

                if result.similarity_score >= 0.7:
                    techniques.append(
                        TechniqueMatch(
                            technique_id=result.technique_id,
                            technique_name=result.technique_name,
                            tactic=result.tactic,
                            description=result.description,
                            similarity_score=result.similarity_score,
                            activity_description=None,
                            correction=None,
                        )
                    )

            processing_time = time.time() - start_time

            return {
                "narrative": narrative,
                "techniques": techniques,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"Erro classificando narrativa: {e}")
            raise

    def is_loaded(self) -> bool:
        return self.loaded

    def get_techniques_count(self) -> int:
        return len(self.techniques)
