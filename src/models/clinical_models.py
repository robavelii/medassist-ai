from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Gender(str, Enum):
    male = "male"
    female = "female"


class BaseInput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    gender: Gender
    age: int
    patient_location: Optional[str] = Field(
        None, description="Patient location for region-specific clinical guidance"
    )


class VisitInfo(BaseModel):
    visit_id: str = Field(..., description="Unique identifier for the visit")


class ConfidenceScore(BaseModel):
    status: str = Field(..., description="Confidence status (e.g., 'low', 'medium', 'high')")
    score_percentage: Optional[float] = Field(
        None, ge=0, le=100, description="Confidence score as a percentage (0-100)"
    )


# Common Vitals Model
class Vitals(BaseModel):
    systolic_bp: Optional[str] = Field(None, description="Systolic blood pressure in mmHg")
    diastolic_bp: Optional[str] = Field(None, description="Diastolic blood pressure in mmHg")
    pulse_rate: Optional[str] = Field(None, description="Pulse rate in bpm")
    respiratory_rate: Optional[str] = Field(None, description="Respiratory rate in breaths/min")
    temperature: Optional[str] = Field(None, description="Temperature in Celsius")
    spo2: Optional[str] = Field(None, description="Oxygen saturation in %")
    weight: Optional[str] = Field(None, description="Weight in kg")
    height: Optional[str] = Field(None, description="Height in cm")


class TriageColdCaseInput(BaseModel):
    vitals: Optional[Vitals] = None
    patient_info: Optional[BaseInput] = None
    visit_info: Optional[VisitInfo] = None
    chief_complaint: str


class VitalClassifications(BaseModel):
    systolic_bp: Optional[str] = None
    diastolic_bp: Optional[str] = None
    pulse_rate: Optional[str] = None
    temperature: Optional[str] = None


class TriageColdCaseOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    vital_classifications: VitalClassifications
    nutritional_status: Optional[str] = None
    summary: Optional[str] = None
    triage_priority: Optional[str] = None
    confidence_score: ConfidenceScore
    follow_up_questions: Optional[List[str]] = Field(
        None,
        description="Follow-up questions to address low confidence or incomplete data.",
    )


# Emergency Triage
class EmergencyTriageInput(BaseModel):
    vitals: Optional[Vitals] = None
    patient_info: Optional[BaseInput] = None
    visit_info: Optional[VisitInfo] = None
    chief_complaint: str


class EmergencyTriageOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    vital_classifications: VitalClassifications
    triage_code: Optional[str] = None
    rationale: Optional[str] = None
    immediate_actions: Optional[List[str]] = None
    confidence_score: ConfidenceScore
    follow_up_questions: Optional[List[str]] = Field(
        None,
        description="Follow-up questions to address low confidence or incomplete data.",
    )


# Outpatient (History & Physical Exam)
class OutpatientHPEInput(BaseModel):
    history_form: str
    physical_exam: str
    vitals: Optional[Vitals] = None
    patient_info: Optional[BaseInput] = None
    visit_info: Optional[VisitInfo] = None


class DifferentialItem(BaseModel):
    diagnosis: str
    support: List[str]
    against: List[str]
    confirmation: List[str]


class OutpatientHPEOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    summary: Optional[str] = None
    follow_up_questions: Optional[List[str]] = None
    differentials: Optional[List[DifferentialItem]] = None
    recommended_tests: Optional[List[str]] = None
    confidence_score: ConfidenceScore


# Outpatient (Lab Result Interpretation)
class LabResultInterpretationInput(BaseModel):
    lab_results: str
    history: str
    vitals: Optional[Vitals] = None
    patient_info: BaseInput
    visit_info: Optional[VisitInfo] = None


class AbnormalResultItem(BaseModel):
    test_name: str
    result: str
    interpretation: str


class LabResultInterpretationOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    abnormal_results: Optional[List[AbnormalResultItem]] = None
    critical_actions: Optional[List[str]] = None
    additional_tests: Optional[List[str]] = None
    confidence_score: ConfidenceScore


# Radiology Image Interpretation
class RadiologyContext(BaseModel):
    history: str
    vitals: Optional[Vitals] = None


class RadiologyImageInterpretationInput(BaseModel):
    image_reference: str
    context: RadiologyContext
    patient_info: BaseInput
    visit_info: Optional[VisitInfo] = None


class RadiologyImageInterpretationOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    findings: Optional[str] = None
    correlation: Optional[str] = None
    next_steps: Optional[List[str]] = None
    confidence_score: ConfidenceScore


# Diagnosis
class DiagnosisInput(BaseModel):
    vitals: Optional[Vitals] = None
    history: str
    exam: str
    labs: str
    radiology: str
    patient_info: BaseInput
    visit_info: Optional[VisitInfo] = None


class ConditionSupport(BaseModel):
    condition: str
    support: List[str]


class DiagnosisOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    diagnoses: Optional[List[ConditionSupport]] = None
    confidence_score: ConfidenceScore
    follow_up_questions: Optional[List[str]] = Field(
        None,
        description="Follow-up questions to address low confidence or incomplete data.",
    )


# Medication
class MedicationLabs(BaseModel):
    Creatinine: Optional[str] = None


class MedicationInput(BaseModel):
    diagnosis: str
    allergies: List[str]
    vitals: Optional[Vitals] = None
    weight: float
    labs: MedicationLabs
    current_medicalist: List[str]
    patient_info: BaseInput
    visit_info: Optional[VisitInfo] = None


class RecommendedDrug(BaseModel):
    name: str
    dose: str
    rationale: str


class MedicationOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    recommended_drugs: Optional[List[RecommendedDrug]] = None
    safety_flags: Optional[List[str]] = None
    dose_adjustments: Optional[List[str]] = None
    confidence_score: ConfidenceScore
    follow_up_questions: Optional[List[str]] = Field(
        None,
        description="Follow-up questions to address low confidence or incomplete data.",
    )


# Inpatient (Admitted Patients)
class InpatientInput(BaseModel):
    ward: str
    vitals: Optional[Vitals] = None
    labs: str
    progress_notes: str
    current_meds: List[str]
    patient_info: BaseInput
    visit_info: Optional[VisitInfo] = None


class InpatientOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    ongoing_updates: Optional[List[str]] = None
    confidence_score: ConfidenceScore
    follow_up_questions: Optional[List[str]] = Field(
        None,
        description="Follow-up questions to address low confidence or incomplete data.",
    )


# Visit Summary
class VisitSummaryInput(BaseModel):
    triage_data: str
    exam: str
    labs: str
    diagnosis: str
    medications: List[str]
    previous_visits: str
    patient_info: BaseInput
    visit_info: Optional[VisitInfo] = None


class VisitSummaryOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    visit_summary: Optional[str] = None
    key_findings: Optional[str] = None
    relation_to_prior: Optional[str] = None
    confidence_score: ConfidenceScore
    follow_up_questions: Optional[List[str]] = Field(
        None,
        description="Follow-up questions to address low confidence or incomplete data.",
    )


# Patient Education
class PatientEducationInput(BaseModel):
    diagnosis: str
    labs: str
    medications: List[str]
    patient_info: BaseInput
    visit_info: Optional[VisitInfo] = None


class PatientEducationOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    visit_id: str = Field(..., description="Unique identifier for the visit")
    explanation: Optional[str] = None
    medication_advice: Optional[str] = None
    lifestyle: Optional[str] = None
    confidence_score: ConfidenceScore
    follow_up_questions: Optional[List[str]] = Field(
        None,
        description="Follow-up questions to address low confidence or incomplete data.",
    )


# Cost Estimation
class EndpointCostEstimate(BaseModel):
    endpoint_name: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    costs_by_model: Dict[str, float] = Field(..., description="Estimated cost for each model")


class CostEstimationInput(BaseModel):
    """Input for cost estimation across all clinical endpoints."""

    num_patients: int = Field(1, ge=1, description="Number of patients for cost estimation")
    triage_cold_case_sample: Optional[TriageColdCaseInput] = None
    emergency_triage_sample: Optional[EmergencyTriageInput] = None
    outpatient_hpe_sample: Optional[OutpatientHPEInput] = None
    lab_result_interpretation_sample: Optional[LabResultInterpretationInput] = None
    radiology_interpretation_sample: Optional[RadiologyImageInterpretationInput] = None
    diagnosis_sample: Optional[DiagnosisInput] = None
    medication_sample: Optional[MedicationInput] = None
    inpatient_sample: Optional[InpatientInput] = None
    visit_summary_sample: Optional[VisitSummaryInput] = None
    patient_education_sample: Optional[PatientEducationInput] = None


class CostEstimationOutput(BaseModel):
    num_patients: int = Field(..., description="Number of patients used for the estimation")
    endpoint_estimates: List[EndpointCostEstimate]
    total_estimated_input_tokens: int
    total_estimated_output_tokens: int
    total_costs_by_model: Dict[str, float] = Field(
        ..., description="Total estimated cost for each model across all endpoints"
    )


class Patient(BaseModel):
    patient: int


# Chat Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (e.g., 'user', 'assistant')")
    content: str = Field(..., description="Content of the chat message")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the message was created or cached")


class ChatHistoryOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    history: List[ChatMessage] = Field(..., description="List of chat messages for the patient")


class FollowBackQuestionOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    questions: List[str] = Field(..., description="List of follow-up questions for the patient")


class ChatInput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    message: str = Field(..., description="The chat message from the user")
    visit_id: Optional[str] = Field(None, description="Optional visit ID associated with the chat message")


class ChatResponseOutput(BaseModel):
    patient_id: str = Field(..., description="Unique identifier for the patient")
    response: str = Field(..., description="The response to the chat message")
    visit_id: Optional[str] = Field(None, description="Optional visit ID associated with the chat message")
