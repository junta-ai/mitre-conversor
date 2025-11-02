import logging
import json
import time
from typing import List, Dict, Optional
import requests

from api.models.schemas import TechniqueMatch

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3.2:1b",
        temperature: float = 0.7,
    ):
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self.api_url = f"{base_url}/api/generate"

        logger.info(f"Iniciando LLMService com modelo: {model_name}")

        self._test_connection()

    def _test_connection(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()

            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            if self.model_name not in model_names:
                logger.warning(
                    f"Modelo {self.model_name} não encontrado. Modelos disponíveis: {model_names}"
                )
                logger.warning("Execute: ollama pull llama3.2:3b")
            else:
                logger.info(
                    f"Conexão bem-sucedida com Ollama - Modelo {self.model_name} está disponível"
                )

            return True

        except Exception as e:
            logger.error(f"Erro ao conectar ao Ollama: {e}")
            logger.error("Certifique-se de que o Ollama está em execução: ollama serve")
            return False

    def _create_prompt(
        self, narrative: str, techniques: List[TechniqueMatch], language: str = "pt-br"
    ) -> str:
        if language == "pt-br":
            prompt = f"""Você é um analista de segurança cibernética especializado no framework MITRE ATT&CK.

Analise o seguinte cenário de segurança e forneça uma resposta clara e profissional baseada nas técnicas MITRE identificadas.

**Cenário:**
{narrative}

**Técnicas MITRE Identificadas:**
"""
            for i, tech in enumerate(techniques, 1):
                prompt += f"\n{i}. **{tech.technique_id} - {tech.technique_name}**"
                prompt += f"\n   - Tática: {tech.tactic}"
                prompt += f"\n   - Confiança: {tech.similarity_score:.1%}"
                if tech.description:

                    desc = (
                        tech.description[:200] + "..."
                        if len(tech.description) > 200
                        else tech.description
                    )
                    prompt += f"\n   - Descrição: {desc}"

            prompt += """

**Sua tarefa:**
Forneça uma análise profissional e compreensível deste incidente de segurança, incluindo:

1. **Resumo Executivo:** Explique brevemente o que está acontecendo em linguagem acessível
2. **Análise das Técnicas:** Descreva como cada técnica MITRE se relaciona com o cenário
3. **Impacto:** Explique os riscos e possíveis consequências
4. **Recomendações:** Sugira medidas de mitigação ou resposta

Mantenha um tom profissional, claro e acessível. Evite jargões excessivos, mas seja tecnicamente preciso.
"""
        else:
            prompt = f"""You are a cybersecurity analyst specialized in the MITRE ATT&CK framework.

Analyze the following security scenario and provide a clear, professional response based on the identified MITRE techniques.

**Scenario:**
{narrative}

**Identified MITRE Techniques:**
"""
            for i, tech in enumerate(techniques, 1):
                prompt += f"\n{i}. **{tech.technique_id} - {tech.technique_name}**"
                prompt += f"\n   - Tactic: {tech.tactic}"
                prompt += f"\n   - Confidence: {tech.similarity_score:.1%}"
                if tech.description:
                    desc = (
                        tech.description[:200] + "..."
                        if len(tech.description) > 200
                        else tech.description
                    )
                    prompt += f"\n   - Description: {desc}"

            prompt += """

**Your task:**
Provide a professional and understandable analysis of this security incident, including:

1. **Executive Summary:** Briefly explain what's happening in accessible language
2. **Technique Analysis:** Describe how each MITRE technique relates to the scenario
3. **Impact:** Explain the risks and potential consequences
4. **Recommendations:** Suggest mitigation or response measures

Maintain a professional, clear, and accessible tone. Avoid excessive jargon, but be technically accurate.
"""

        return prompt

    def generate_response(
        self,
        narrative: str,
        techniques: List[TechniqueMatch],
        language: str = "pt-br",
        stream: bool = False,
    ) -> Dict:
        start_time = time.time()

        try:

            prompt = self._create_prompt(narrative, techniques, language)

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "stream": stream,
            }

            logger.info(f"Gerando resposta LLM com modelo: {self.model_name}")
            response = requests.post(self.api_url, json=payload, timeout=300)
            response.raise_for_status()

            if stream:

                full_response = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            full_response += data["response"]
                result = full_response
            else:

                result = response.json()["response"]

            generation_time = time.time() - start_time

            logger.info(f"Resposta LLM gerada em {generation_time:.2f}s")

            return {
                "response": result.strip(),
                "generation_time": generation_time,
                "model": self.model_name,
                "language": language,
            }

        except requests.exceptions.ConnectionError:
            logger.error(
                "Não é possível conectar ao Ollama. Certifique-se de que está em execução: ollama serve"
            )
            raise Exception(
                "O serviço Ollama não está disponível. Certifique-se de que o Ollama está em execução."
            )
        except requests.exceptions.Timeout:
            logger.error("Geração de LLM excedeu o tempo limite")
            raise Exception(
                "A geração de LLM demorou muito. Por favor, tente novamente."
            )
        except Exception as e:
            logger.error(f"Erro gerando resposta da LLM : {e}")
            raise Exception(f"Falha ao gerar resposta LLM: {str(e)}")

    async def generate_response_async(
        self, narrative: str, techniques: List[TechniqueMatch], language: str = "pt-br"
    ) -> Dict:
        return self.generate_response(narrative, techniques, language)

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
