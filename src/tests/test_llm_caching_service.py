import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.llm_caching_service import LLMCacheService


@pytest.fixture
def mock_db_session():
    session = MagicMock()
    return session


@pytest.fixture
def llm_cache_service(mock_db_session):
    return LLMCacheService(db_session=mock_db_session)


class TestCacheKeyGeneration:
    def test_generate_cache_key_consistency(self, llm_cache_service):
        prompt = "test prompt"
        model = "gpt-4o"
        key1 = llm_cache_service._generate_cache_key(prompt, model)
        key2 = llm_cache_service._generate_cache_key(prompt, model)
        assert key1 == key2

    def test_generate_cache_key_uniqueness(self, llm_cache_service):
        key1 = llm_cache_service._generate_cache_key("prompt1", "gpt-4o")
        key2 = llm_cache_service._generate_cache_key("prompt2", "gpt-4o")
        assert key1 != key2

    def test_generate_cache_key_format(self, llm_cache_service):
        key = llm_cache_service._generate_cache_key("test", "gpt-4o")
        assert len(key) == 64  # SHA-256 hex digest length


class TestCostCalculation:
    def test_calculate_cost_known_model(self, llm_cache_service):
        cost = llm_cache_service._calculate_cost("gpt-4o", 1000, 500)
        assert cost["input_tokens"] == 1000
        assert cost["output_tokens"] == 500
        assert cost["total_cost"] > 0
        assert cost["input_cost"] == (1000 / 1_000) * 0.005
        assert cost["output_cost"] == (500 / 1_000) * 0.015

    def test_calculate_cost_unknown_model_uses_default(self, llm_cache_service):
        cost = llm_cache_service._calculate_cost("unknown-model", 1000, 500)
        # Should fall back to gpt-4o pricing
        assert cost["total_cost"] > 0

    def test_calculate_cost_zero_tokens(self, llm_cache_service):
        cost = llm_cache_service._calculate_cost("gpt-4o", 0, 0)
        assert cost["total_cost"] == 0.0


class TestCacheRetrieval:
    def test_get_cached_responses_returns_empty_on_error(
        self, llm_cache_service, mock_db_session
    ):
        mock_db_session.side_effect = Exception("DB error")
        result = llm_cache_service.get_cached_responses_by_patient_id("test-patient")
        assert result == []

    def test_get_latest_cached_response_returns_none_on_error(
        self, llm_cache_service, mock_db_session
    ):
        mock_db_session.side_effect = Exception("DB error")
        result = llm_cache_service.get_latest_cached_response_by_patient_and_model(
            "test-patient", "triage"
        )
        assert result is None
