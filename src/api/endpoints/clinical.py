import uuid
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.endpoints.auth import validate_api_key
from src.core.container import Container
from src.models.clinical_models import (
    ChatHistoryOutput,
    ChatInput,
    ChatResponseOutput,
    CostEstimationInput,
    CostEstimationOutput,
    DiagnosisInput,
    DiagnosisOutput,
    EmergencyTriageInput,
    EmergencyTriageOutput,
    FollowBackQuestionOutput,
    InpatientInput,
    InpatientOutput,
    LabResultInterpretationInput,
    LabResultInterpretationOutput,
    MedicationInput,
    MedicationOutput,
    OutpatientHPEInput,
    OutpatientHPEOutput,
    Patient,
    PatientEducationInput,
    PatientEducationOutput,
    RadiologyImageInterpretationInput,
    RadiologyImageInterpretationOutput,
    TriageColdCaseInput,
    TriageColdCaseOutput,
    VisitInfo,
    VisitSummaryInput,
    VisitSummaryOutput,
)
from src.services.clinical_assistant_service import ClinicalAssistantService

router = APIRouter(
    prefix="/clinical", tags=["clinical"], dependencies=[Depends(validate_api_key)]
)


# --- Triage Cold Cases ---


@router.get(
    "/triage-cold-cases/{patient_id}", response_model=Optional[TriageColdCaseOutput]
)
@inject
async def get_triage_cold_cases_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached triage cold cases data for a patient."""
    response = await service._get_cached_response_for_prompt(
        patient_id, "triage_cold_cases", TriageColdCaseOutput
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached triage cold cases data found for patient_id: {patient_id}",
        )
    return response


@router.post("/triage-cold-cases", response_model=Optional[TriageColdCaseOutput])
@inject
async def triage_cold_cases(
    input_data: TriageColdCaseInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Analyze cold case triage based on vitals, patient info, and chief complaint."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.triage_cold_cases(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for triage cold cases.",
        )
    return response


# --- Emergency Triage ---


@router.get(
    "/emergency-triage/{patient_id}", response_model=Optional[EmergencyTriageOutput]
)
@inject
async def get_emergency_triage_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached emergency triage data for a patient."""
    response = await service._get_cached_response_for_prompt(
        patient_id, "emergency_triage", EmergencyTriageOutput
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached emergency triage data found for patient_id: {patient_id}",
        )
    return response


@router.post("/emergency-triage", response_model=Optional[EmergencyTriageOutput])
@inject
async def emergency_triage(
    input_data: EmergencyTriageInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Perform emergency triage assessment with color-coded priority."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.emergency_triage(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for emergency triage.",
        )
    return response


# --- Outpatient History & Physical Exam ---


@router.get(
    "/outpatient-hpe/{patient_id}", response_model=Optional[OutpatientHPEOutput]
)
@inject
async def get_outpatient_hpe_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached outpatient history and physical exam data."""
    response = await service._get_cached_response_for_prompt(
        patient_id, "outpatient_history_physical_exam", OutpatientHPEOutput
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached outpatient HPE data found for patient_id: {patient_id}",
        )
    return response


@router.post("/outpatient-hpe", response_model=Optional[OutpatientHPEOutput])
@inject
async def outpatient_history_physical_exam(
    input_data: OutpatientHPEInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Analyze outpatient history and physical examination findings."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.outpatient_history_physical_exam(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for outpatient HPE.",
        )
    return response


# --- Lab Result Interpretation ---


@router.get(
    "/lab-interpretation/{patient_id}",
    response_model=Optional[LabResultInterpretationOutput],
)
@inject
async def get_lab_interpretation_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached lab result interpretation data."""
    response = await service._get_cached_response_for_prompt(
        patient_id,
        "outpatient_lab_result_interpretation",
        LabResultInterpretationOutput,
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached lab interpretation data found for patient_id: {patient_id}",
        )
    return response


@router.post(
    "/lab-interpretation", response_model=Optional[LabResultInterpretationOutput]
)
@inject
async def lab_result_interpretation(
    input_data: LabResultInterpretationInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Interpret lab results and identify abnormal findings."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.outpatient_lab_result_interpretation(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for lab interpretation.",
        )
    return response


# --- Radiology Image Interpretation ---


@router.get(
    "/radiology-interpretation/{patient_id}",
    response_model=Optional[RadiologyImageInterpretationOutput],
)
@inject
async def get_radiology_interpretation_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached radiology image interpretation data."""
    response = await service._get_cached_response_for_prompt(
        patient_id, "radiology_image_interpretation", RadiologyImageInterpretationOutput
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached radiology interpretation data found for patient_id: {patient_id}",
        )
    return response


@router.post(
    "/radiology-interpretation",
    response_model=Optional[RadiologyImageInterpretationOutput],
)
@inject
async def radiology_image_interpretation(
    input_data: RadiologyImageInterpretationInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Interpret radiology images within clinical context."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.radiology_image_interpretation(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for radiology interpretation.",
        )
    return response


# --- Diagnosis ---


@router.get("/diagnosis/{patient_id}", response_model=Optional[DiagnosisOutput])
@inject
async def get_diagnosis_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached diagnosis data for a patient."""
    response = await service._get_cached_response_for_prompt(
        patient_id, "diagnosis", DiagnosisOutput
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached diagnosis data found for patient_id: {patient_id}",
        )
    return response


