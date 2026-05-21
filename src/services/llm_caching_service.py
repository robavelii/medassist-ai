import hashlib
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from openai import AsyncOpenAI

from src.core.config import configs
from src.models.llm_cache_model import LLMCache
from src.utils.llm_security import count_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


openai_client = AsyncOpenAI(api_key=configs.OPENAI_API_KEY)


class LLMCacheService:
    def __init__(self, db_session):
        self.db_session = db_session

    def _generate_cache_key(self, structured_prompt: str, model: str) -> str:
        """Generate a secure cache key using SHA-256."""
        content = f"{model}:{structured_prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Calculate the cost of an API request based on token usage."""
        pricing = configs.MODEL_PRICING.get(model)
        if not pricing:
            logger.warning(f"Unknown model pricing for {model}, using gpt-4o pricing from configs.")
            pricing = configs.MODEL_PRICING["gpt-4o"]

        input_cost = (input_tokens / 1_000) * pricing["input_cost_per_1k_tokens"]
        output_cost = (output_tokens / 1_000) * pricing["output_cost_per_1k_tokens"]

        total_cost = input_cost + output_cost

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "price_per_input_token": pricing["input_cost_per_1k_tokens"] / 1_000,
            "price_per_output_token": pricing["output_cost_per_1k_tokens"] / 1_000,
        }

    async def get_llm_response(
        self,
        structured_prompt: str,
        prompt_name: str,
        model: str = "gpt-4o",
        response_format=None,
        patient_id: Optional[str] = None,
        visit_id: Optional[str] = None,
    ) -> tuple[Optional[str], int, int]:
        """
        Get LLM response with caching and error handling.

        Args:
            structured_prompt: The prompt to send to the LLM
            prompt_name: Name of the prompt for cache categorization
            model: The model to use (default: gpt-4o)
            response_format: Optional response format specification
            patient_id: Optional patient ID for caching
            visit_id: Optional visit ID for caching

        Returns:
            Tuple of (response_string, input_tokens, output_tokens)
        """
        cache_key = self._generate_cache_key(structured_prompt, model)
        actual_input_tokens = 0
        output_tokens = 0

        # Check cache first
        try:
            with self.db_session() as session:
                query = session.query(LLMCache).filter(LLMCache.id == cache_key)
                if patient_id:
                    query = query.filter(LLMCache.patient_id == patient_id)
                if visit_id:
                    query = query.filter(LLMCache.visit_id == visit_id)
                cached_response = query.first()

                if cached_response:
                    logger.info(
                        f"CACHE HIT - Request: {cache_key[:12]} | "
                        f"Model: {model} | "
                        f"Input Tokens: {cached_response.input_tokens} | "
                        f"Output Tokens: {cached_response.output_tokens} | "
                        f"Cost: ${cached_response.total_cost:.6f} (saved API call)"
                    )
                    return (
                        cached_response.response,
                        cached_response.input_tokens,
                        cached_response.output_tokens,
                    )
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e} cache_key[:12]: {cache_key[:12]}")

        # Make OpenAI request
        try:
            input_tokens_estimate = count_tokens(structured_prompt)
            logger.info(
                f"Making OpenAI API request with model: {model}, estimated input tokens: {input_tokens_estimate}"
            )

            request_kwargs: Dict[str, Any] = {
                "model": model,
                "messages": [{"role": "user", "content": structured_prompt}],
                "temperature": 0,
            }

            if response_format is not None:
                request_kwargs["response_format"] = response_format

            response = await openai_client.chat.completions.create(**request_kwargs)

            if not response.choices or not response.choices[0].message.content:
                logger.error("Empty response from OpenAI API")
                return None, 0, 0

            response_content = response.choices[0].message.content

            if response.usage:
                actual_input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
            else:
                actual_input_tokens = input_tokens_estimate
                output_tokens = count_tokens(response_content)
                total_tokens = actual_input_tokens + output_tokens

            cost_info_for_logging = self._calculate_cost(model, actual_input_tokens, output_tokens)

            logger.info(
                f"API REQUEST COST - Model: {model} | "
                f"Input tokens: {actual_input_tokens} (${cost_info_for_logging['input_cost']:.6f}) | "
                f"Output tokens: {output_tokens} (${cost_info_for_logging['output_cost']:.6f}) | "
                f"Total tokens: {total_tokens} | "
                f"Total cost: ${cost_info_for_logging['total_cost']:.6f}"
            )

            # Cache the response
            cost_info_for_caching = self._calculate_cost(model, actual_input_tokens, output_tokens)
            await self._cache_response(
                cache_key,
                structured_prompt,
                response_content,
                prompt_name,
                actual_input_tokens,
                output_tokens,
                cost_info_for_caching["total_cost"],
                patient_id,
                visit_id,
            )

            return response_content, actual_input_tokens, output_tokens

        except Exception as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def _cache_response(
        self,
        cache_key: str,
        structured_prompt: str,
        response_content: str,
        prompt_name: str,
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        patient_id: Optional[str] = None,
        visit_id: Optional[str] = None,
    ) -> None:
        """Cache the LLM response with proper error handling."""
        try:
            with self.db_session() as session:
                cache_entry = LLMCache(
                    id=cache_key,
                    structured_prompt=structured_prompt,
                    response=response_content,
                    model_name=prompt_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_cost=total_cost,
                    patient_id=patient_id,
                    visit_id=visit_id,
                )
                session.add(cache_entry)
                session.commit()
                logger.info(f"Response cached successfully: {cache_key[:12]}")

        except Exception as e:
            logger.warning(f"Failed to cache response: {e} {cache_key[:12]}", exc_info=True)

    def get_cached_responses_by_patient_id(self, patient_id: str) -> List[LLMCache]:
        """Fetch all cached LLM responses for a given patient_id."""
        try:
            with self.db_session() as session:
                cached_responses = session.query(LLMCache).filter(LLMCache.patient_id == patient_id).all()
                logger.info(f"Fetched {len(cached_responses)} cached responses for patient_id: {patient_id}")
                return cached_responses
        except Exception as e:
            logger.error(f"Failed to fetch cached responses for patient_id {patient_id}: {e}", exc_info=True)
            return []

    def get_latest_cached_response_by_patient_and_model(self, patient_id: str, model_name: str) -> Optional[LLMCache]:
        """Fetch the latest cached LLM response for a given patient_id and model_name."""
        try:
            with self.db_session() as session:
                cached_response = (
                    session.query(LLMCache)
                    .filter(LLMCache.patient_id == patient_id, LLMCache.model_name == model_name)
                    .order_by(LLMCache.created_at.desc())
                    .first()
                )
                if cached_response:
                    logger.info(
                        f"Fetched latest cached response for patient_id: {patient_id}, model_name: {model_name}"
                    )
                else:
                    logger.info(f"No cached response found for patient_id: {patient_id}, model_name: {model_name}")
                return cached_response
        except Exception as e:
            logger.error(
                f"Failed to fetch latest cached response for patient_id {patient_id}, model_name {model_name}: {e}",
                exc_info=True,
            )
            return None

    def get_cached_responses_by_patient_id_and_model(self, patient_id: str, model_name: str) -> List[LLMCache]:
        """Fetch all cached LLM responses for a given patient_id and model_name."""
        try:
            with self.db_session() as session:
                cached_responses = (
                    session.query(LLMCache)
                    .filter(LLMCache.patient_id == patient_id, LLMCache.model_name == model_name)
                    .order_by(LLMCache.created_at)
                    .all()
                )
                logger.info(f"Fetched {len(cached_responses)} cached responses for patient_id: {patient_id}")
                return cached_responses
        except Exception as e:
            logger.error(
                f"Failed to fetch cached responses for patient_id {patient_id}, model_name {model_name}: {e}",
                exc_info=True,
            )
            return []
