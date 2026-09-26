"""Prompt Injection & Credential Leak Defense System adhering to docs/Rules.md § 30, § 31, and § 169."""

import re
from dataclasses import dataclass, field
from re import Pattern


@dataclass
class PromptScanResult:
    """Result of prompt injection scanning and credential redaction."""

    is_safe: bool
    injection_detected: bool
    injection_indicators: list[str] = field(default_factory=list)
    redacted_content: str = ""
    redacted_secrets_count: int = 0
    data_tagged_content: str = ""


class PromptGuard:
    """Adversarial prompt injection detector and sensitive credential redactor."""

    # Common injection phrases and jailbreak signatures
    INJECTION_PATTERNS: list[tuple[str, Pattern[str]]] = [
        (
            "SYSTEM_PROMPT_OVERRIDE",
            re.compile(
                r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|directions)",
                re.IGNORECASE,
            ),
        ),
        (
            "SYSTEM_PROMPT_DISREGARD",
            re.compile(
                r"disregard\s+(all\s+)?(previous|prior|past|earlier|system|above)\s+(instructions|prompts|rules|directions|commands)",
                re.IGNORECASE,
            ),
        ),
        (
            "DEVELOPER_MODE_JAILBREAK",
            re.compile(
                r"(enter|switch\s+to|enable)\s+(developer|dan|unfiltered|jailbreak)\s+mode",
                re.IGNORECASE,
            ),
        ),
        (
            "SYSTEM_DIRECTIVE_HIJACK",
            re.compile(
                r"you\s+are\s+now\s+(an?\s+unrestricted|a\s+different|in\s+developer|unfiltered)",
                re.IGNORECASE,
            ),
        ),
        (
            "SECRET_EXTRACTION_PROMPT",
            re.compile(
                r"(reveal|print|output|display|show|leak)\s+(your\s+)?(system\s+prompt|instructions|api\s*key|secret)",
                re.IGNORECASE,
            ),
        ),
        (
            "SECURITY_BYPASS_ATTEMPT",
            re.compile(
                r"bypass\s+(all\s+)?(security|policy|restrictions|filters|guidelines)",
                re.IGNORECASE,
            ),
        ),
        (
            "DELIMITER_HIJACK_TAG",
            re.compile(r"</?(system|instructions|admin|prompt_override)>", re.IGNORECASE),
        ),
        (
            "ROLEPLAY_EXPLOIT",
            re.compile(
                r"for\s+the\s+rest\s+of\s+this\s+conversation\s+you\s+will\s+act\s+as\s+an\s+unaligned",
                re.IGNORECASE,
            ),
        ),
    ]

    # Sensitive credential redaction patterns
    CREDENTIAL_PATTERNS: list[tuple[str, Pattern[str]]] = [
        ("OPENAI_KEY", re.compile(r"sk-[a-zA-Z0-9_\-]{20,}")),
        ("ANTHROPIC_KEY", re.compile(r"sk-ant-[a-zA-Z0-9_\-]{20,}")),
        ("AWS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
        (
            "DATABASE_URI_PASSWORD",
            re.compile(r"(postgres(?:ql)?|mysql|redis|mongodb)://[^:]+:([^@]+)@"),
        ),
        (
            "JWT_TOKEN",
            re.compile(r"eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]+"),
        ),
        (
            "PRIVATE_KEY_BLOCK",
            re.compile(
                r"-----BEGIN\s+[A-Z ]*PRIVATE KEY-----[^-]+-----END\s+[A-Z ]*PRIVATE KEY-----",
                re.DOTALL,
            ),
        ),
        ("GENERIC_BEARER_TOKEN", re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{25,}")),
    ]

    @classmethod
    def scan_and_sanitize(cls, content: str, source_type: str = "EXTERNAL") -> PromptScanResult:
        """Scan input content for adversarial injections and redact sensitive secrets."""
        if not content:
            return PromptScanResult(
                is_safe=True,
                injection_detected=False,
                injection_indicators=[],
                redacted_content="",
                redacted_secrets_count=0,
                data_tagged_content="",
            )

        indicators: list[str] = []
        for name, pattern in cls.INJECTION_PATTERNS:
            if pattern.search(content):
                indicators.append(name)

        injection_detected = len(indicators) > 0

        # Redact credentials
        sanitized = content
        redacted_count = 0
        for name, pattern in cls.CREDENTIAL_PATTERNS:
            matches = list(pattern.finditer(sanitized))
            if matches:
                redacted_count += len(matches)
                sanitized = pattern.sub(f"[REDACTED_{name}]", sanitized)

        # Enforce Rule 169: Tag untrusted external input as DATA, never INSTRUCTION
        data_tagged = f'<untrusted_data source="{source_type}">\n{sanitized}\n</untrusted_data>'

        return PromptScanResult(
            is_safe=not injection_detected,
            injection_detected=injection_detected,
            injection_indicators=indicators,
            redacted_content=sanitized,
            redacted_secrets_count=redacted_count,
            data_tagged_content=data_tagged,
        )

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """Convenience method to scrub text of any embedded credentials."""
        if not text:
            return ""
        result = text
        for name, pattern in cls.CREDENTIAL_PATTERNS:
            result = pattern.sub(f"[REDACTED_{name}]", result)
        return result
