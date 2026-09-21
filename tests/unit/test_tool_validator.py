"""Unit tests for ToolValidator adhering to docs/Rules.md Sections 38-39."""

import pytest

from domain.tools.exceptions import ToolValidationError
from tools.gateway.validator import ToolValidator


def test_validate_input_success() -> None:
    """Verify input validation succeeds when all required properties are present."""
    schema = {
        "type": "object",
        "required": ["query"],
        "properties": {"query": {"type": "string"}},
    }
    # Should not raise
    ToolValidator.validate_input("web_search", schema, {"query": "AI architecture"})


def test_validate_input_missing_required() -> None:
    """Verify missing required parameter raises ToolValidationError."""
    schema = {
        "type": "object",
        "required": ["repository", "action"],
        "properties": {
            "repository": {"type": "string"},
            "action": {"type": "string"},
        },
    }
    with pytest.raises(ToolValidationError) as exc_info:
        ToolValidator.validate_input("github", schema, {"repository": "moon90/AICompanyOS"})
    assert "missing required input parameter: 'action'" in str(exc_info.value)


def test_sanitize_parameters_masks_secrets() -> None:
    """Verify secret patterns (API keys, tokens, passwords) are automatically masked."""
    params = {
        "query": "find bug",
        "api_key": "sk-1234567890abcdef1234567890",
        "github_token": "ghp_123456789012345678901234567890123456",
        "nested": {
            "password": "SuperSecretPassword123!",
            "normal_field": "public_data",
        },
    }

    sanitized = ToolValidator.sanitize_parameters(params)

    assert sanitized["query"] == "find bug"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["github_token"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["nested"]["normal_field"] == "public_data"


def test_sanitize_parameters_masks_bearer_in_string() -> None:
    """Verify bearer tokens embedded within string values are masked."""
    params = {
        "auth_header": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tokencontenthere1234",
    }
    sanitized = ToolValidator.sanitize_parameters(params)
    assert "[REDACTED]" in sanitized["auth_header"]