@router.post("/diagnosis", response_model=Optional[DiagnosisOutput])
@inject
async def diagnosis(
    input_data: DiagnosisInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Synthesize clinical data to suggest ranked diagnoses."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.diagnosis(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for diagnosis.",
        )
    return response


# --- Medication ---


@router.get("/medication/{patient_id}", response_model=Optional[MedicationOutput])
@inject
async def get_medication_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached medication data for a patient."""
    response = await service._get_cached_response_for_prompt(
        patient_id, "medication", MedicationOutput
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached medication data found for patient_id: {patient_id}",
        )
    return response


@router.post("/medication", response_model=Optional[MedicationOutput])
@inject
async def medication(
    input_data: MedicationInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Suggest medications with safety checks and dose adjustments."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.medication(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for medication.",
        )
    return response


# --- Inpatient Admitted Patients ---


@router.get("/inpatient/{patient_id}", response_model=Optional[InpatientOutput])
@inject
async def get_inpatient_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached inpatient monitoring data."""
    response = await service._get_cached_response_for_prompt(
        patient_id, "inpatient_admitted_patients", InpatientOutput
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached inpatient data found for patient_id: {patient_id}",
        )
    return response


@router.post("/inpatient", response_model=Optional[InpatientOutput])
@inject
async def inpatient_admitted_patients(
    input_data: InpatientInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Provide ongoing guidance for admitted inpatient care."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.inpatient_admitted_patients(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for inpatient monitoring.",
        )
    return response


# --- Visit Summary ---


@router.get("/visit-summary/{patient_id}", response_model=Optional[VisitSummaryOutput])
@inject
async def get_visit_summary_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached visit summary data."""
    response = await service._get_cached_response_for_prompt(
        patient_id, "visit_summary", VisitSummaryOutput
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached visit summary data found for patient_id: {patient_id}",
        )
    return response


@router.post("/visit-summary", response_model=Optional[VisitSummaryOutput])
@inject
async def visit_summary(
    input_data: VisitSummaryInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Generate a comprehensive visit summary with prior visit correlation."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.visit_summary(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for visit summary.",
        )
    return response


# --- Patient Education ---


@router.get(
    "/patient-education/{patient_id}", response_model=Optional[PatientEducationOutput]
)
@inject
async def get_patient_education_cached(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch cached patient education data."""
    response = await service._get_cached_response_for_prompt(
        patient_id, "patient_education", PatientEducationOutput
    )
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached patient education data found for patient_id: {patient_id}",
        )
    return response


@router.post("/patient-education", response_model=Optional[PatientEducationOutput])
@inject
async def patient_education(
    input_data: PatientEducationInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Generate patient-friendly education materials."""
    if not input_data.visit_info or not input_data.visit_info.visit_id:
        input_data.visit_info = VisitInfo(visit_id=str(uuid.uuid4()))
    response = await service.patient_education(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get response for patient education.",
        )
    return response


# --- Cost Estimation ---


@router.post("/cost-estimation", response_model=CostEstimationOutput)
@inject
async def cost_estimation(
    input_data: CostEstimationInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
    patient: Optional[Patient] = None,
):
    """
    Estimate token usage and costs for all clinical endpoints.

    Calculates per-endpoint and total costs across different models.
    Optionally provide sample data for more accurate token estimates.
    """
    try:
        response = await service.estimate_costs(input_data, patient)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate cost estimation: {str(e)}",
        )


# --- Chat ---


@router.get("/chat-history/{patient_id}", response_model=Optional[ChatHistoryOutput])
@inject
async def get_chat_history(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch chat history for a patient."""
    response = await service.get_chat_history(patient_id)
    if not response.history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chat history found for patient_id: {patient_id}",
        )
    return response


@router.get(
    "/follow-back-questions/{patient_id}",
    response_model=Optional[FollowBackQuestionOutput],
)
@inject
async def get_follow_back_questions(
    patient_id: str,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Fetch follow-back questions for a patient."""
    response = await service.get_follow_back_questions(patient_id)
    if not response.questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No follow-back questions found for patient_id: {patient_id}",
        )
    return response


@router.post("/chat", response_model=ChatResponseOutput)
@inject
async def chat(
    input_data: ChatInput,
    service: ClinicalAssistantService = Depends(
        Provide[Container.clinical_assistant_service]
    ),
):
    """Send a chat message and receive a context-aware clinical response."""
    response = await service.handle_chat_message(input_data)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get a response for the chat message.",
        )
    return response
