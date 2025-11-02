from pydantic import BaseModel, Field
from typing import List, Optional

class HealthResponse(BaseModel):
    status: str
    rag_loaded: bool
    techniques_count: int
    llm_available: bool = False
    llm_model: Optional[str] = None

class ClassificationRequest(BaseModel):
    narrative: str = Field(..., description="Narrativa de segurança a ser classificada")
    top_k: int = Field(5, ge=1, le=20, description="Numero de técnicas MITRE a retornar")
    use_llm: bool = Field(False, description="Gerar resposta amigável ao humano usando LLM")
    language: str = Field("pt-br", description="Idioma da resposta (pt-br ou en)")

class TechniqueMatch(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    description: str
    similarity_score: float
    activity_description: Optional[str] = None
    correction: Optional[str] = None

class ClassificationResponse(BaseModel):
    narrative: str
    techniques: List[TechniqueMatch]
    processing_time: float
    human_response: Optional[str] = None
    llm_metadata: Optional[dict] = None

class SearchRequest(BaseModel):
    query: str = Field(..., description="Query de busca para técnicas MITRE")
    top_k: int = Field(10, ge=1, le=50, description="Numero de técnicas MITRE a retornar")

class SearchResult(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    description: str
    similarity_score: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]

class MITRETechnique(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    description: str
