"""
Security Utility Module

Provides security functions for protecting against prompt injection attacks
and ensuring safe interaction with Large Language Models.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import tiktoken
from loguru import logger

# Default constant for prompt max tokens
PROMPT_MAX_TOKENS = 4000

# Initialize security logger
security_logger = logger.bind(name="security.prompt_injection")

# Common injection patterns that should be detected and sanitized
INJECTION_PATTERNS = [
    # Direct instruction manipulation
    r"ignore previous instructions",
    r"ignore all previous instructions",
    r"disregard previous instructions",
    r"forget previous instructions",
    r"override previous instructions",
    r"new instructions:",
    r"system:",
    r"system prompt:",
    r"###instruction###",
    r"###system###",
    # Role manipulation attempts
    r"you are now",
    r"you must now",
    r"act as",
    r"pretend to be",
    r"imagine you are",
    r"switch to",
    r"change your role",
    # Output manipulation
    r"print the following",
    r"output exactly",
    r"repeat after me",
    r"say exactly",
    r"write exactly",
    # Delimiter injection
    r"\n\n###",
    r"\n\nsystem:",
    r"```system",
    r"</system>",
    r"<system>",
    # Prompt leaking attempts
    r"show your instructions",
    r"reveal your prompt",
    r"what are your instructions",
    r"display your system prompt",
    r"show me your rules",
]

# Compile regex patterns for efficiency
COMPILED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS
]

# Special characters that need escaping in prompts
SPECIAL_CHARS_PATTERN = re.compile(r"([<>{}\\])")

# Token encoder for GPT models
try:
    TOKEN_ENCODER = tiktoken.encoding_for_model("gpt-4")
except Exception:
    TOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text string.

    Args:
        text: The text to count tokens for

    Returns:
        Number of tokens in the text
    """
    try:
        return len(TOKEN_ENCODER.encode(text))
    except Exception as e:
        security_logger.warning(
            f"Token counting failed: {e}. Using character estimate."
        )
        # Fallback: estimate ~4 characters per token
        return len(text) // 4


def detect_injection_patterns(text: str) -> List[str]:
    """
    Detect potential injection patterns in the input text.

    Args:
        text: The text to analyze for injection patterns

    Returns:
        List of detected injection patterns
    """
    detected_patterns = []

    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            detected_patterns.append(pattern.pattern)

    if detected_patterns:
        security_logger.warning(
            f"Detected {len(detected_patterns)} potential injection patterns",
            patterns=detected_patterns[:5],
        )

    return detected_patterns


def sanitize_for_llm(text: str, max_tokens: int = PROMPT_MAX_TOKENS) -> str:
    """
    Sanitize user input for safe use in LLM prompts.

    Args:
        text: The user input text to sanitize
        max_tokens: Maximum number of tokens allowed

    Returns:
        Sanitized text safe for LLM processing
    """
    if not text:
        return ""

    # Pattern-based detection
    injection_attempts = detect_injection_patterns(text)

    # Replace detected injection patterns with [REDACTED]
    sanitized_text = text
    for pattern in COMPILED_PATTERNS:
        sanitized_text = pattern.sub("[REDACTED]", sanitized_text)

    # Escape special characters that could break prompt structure
    sanitized_text = SPECIAL_CHARS_PATTERN.sub(r"\\\1", sanitized_text)

    # Remove multiple consecutive newlines (potential delimiter injection)
    sanitized_text = re.sub(r"\n{3,}", "\n\n", sanitized_text)

    # Trim to token limit
    token_count = count_tokens(sanitized_text)
    if token_count > max_tokens:
        char_limit = int((max_tokens / token_count) * len(sanitized_text))
        sanitized_text = sanitized_text[:char_limit] + "... [TRUNCATED]"
        security_logger.info(
            f"Input truncated from {token_count} to ~{max_tokens} tokens"
        )

    # Log if injection was detected
    if injection_attempts:
        security_logger.warning(
            "Input sanitized due to injection attempts",
            attempts_count=len(injection_attempts),
            original_length=len(text),
            sanitized_length=len(sanitized_text),
        )

    return sanitized_text


