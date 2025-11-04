"""
Serviço RAG de fallback que funciona sem modelos ML
Usado quando há problemas para carregar o SentenceTransformer
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
import re

from api.models.schemas import TechniqueMatch, SearchResult
from config import settings

logger = logging.getLogger(__name__)


class FallbackRAGService:
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = Path(data_path) if data_path else settings.MITRE_DATA_PATH
        self.techniques = []
        self.loaded = False

        logger.info("Iniciando serviço RAG de fallback (sem ML)")
        logger.info(f"Usando dados de: {self.data_path}")

        self._load_data()

    def _load_data(self):
        try:
            logger.info(f"Carregando técnicas MITRE de: {self.data_path}")

            if not self.data_path.exists():
                logger.warning(f"Arquivo de dados não encontrado: {self.data_path}")
                self.techniques = []
                self.loaded = True
                return

            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                technique = {
                    "technique_id": item["output"]["technique_id"],
                    "technique_name": item["output"]["technique_name"],
                    "tactic": item["output"]["tactic"],
                    "description": item["input"],
                    "keywords": self._extract_keywords(item["input"]),
                }
                self.techniques.append(technique)

            self.loaded = True
            logger.info(
                f"Carregado {len(self.techniques)} técnicas MITRE (fallback mode)"
            )

        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            self.techniques = []
            self.loaded = True

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave simples do texto"""

        words = re.findall(r"\b[a-záàâãéèêíìîóòôõúùûç]+\b", text.lower())

        stopwords = {
            "de",
            "da",
            "do",
            "das",
            "dos",
            "e",
            "o",
            "a",
            "os",
            "as",
            "um",
            "uma",
            "para",
            "com",
            "por",
            "em",
            "na",
            "no",
            "que",
            "se",
            "ou",
            "mas",
            "the",
            "and",
            "or",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
        }
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]
        return list(set(keywords))

    def _calculate_similarity(self, query: str, technique: Dict) -> float:
        """Calcula similaridade baseada em palavras-chave"""
        query_keywords = self._extract_keywords(query)
        technique_keywords = technique.get("keywords", [])

        if not query_keywords:
            return 0.0

        if not technique_keywords:
            return 0.0

        common_words = set(query_keywords) & set(technique_keywords)
        base_similarity = len(common_words) / max(
            len(query_keywords), len(technique_keywords)
        )

        technique_name_words = self._extract_keywords(technique["technique_name"])
        name_matches = set(query_keywords) & set(technique_name_words)
        name_bonus = 0.0
        if name_matches:
            name_bonus = 0.3 * len(name_matches) / max(len(technique_name_words), 1)

        tactic_words = self._extract_keywords(technique.get("tactic", ""))
        tactic_matches = set(query_keywords) & set(tactic_words)
        tactic_bonus = 0.0
        if tactic_matches:
            tactic_bonus = 0.2 * len(tactic_matches) / max(len(tactic_words), 1)

        total_similarity = base_similarity + name_bonus + tactic_bonus

        return min(total_similarity, 1.0)

    def search_techniques(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Busca técnicas usando correspondência de palavras-chave"""
        try:
            if not self.techniques:
                logger.warning("Nenhuma técnica carregada para busca")
                return []

            scored_techniques = []

            for technique in self.techniques:
                similarity = self._calculate_similarity(query, technique)
                scored_techniques.append((technique, similarity))

            scored_techniques.sort(key=lambda x: x[1], reverse=True)

            results = []
            for technique, score in scored_techniques[:top_k]:
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

            logger.info(f"Encontradas {len(results)} técnicas para query: {query[:50]}")
            return results

        except Exception as e:
            logger.error(f"Erro ao buscar técnicas: {e}")
            return []

    async def classify_narrative(self, narrative: str, top_k: int = 5) -> Dict:
        """Classifica narrativa usando busca por palavras-chave"""
        start_time = time.time()

        try:
            search_results = self.search_techniques(narrative, top_k=top_k)

            techniques = []
            below_threshold = False

            for result in search_results:
                if result.similarity_score >= 0.15:
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

            if not techniques and search_results:
                below_threshold = True
                for result in search_results:
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
                logger.warning(
                    f"Nenhuma técnica acima do threshold (0.15). Retornando {len(techniques)} técnicas com maior similaridade"
                )

            processing_time = time.time() - start_time

            return {
                "narrative": narrative,
                "techniques": techniques,
                "processing_time": processing_time,
                "below_threshold": below_threshold,
            }

        except Exception as e:
            logger.error(f"Erro classificando narrativa: {e}")
            raise

    def is_loaded(self) -> bool:
        return self.loaded

    def get_techniques_count(self) -> int:
        return len(self.techniques)
