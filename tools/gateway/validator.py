"""Input/output validation and secret sanitization adhering to docs/Rules.md Sections 34, 35, 38, 39."""

import re
from typing import Any

from domain.tools.exceptions import ToolValidationError


class ToolValidator:
    """Validates tool inputs/outputs and sanitizes sensitive data."""

    # Patterns for secrets to prevent leaking credentials in prompts/logs (docs/Rules.md § 38-39)
    SECRET_PATTERNS = [
        re.compile(
            r"(?i)(api[-_]?key|secret|token|password|bearer|auth)[\s:=]+['\"]?([a-zA-Z0-9_\-\.]{12,})['\"]?"
        ),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"sk-[a-zA-Z0-9]{32,}"),
    ]

    @classmethod
    def sanitize_parameters(cls, params: dict[str, Any]) -> dict[str, Any]:
        """Sanitize input parameters by masking potential credentials or API keys."""
        sanitized: dict[str, Any] = {}
        for key, val in params.items():
            if isinstance(val, str):
                cleaned = val
                for pattern in cls.SECRET_PATTERNS:
                    if pattern.groups >= 1:
                        cleaned = pattern.sub(r"\1 [REDACTED]", cleaned)
                    else:
                        cleaned = pattern.sub("[REDACTED]", cleaned)
                # Specific high-risk keys
                if any(k in key.lower() for k in ("secret", "password", "token", "key")):
                    cleaned = "[REDACTED]"
                sanitized[key] = cleaned
            elif isinstance(val, dict):
                sanitized[key] = cls.sanitize_parameters(val)
            else:
                sanitized[key] = val
        return sanitized

    @classmethod
    def validate_input(
        cls, tool_name: str, input_schema: dict[str, Any], parameters: dict[str, Any]
    ) -> None:
        """Validate input parameters against declared required properties."""
        if not input_schema:
            return

        required_props = input_schema.get("required", [])
        for prop in required_props:
            if prop not in parameters:
                raise ToolValidationError(
                    f"Tool '{tool_name}' missing required input parameter: '{prop}'.",
                    details={"missing_parameter": prop, "schema": input_schema},
                )

        # Check property types if specified
        properties = input_schema.get("properties", {})
        for prop, prop_schema in properties.items():
            if prop in parameters and parameters[prop] is not None:
                expected_type = prop_schema.get("type")
                val = parameters[prop]
                if expected_type == "string" and not isinstance(val, str):
                    raise ToolValidationError(
                        f"Parameter '{prop}' must be a string, got {type(val).__name__}."
                    )
                elif expected_type == "integer" and not isinstance(val, int):
                    raise ToolValidationError(
                        f"Parameter '{prop}' must be an integer, got {type(val).__name__}."
                    )
                elif expected_type == "boolean" and not isinstance(val, bool):
                    raise ToolValidationError(
                        f"Parameter '{prop}' must be a boolean, got {type(val).__name__}."
                    )
                elif expected_type == "array" and not isinstance(val, list):
                    raise ToolValidationError(
                        f"Parameter '{prop}' must be a list/array, got {type(val).__name__}."
                    )
                elif expected_type == "object" and not isinstance(val, dict):
                    raise ToolValidationError(
                        f"Parameter '{prop}' must be an object/dict, got {type(val).__name__}."
                    )