async def sanitize_for_llm_async(text: str, max_tokens: int = PROMPT_MAX_TOKENS) -> str:
    """
    Async version of sanitize_for_llm for non-blocking operations.

    Args:
        text: The user input text to sanitize
        max_tokens: Maximum number of tokens allowed

    Returns:
        Sanitized text safe for LLM processing
    """
    if not text:
        return ""

    return sanitize_for_llm(text, max_tokens)


def create_structured_prompt(system_instruction: str, user_input: str) -> str:
    """
    Create a structured prompt with clear boundaries between system and user content.

    Args:
        system_instruction: The system-level instruction for the LLM
        user_input: The user-provided input (should be pre-sanitized)

    Returns:
        Structured prompt with clear delimiters
    """
    # Ensure system instruction doesn't contain user manipulation
    if detect_injection_patterns(system_instruction):
        raise ValueError("System instruction contains potential injection patterns")

    structured_prompt = f"""SYSTEM_INSTRUCTION:
{system_instruction}

USER_INPUT:
---BEGIN USER INPUT---
{user_input}
---END USER INPUT---

Please process the user input according to the system instruction above. Your response must be in JSON format."""

    return structured_prompt


def validate_ai_response(
    response: str, expected_format: Dict[str, Any]
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate that a response matches the expected format.

    Args:
        response: The model's response
        expected_format: Dictionary describing expected response structure

    Returns:
        Tuple of (is_valid, parsed_response)
    """
    try:
        parsed = json.loads(response)

        if "required_keys" in expected_format:
            for key in expected_format["required_keys"]:
                if key == "confidence_score":
                    continue

                if key == "response":
                    if key not in parsed:
                        security_logger.warning(
                            f"Missing required key in response: {key}"
                        )
                        return False, None
                elif key not in parsed.get("response", {}):
                    security_logger.warning(f"Missing required key in response: {key}")
                    return False, None

        if "types" in expected_format:
            response_data = parsed.get("response", {})
            for key, expected_type in expected_format["types"].items():
                if key in response_data:
                    if expected_type == "boolean" and not isinstance(
                        response_data[key], bool
                    ):
                        security_logger.warning(
                            f"Invalid type for {key}: expected boolean"
                        )
                        return False, None
                    elif expected_type == "string" and not isinstance(
                        response_data[key], str
                    ):
                        security_logger.warning(
                            f"Invalid type for {key}: expected string"
                        )
                        return False, None
                    elif expected_type == "number" and not isinstance(
                        response_data[key], (int, float)
                    ):
                        security_logger.warning(
                            f"Invalid type for {key}: expected number"
                        )
                        return False, None

        if "validators" in expected_format:
            response_data = parsed.get("response", {})
            for key, validator in expected_format["validators"].items():
                if key in response_data:
                    if response_data[key] not in validator:
                        security_logger.warning(f"Validation failed for {key}")
                        return False, None

        return True, parsed

    except json.JSONDecodeError as e:
        security_logger.error(f"Failed to parse response as JSON: {e}")
        return False, None
    except Exception as e:
        security_logger.error(f"Unexpected error validating response: {e}")
        return False, None


def create_safe_json_prompt(data: Dict[str, Any]) -> str:
    """
    Create a safe JSON representation for inclusion in prompts.

    Args:
        data: Dictionary to convert to safe JSON

    Returns:
        Safe JSON string for prompt inclusion
    """
    safe_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            safe_data[key] = sanitize_for_llm(value, max_tokens=500)
        elif isinstance(value, dict):
            safe_data[key] = create_safe_json_prompt(value)
        elif isinstance(value, list):
            safe_data[key] = [
                (
                    sanitize_for_llm(item, max_tokens=500)
                    if isinstance(item, str)
                    else item
                )
                for item in value
            ]
        else:
            safe_data[key] = value

    return json.dumps(safe_data, ensure_ascii=True, indent=2)


def log_security_event(event_type: str, details: Dict[str, Any]) -> None:
    """
    Log security-related events for monitoring and alerting.

    Args:
        event_type: Type of security event
        details: Additional details about the event
    """
    security_logger.warning(
        f"Security event: {event_type}", event_type=event_type, **details
    )
