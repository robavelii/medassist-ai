import json
import uuid
from typing import Any, Dict, List, Optional, Type

from fastapi import HTTPException
from loguru import logger

from src.core import config
from src.models.clinical_models import (
    ChatHistoryOutput,
    ChatInput,
    ChatMessage,
    ChatResponseOutput,
    CostEstimationInput,
    CostEstimationOutput,
    DiagnosisInput,
    DiagnosisOutput,
    EmergencyTriageInput,
    EmergencyTriageOutput,
    EndpointCostEstimate,
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
    VisitSummaryInput,
    VisitSummaryOutput,
)
from src.services.llm_caching_service import LLMCacheService
from src.utils.llm_security import (
    count_tokens,
    create_structured_prompt,
    log_security_event,
    sanitize_for_llm,
)


class ClinicalAssistantService:
    def __init__(self, llm_cache_service: LLMCacheService):
        self.llm_cache_service = llm_cache_service

    async def _get_cached_response_for_prompt(
        self,
        patient_id: str,
        prompt_name: str,
        output_model: Type[Any],
    ) -> Optional[Any]:
        """
        Fetches and parses the latest cached LLM response for a given patient_id and prompt_name.
        """
        cached_entry = (
            self.llm_cache_service.get_latest_cached_response_by_patient_and_model(
                patient_id=patient_id, model_name=prompt_name
            )
        )
        if not cached_entry:
            return None

        try:
            parsed_response = json.loads(cached_entry.response.strip())

            if output_model == ChatHistoryOutput:
                history_data = parsed_response.get("history", [])
                history = [ChatMessage(**msg_data) for msg_data in history_data]
                return ChatHistoryOutput(patient_id=patient_id, history=history)
            elif output_model == FollowBackQuestionOutput:
                questions_data = parsed_response.get("questions", [])
                return FollowBackQuestionOutput(
                    patient_id=patient_id, questions=questions_data
                )
            elif output_model == ChatResponseOutput:
                response_content = parsed_response.get("response", "")
                return ChatResponseOutput(
                    patient_id=patient_id,
                    response=response_content,
                    visit_id=cached_entry.visit_id,
                )
            else:
                response_data = parsed_response.get("response", {})
                confidence_score_data = parsed_response.get("confidence_score", {})

                if not confidence_score_data:
                    confidence_score_data = {
                        "status": "unknown",
                        "score_percentage": None,
                    }

                model_arguments = {
                    **response_data,
                    "confidence_score": confidence_score_data,
                    "patient_id": cached_entry.patient_id,
                    "visit_id": cached_entry.visit_id,
                }
                return output_model(**model_arguments)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(
                f"Error parsing cached LLM response for {output_model.__name__} "
                f"for patient {patient_id}, prompt {prompt_name}: {e}"
            )
            return None

    async def _get_llm_response_for_prompt(
        self,
        prompt_name: str,
        user_prompt_content: Dict[str, Any],
        output_model: Type[Any],
        patient_id: Optional[str] = None,
        visit_id: Optional[str] = None,
    ) -> Any:
        prompt_config = config.configs.PROMPTS.get(prompt_name, {})
        system_prompt_content = prompt_config.get("system_instruction", "")

        llm_user_prompt_content = user_prompt_content.copy()

        dump_llm_user_prompt_content = json.dumps(llm_user_prompt_content)
        sanitized_llm_user_prompt_content = sanitize_for_llm(
            dump_llm_user_prompt_content, max_tokens=4000
        )

        try:
            unescaped_sanitized = sanitized_llm_user_prompt_content.replace("\\", "")
            sanitized_json = json.loads(unescaped_sanitized)

            if llm_user_prompt_content != sanitized_json:
                log_security_event(
                    "potential_injection_attempt",
                    {
                        "method": prompt_name,
                        "input_modified": True,
                        "original_input": user_prompt_content,
                        "sanitized_input": sanitized_json,
                    },
                )
        except Exception as e:
            logger.error(f"Error parsing sanitized content: {e}")

        structured_prompt = create_structured_prompt(
            system_prompt_content, sanitized_llm_user_prompt_content
        )
        llm_response_str, _, _ = await self.llm_cache_service.get_llm_response(
            structured_prompt=structured_prompt,
            prompt_name=prompt_name,
            response_format={"type": "json_object"},
            patient_id=patient_id,
            visit_id=visit_id,
        )

        if not llm_response_str:
            logger.error("Failed to get a valid response from the language model.")
            raise HTTPException(
                status_code=500,
                detail="Failed to get a valid response from the language model.",
            )

        try:
            parsed_response = json.loads(llm_response_str.strip())

            if output_model == ChatHistoryOutput:
                history_data = parsed_response.get("history", [])
                history = [ChatMessage(**msg_data) for msg_data in history_data]
                return ChatHistoryOutput(patient_id=patient_id, history=history)
            elif output_model == FollowBackQuestionOutput:
                questions_data = parsed_response.get("questions", [])
                return FollowBackQuestionOutput(
                    patient_id=patient_id, questions=questions_data
                )
            elif output_model == ChatResponseOutput:
                response_content = parsed_response.get("response", "")
                return ChatResponseOutput(
                    patient_id=patient_id,
                    response=response_content,
                    visit_id=visit_id,
                )
            else:
                response_data = parsed_response.get("response", {})
                confidence_score_data = parsed_response.get("confidence_score", {})

                if not confidence_score_data:
                    log_security_event(
                        "response_missing_confidence_score",
                        {
                            "method": prompt_name,
                            "response_snippet": llm_response_str[:100],
                        },
                    )
                    confidence_score_data = {
                        "status": "unknown",
                        "score_percentage": None,
                    }

                model_arguments = {
                    **response_data,
                    "confidence_score": confidence_score_data,
                    "patient_id": patient_id,
                    "visit_id": visit_id,
                }
                result = output_model(**model_arguments)

                # Check for follow-up questions and cache them separately
                if (
                    hasattr(result, "follow_up_questions")
                    and result.follow_up_questions
                ):
                    await self.llm_cache_service._cache_response(
                        cache_key=str(uuid.uuid4()),
                        structured_prompt=json.dumps(
                            {
                                "patient_id": patient_id,
                                "questions": result.follow_up_questions,
                            }
                        ),
                        response_content=json.dumps(
                            {
                                "patient_id": patient_id,
                                "questions": result.follow_up_questions,
                            }
                        ),
                        prompt_name="follow_back_questions",
                        input_tokens=0,
                        output_tokens=0,
                        total_cost=0.0,
                        patient_id=patient_id,
                        visit_id=visit_id,
                    )

                if output_model not in [
                    ChatHistoryOutput,
                    FollowBackQuestionOutput,
                    ChatResponseOutput,
                ]:
                    response_content = json.dumps(result.model_dump(mode="json"))
                    assistant_chat_message = ChatMessage(
                        role="assistant", content=response_content
                    )
                    await self.save_chat_message(
                        patient_id, assistant_chat_message, visit_id
                    )

                return result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error parsing LLM response for {output_model.__name__}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error processing LLM response: {e}"
            )

    async def triage_cold_cases(
        self, input_data: TriageColdCaseInput
    ) -> TriageColdCaseOutput:
        return await self._get_llm_response_for_prompt(
            "triage_cold_cases",
            input_data.model_dump(mode="json"),
            TriageColdCaseOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def emergency_triage(
        self, input_data: EmergencyTriageInput
    ) -> EmergencyTriageOutput:
        return await self._get_llm_response_for_prompt(
            "emergency_triage",
            input_data.model_dump(mode="json"),
            EmergencyTriageOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def outpatient_history_physical_exam(
        self,
        input_data: OutpatientHPEInput,
    ) -> OutpatientHPEOutput:
        return await self._get_llm_response_for_prompt(
            "outpatient_history_physical_exam",
            input_data.model_dump(mode="json"),
            OutpatientHPEOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def outpatient_lab_result_interpretation(
        self,
        input_data: LabResultInterpretationInput,
    ) -> LabResultInterpretationOutput:
        return await self._get_llm_response_for_prompt(
            "outpatient_lab_result_interpretation",
            input_data.model_dump(mode="json"),
            LabResultInterpretationOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def radiology_image_interpretation(
        self,
        input_data: RadiologyImageInterpretationInput,
    ) -> RadiologyImageInterpretationOutput:
        return await self._get_llm_response_for_prompt(
            "radiology_image_interpretation",
            input_data.model_dump(mode="json"),
            RadiologyImageInterpretationOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def diagnosis(self, input_data: DiagnosisInput) -> DiagnosisOutput:
        return await self._get_llm_response_for_prompt(
            "diagnosis",
            input_data.model_dump(mode="json"),
            DiagnosisOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def medication(self, input_data: MedicationInput) -> MedicationOutput:
        return await self._get_llm_response_for_prompt(
            "medication",
            input_data.model_dump(mode="json"),
            MedicationOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def inpatient_admitted_patients(
        self, input_data: InpatientInput
    ) -> InpatientOutput:
        return await self._get_llm_response_for_prompt(
            "inpatient_admitted_patients",
            input_data.model_dump(mode="json"),
            InpatientOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def visit_summary(self, input_data: VisitSummaryInput) -> VisitSummaryOutput:
        return await self._get_llm_response_for_prompt(
            "visit_summary",
            input_data.model_dump(mode="json"),
            VisitSummaryOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def patient_education(
        self, input_data: PatientEducationInput
    ) -> PatientEducationOutput:
        return await self._get_llm_response_for_prompt(
            "patient_education",
            input_data.model_dump(mode="json"),
            PatientEducationOutput,
            patient_id=(
                input_data.patient_info.patient_id if input_data.patient_info else None
            ),
            visit_id=input_data.visit_info.visit_id if input_data.visit_info else None,
        )

    async def get_chat_history(self, patient_id: str) -> ChatHistoryOutput:
        """Retrieves the chat history for a given patient."""
        cached_entries = (
            self.llm_cache_service.get_cached_responses_by_patient_id_and_model(
                patient_id=patient_id, model_name="chat_history"
            )
        )
        history = []
        for entry in cached_entries:
            try:
                parsed_response = json.loads(entry.response.strip())
                entry_created_at = entry.created_at

                if isinstance(parsed_response, list):
                    for msg_data in parsed_response:
                        if isinstance(msg_data, dict):
                            msg_data_with_timestamp = {
                                **msg_data,
                                "created_at": entry_created_at,
                            }
                            history.append(ChatMessage(**msg_data_with_timestamp))
                        else:
                            logger.warning(
                                f"Unexpected chat message format in list: {msg_data}"
                            )
                elif isinstance(parsed_response, dict):
                    parsed_response_with_timestamp = {
                        **parsed_response,
                        "created_at": entry_created_at,
                    }
                    history.append(ChatMessage(**parsed_response_with_timestamp))
                else:
                    logger.warning(
                        f"Unexpected cached chat response format: {parsed_response}"
                    )
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(
                    f"Error parsing chat history entry for patient {patient_id}: {e}"
                )

        sorted_history = sorted(history, key=lambda msg: msg.created_at)

        return ChatHistoryOutput(patient_id=patient_id, history=sorted_history)

    async def get_follow_back_questions(
        self, patient_id: str
    ) -> FollowBackQuestionOutput:
        """Retrieves follow-back questions for a given patient."""
        cached_entries = (
            self.llm_cache_service.get_cached_responses_by_patient_id_and_model(
                patient_id=patient_id, model_name="follow_back_questions"
            )
        )
        all_questions = []
        for entry in cached_entries:
            try:
                parsed_response = json.loads(entry.response.strip())
                questions_data = parsed_response.get("questions", [])
                if isinstance(questions_data, list):
                    all_questions.extend(questions_data)
                else:
                    logger.warning(
                        f"Cached follow-back questions entry for patient {patient_id} is not a list: {questions_data}"
                    )
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(
                    f"Error parsing follow-back questions entry for patient {patient_id}: {e}"
                )
        return FollowBackQuestionOutput(patient_id=patient_id, questions=all_questions)

    async def save_chat_message(
        self, patient_id: str, message: ChatMessage, visit_id: Optional[str] = None
    ) -> None:
        """Saves a single chat message to the cache."""
        message_content = message.model_dump_json()
        cache_key = str(uuid.uuid4())
        await self.llm_cache_service._cache_response(
            cache_key=cache_key,
            structured_prompt=json.dumps(
                {"patient_id": patient_id, "message": message_content}
            ),
            response_content=message_content,
            prompt_name="chat_history",
            input_tokens=0,
            output_tokens=0,
            total_cost=0.0,
            patient_id=patient_id,
            visit_id=visit_id,
        )
        logger.info(f"Chat message for patient {patient_id} cached successfully.")

    async def handle_chat_message(self, input_data: ChatInput) -> ChatResponseOutput:
        """Handles a user's chat message, gets an LLM response, and caches both."""
        patient_id = input_data.patient_id
        user_message_content = input_data.message
        visit_id = input_data.visit_id

        # Get previous chat history and medical context
        chat_history = await self.get_chat_history(patient_id)
        all_cached_responses = (
            self.llm_cache_service.get_cached_responses_by_patient_id(patient_id)
        )

        patient_info_summary = None
        latest_vitals_summary = None
        medical_context_summary = "No medical history available."
        if all_cached_responses:
            non_chat_entries = [
                entry
                for entry in all_cached_responses
                if entry.model_name
                not in ["chat_history", "chat", "follow_back_questions"]
            ]
            if non_chat_entries:
                context_items = []
                non_chat_entries.sort(key=lambda x: x.created_at, reverse=True)

                for entry in non_chat_entries:
                    try:
                        prompt_data = json.loads(entry.structured_prompt)
                        user_content_str = prompt_data.get("messages", [{}])[0].get(
                            "content", "{}"
                        )
                        user_content = json.loads(user_content_str)

                        if not patient_info_summary and "patient_info" in user_content:
                            patient_info = user_content["patient_info"]
                            age = patient_info.get("age")
                            gender = patient_info.get("gender")
                            patient_info_summary = f"Patient Information: Age {age} years, Gender {gender}."

                        if not latest_vitals_summary and "vitals" in user_content:
                            vitals = user_content["vitals"]
                            vitals_summary_parts = []
                            for vital_key in [
                                "systolic_bp",
                                "diastolic_bp",
                                "pulse_rate",
                                "respiratory_rate",
                                "temperature",
                                "spo2",
                                "weight",
                                "height",
                            ]:
                                value = vitals.get(vital_key)
                                if value is not None:
                                    vitals_summary_parts.append(
                                        f"{vital_key.replace('_', ' ').title()}: {value}"
                                    )
                                else:
                                    vitals_summary_parts.append(
                                        f"{vital_key.replace('_', ' ').title()}: Not provided"
                                    )

                            if vitals_summary_parts:
                                latest_vitals_summary = (
                                    f"Latest Vitals: {'; '.join(vitals_summary_parts)}."
                                )
                            else:
                                latest_vitals_summary = (
                                    "Latest Vitals: No vital signs provided."
                                )
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

                for entry in non_chat_entries:
                    try:
                        response_data = json.loads(entry.response)
                        main_content = response_data.get("response", response_data)

                        summary_parts = []
                        for key, value in main_content.items():
                            if value and key not in [
                                "patient_id",
                                "visit_id",
                                "confidence_score",
                            ]:
                                summary_parts.append(
                                    f"{key.replace('_', ' ').title()}: {json.dumps(value)}"
                                )
                        readable_summary = "; ".join(summary_parts)

                        task_name = entry.model_name or "an unspecified task"
                        context_item = (
                            f"On {entry.created_at.strftime('%Y-%m-%d')}, for task '{task_name}', "
                            f"the following was recorded: {readable_summary}"
                        )
                        context_items.append(context_item)
                    except (json.JSONDecodeError, AttributeError):
                        context_items.append(
                            f"On {entry.created_at.strftime('%Y-%m-%d')}, an entry was recorded: {entry.response}"
                        )

                final_context_parts = []
                if patient_info_summary:
                    final_context_parts.append(patient_info_summary)
                if latest_vitals_summary:
                    final_context_parts.append(latest_vitals_summary)
                final_context_parts.extend(context_items)
                medical_context_summary = "\n".join(final_context_parts)

        # Save the new user's message to chat history
        user_chat_message = ChatMessage(role="user", content=user_message_content)
        await self.save_chat_message(patient_id, user_chat_message, visit_id)

        # Get LLM response with history context
        formatted_chat_history_parts = []
        for msg in chat_history.history:
            formatted_chat_history_parts.append(f"{msg.role.upper()}: {msg.content}")
        formatted_chat_history_parts.append(
            f"{user_chat_message.role.upper()}: {user_chat_message.content}"
        )
        formatted_chat_history_string = "\n".join(formatted_chat_history_parts)

        llm_response_output = await self._get_llm_response_for_prompt(
            "chat",
            {
                "medical_context": medical_context_summary,
                "conversation_history": formatted_chat_history_string,
            },
            ChatResponseOutput,
            patient_id=patient_id,
            visit_id=visit_id,
        )

        # Save the LLM's response to chat history
        assistant_chat_message = ChatMessage(
            role="assistant", content=llm_response_output.response
        )
        await self.save_chat_message(patient_id, assistant_chat_message, visit_id)

        return llm_response_output

    async def estimate_costs(
        self,
        input_data: CostEstimationInput,
        patient: Optional[Patient] = None,
    ) -> CostEstimationOutput:
        """
        Estimate costs for all clinical endpoints across different models.

        Calculates estimated token usage and costs for each endpoint. When sample
        data is provided, uses actual token counts for more accurate estimates.
        Otherwise, uses default estimates based on typical usage patterns.
        """
        # Default token estimates per endpoint when no sample data is provided
        default_estimates = {
            "triage_cold_cases": {"input": 800, "output": 600},
            "emergency_triage": {"input": 900, "output": 700},
            "outpatient_history_physical_exam": {"input": 1200, "output": 900},
            "outpatient_lab_result_interpretation": {"input": 1000, "output": 800},
            "radiology_image_interpretation": {"input": 800, "output": 600},
            "diagnosis": {"input": 1500, "output": 1000},
            "medication": {"input": 1200, "output": 900},
            "inpatient_admitted_patients": {"input": 1000, "output": 800},
            "visit_summary": {"input": 1200, "output": 800},
            "patient_education": {"input": 800, "output": 700},
        }

        # Map sample fields to endpoint names
        sample_mapping = {
            "triage_cold_cases": input_data.triage_cold_case_sample,
            "emergency_triage": input_data.emergency_triage_sample,
            "outpatient_history_physical_exam": input_data.outpatient_hpe_sample,
            "outpatient_lab_result_interpretation": input_data.lab_result_interpretation_sample,
            "radiology_image_interpretation": input_data.radiology_interpretation_sample,
            "diagnosis": input_data.diagnosis_sample,
            "medication": input_data.medication_sample,
            "inpatient_admitted_patients": input_data.inpatient_sample,
            "visit_summary": input_data.visit_summary_sample,
            "patient_education": input_data.patient_education_sample,
        }

        endpoint_estimates: List[EndpointCostEstimate] = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_costs: Dict[str, float] = {}

        for endpoint_name, defaults in default_estimates.items():
            sample = sample_mapping.get(endpoint_name)

            if sample:
                # Use actual token count from sample data
                prompt_config = config.configs.PROMPTS.get(endpoint_name, {})
                system_instruction = prompt_config.get("system_instruction", "")
                sample_json = json.dumps(sample.model_dump(mode="json"))
                estimated_input = count_tokens(system_instruction) + count_tokens(
                    sample_json
                )
                estimated_output = defaults["output"]
            else:
                estimated_input = defaults["input"]
                estimated_output = defaults["output"]

            # Scale by number of patients
            estimated_input *= input_data.num_patients
            estimated_output *= input_data.num_patients

            total_input_tokens += estimated_input
            total_output_tokens += estimated_output

            # Calculate cost per model
            costs_by_model = {}
            for model_name, pricing in config.configs.MODEL_PRICING.items():
                input_cost = (estimated_input / 1_000) * pricing[
                    "input_cost_per_1k_tokens"
                ]
                output_cost = (estimated_output / 1_000) * pricing[
                    "output_cost_per_1k_tokens"
                ]
                model_cost = input_cost + output_cost
                costs_by_model[model_name] = round(model_cost, 6)

                if model_name not in total_costs:
                    total_costs[model_name] = 0.0
                total_costs[model_name] += model_cost

            endpoint_estimates.append(
                EndpointCostEstimate(
                    endpoint_name=endpoint_name,
                    estimated_input_tokens=estimated_input,
                    estimated_output_tokens=estimated_output,
                    costs_by_model=costs_by_model,
                )
            )

        # Round total costs
        total_costs = {k: round(v, 6) for k, v in total_costs.items()}

        return CostEstimationOutput(
            num_patients=input_data.num_patients,
            endpoint_estimates=endpoint_estimates,
            total_estimated_input_tokens=total_input_tokens,
            total_estimated_output_tokens=total_output_tokens,
            total_costs_by_model=total_costs,
        )
