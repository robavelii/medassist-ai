import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.clinical_models import (
    BaseInput,
    DiagnosisInput,
    EmergencyTriageInput,
    MedicationInput,
    MedicationLabs,
    TriageColdCaseInput,
    Vitals,
)
from src.services.clinical_assistant_service import ClinicalAssistantService


@pytest.fixture
def mock_llm_cache_service():
    service = MagicMock()
    service.get_llm_response = AsyncMock()
    service._cache_response = AsyncMock()
    service.get_latest_cached_response_by_patient_and_model = MagicMock(return_value=None)
    service.get_cached_responses_by_patient_id_and_model = MagicMock(return_value=[])
    service.get_cached_responses_by_patient_id = MagicMock(return_value=[])
    return service


@pytest.fixture
def clinical_service(mock_llm_cache_service):
    return ClinicalAssistantService(llm_cache_service=mock_llm_cache_service)


@pytest.fixture
def sample_patient_info():
    return BaseInput(patient_id="test-patient-001", gender="male", age=35)


@pytest.fixture
def sample_vitals():
    return Vitals(
        systolic_bp="120",
        diastolic_bp="80",
        pulse_rate="72",
        respiratory_rate="16",
        temperature="36.8",
        spo2="98",
        weight="75",
        height="175",
    )


class TestClinicalAssistantServiceCachedResponses:
    """Tests for cached response retrieval."""

    @pytest.mark.asyncio
    async def test_get_cached_response_returns_none_when_no_cache(self, clinical_service):
        result = await clinical_service._get_cached_response_for_prompt(
            "test-patient-001", "triage_cold_cases", MagicMock
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_response_handles_json_decode_error(self, clinical_service, mock_llm_cache_service):
        mock_entry = MagicMock()
        mock_entry.response = "invalid-json"
        mock_entry.patient_id = "test-patient-001"
        mock_entry.visit_id = "test-visit-001"
        mock_llm_cache_service.get_latest_cached_response_by_patient_and_model.return_value = mock_entry

        result = await clinical_service._get_cached_response_for_prompt(
            "test-patient-001", "triage_cold_cases", MagicMock
        )
        assert result is None


class TestClinicalAssistantServiceLLMResponses:
    """Tests for LLM response processing."""

    @pytest.mark.asyncio
    async def test_triage_cold_cases_calls_llm(self, clinical_service, mock_llm_cache_service, sample_vitals):
        mock_response = json.dumps(
            {
                "response": {
                    "vital_classifications": {
                        "systolic_bp": "Normal (120 mmHg)",
                        "diastolic_bp": "Normal (80 mmHg)",
                        "pulse_rate": "Normal (72 bpm)",
                        "temperature": "Normal (36.8 C)",
                    },
                    "nutritional_status": "Normal BMI",
                    "summary": "Patient presents with stable vitals.",
                    "triage_priority": "Non-Urgent",
                    "follow_up_questions": [],
                },
                "confidence_score": {"status": "high", "score_percentage": 92},
            }
        )
        mock_llm_cache_service.get_llm_response.return_value = (mock_response, 100, 200)

        input_data = TriageColdCaseInput(
            vitals=sample_vitals,
            patient_info=BaseInput(patient_id="test-patient-001", gender="male", age=35),
            chief_complaint="Mild headache for 2 days",
        )

        result = await clinical_service.triage_cold_cases(input_data)
        assert result is not None
        assert result.patient_id == "test-patient-001"
        assert result.triage_priority == "Non-Urgent"

    @pytest.mark.asyncio
    async def test_emergency_triage_calls_llm(self, clinical_service, mock_llm_cache_service, sample_vitals):
        mock_response = json.dumps(
            {
                "response": {
                    "vital_classifications": {
                        "systolic_bp": "Normal",
                        "diastolic_bp": "Normal",
                        "pulse_rate": "Normal",
                        "temperature": "Normal",
                    },
                    "triage_code": "Green",
                    "rationale": "Stable vitals, non-urgent presentation.",
                    "immediate_actions": ["Monitor vitals"],
                    "follow_up_questions": [],
                },
                "confidence_score": {"status": "high", "score_percentage": 88},
            }
        )
        mock_llm_cache_service.get_llm_response.return_value = (mock_response, 100, 200)

        input_data = EmergencyTriageInput(
            vitals=sample_vitals,
            patient_info=BaseInput(patient_id="test-patient-001", gender="male", age=35),
            chief_complaint="Minor laceration on right hand",
        )

        result = await clinical_service.emergency_triage(input_data)
        assert result is not None
        assert result.triage_code == "Green"


class TestCostEstimation:
    """Tests for cost estimation functionality."""

    @pytest.mark.asyncio
    async def test_estimate_costs_default_estimates(self, clinical_service):
        from src.models.clinical_models import CostEstimationInput

        input_data = CostEstimationInput(num_patients=1)
        result = await clinical_service.estimate_costs(input_data)

        assert result is not None
        assert result.num_patients == 1
        assert len(result.endpoint_estimates) == 10
        assert result.total_estimated_input_tokens > 0
        assert result.total_estimated_output_tokens > 0
        assert "gpt-4o" in result.total_costs_by_model

    @pytest.mark.asyncio
    async def test_estimate_costs_scales_with_patients(self, clinical_service):
        from src.models.clinical_models import CostEstimationInput

        input_1 = CostEstimationInput(num_patients=1)
        input_5 = CostEstimationInput(num_patients=5)

        result_1 = await clinical_service.estimate_costs(input_1)
        result_5 = await clinical_service.estimate_costs(input_5)

        assert result_5.total_estimated_input_tokens == result_1.total_estimated_input_tokens * 5
