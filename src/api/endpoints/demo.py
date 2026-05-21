from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.core.container import Container
from src.models.clinical_models import BaseInput, EmergencyTriageInput, Vitals
from src.services.clinical_assistant_service import ClinicalAssistantService

router = APIRouter(prefix="/demo", tags=["demo"])


SAMPLE_PATIENT = BaseInput(
    patient_id="demo-patient-001",
    gender="female",
    age=45,
    patient_location="New York, USA",
)

SAMPLE_VITALS = Vitals(
    systolic_bp="145",
    diastolic_bp="92",
    pulse_rate="88",
    respiratory_rate="18",
    temperature="37.2",
    spo2="97",
    weight="72",
    height="165",
)


@router.get("/capabilities")
async def list_capabilities():
    """
    List all clinical modules available in the platform.

    Returns a summary of each module with its endpoint and description.
    """
    return {
        "platform": "MedAssist AI",
        "version": "1.0.0",
        "modules": [
            {
                "name": "Triage - Cold Cases",
                "endpoint": "POST /api/v1/clinical/triage-cold-cases",
                "description": "Analyze patient vitals and chief complaint to determine triage priority for non-emergency cases.",
            },
            {
                "name": "Emergency Triage",
                "endpoint": "POST /api/v1/clinical/emergency-triage",
                "description": "Rapid emergency assessment with color-coded triage and immediate stabilization recommendations.",
            },
            {
                "name": "Outpatient H&PE",
                "endpoint": "POST /api/v1/clinical/outpatient-hpe",
                "description": "Analyze outpatient history and physical exam findings to generate differential diagnoses.",
            },
            {
                "name": "Lab Interpretation",
                "endpoint": "POST /api/v1/clinical/lab-interpretation",
                "description": "Interpret lab results, identify abnormal findings, and suggest critical actions.",
            },
            {
                "name": "Radiology Interpretation",
                "endpoint": "POST /api/v1/clinical/radiology-interpretation",
                "description": "Interpret radiology images within clinical context and suggest next steps.",
            },
            {
                "name": "Diagnosis",
                "endpoint": "POST /api/v1/clinical/diagnosis",
                "description": "Synthesize all clinical data to suggest ranked differential diagnoses.",
            },
            {
                "name": "Medication Management",
                "endpoint": "POST /api/v1/clinical/medication",
                "description": "Suggest medications with safety checks, drug interactions, and dose adjustments.",
            },
            {
                "name": "Inpatient Monitoring",
                "endpoint": "POST /api/v1/clinical/inpatient",
                "description": "Provide ongoing guidance and updates for admitted patients.",
            },
            {
                "name": "Visit Summary",
                "endpoint": "POST /api/v1/clinical/visit-summary",
                "description": "Generate comprehensive visit summaries with prior visit correlation.",
            },
            {
                "name": "Patient Education",
                "endpoint": "POST /api/v1/clinical/patient-education",
                "description": "Generate patient-friendly education materials about conditions and treatments.",
            },
            {
                "name": "Clinical Chat",
                "endpoint": "POST /api/v1/clinical/chat",
                "description": "Context-aware clinical conversation with full medical history integration.",
            },
            {
                "name": "Cost Estimation",
                "endpoint": "POST /api/v1/clinical/cost-estimation",
                "description": "Estimate token usage and API costs across all clinical modules.",
            },
        ],
    }


@router.get("/sample-request")
async def get_sample_request():
    """
    Return a sample emergency triage request payload for testing.

    Use this payload as a template when calling POST /api/v1/clinical/emergency-triage.
    """
    sample_input = EmergencyTriageInput(
        vitals=SAMPLE_VITALS,
        patient_info=SAMPLE_PATIENT,
        chief_complaint="Severe chest pain radiating to left arm, onset 30 minutes ago, associated with diaphoresis and shortness of breath.",
    )
    return {
        "description": "Sample emergency triage request for a 45-year-old female with chest pain",
        "target_endpoint": "POST /api/v1/clinical/emergency-triage",
        "request_body": sample_input.model_dump(mode="json"),
    }
