"""Data types and schemas for the ML preprocessing pipeline.

Follows the dataclass and enum design pattern established in ``backend/ml/contract.py``.
All dataclasses are frozen and provide deterministic serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


class ValidationSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR

    def to_dict(self) -> dict[str, str]:
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)
    cleaned_data: dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.WARNING)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }


@dataclass(frozen=True)
class TextQualityMetrics:
    char_count: int
    word_count: int
    line_count: int
    is_empty: bool
    is_very_short: bool
    detected_scripts: tuple[str, ...]
    has_multilingual_chars: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "char_count": self.char_count,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "is_empty": self.is_empty,
            "is_very_short": self.is_very_short,
            "detected_scripts": list(self.detected_scripts),
            "has_multilingual_chars": self.has_multilingual_chars,
        }


@dataclass(frozen=True)
class NormalizedText:
    raw: str
    clean: str
    language: Optional[str]
    quality: TextQualityMetrics

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "clean": self.clean,
            "language": self.language,
            "quality": self.quality.to_dict(),
        }


@dataclass(frozen=True)
class MissingnessReport:
    total_expected_fields: int
    missing_fields: tuple[str, ...]
    available_fields: tuple[str, ...]
    missing_count: int
    completeness_ratio: float
    is_text_missing: bool
    is_voice_missing: bool
    is_behavioural_missing: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_expected_fields": self.total_expected_fields,
            "missing_fields": list(self.missing_fields),
            "available_fields": list(self.available_fields),
            "missing_count": self.missing_count,
            "completeness_ratio": self.completeness_ratio,
            "is_text_missing": self.is_text_missing,
            "is_voice_missing": self.is_voice_missing,
            "is_behavioural_missing": self.is_behavioural_missing,
        }


@dataclass(frozen=True)
class PreprocessedInteraction:
    """Standardized representation of a single interaction ready for downstream features.

    Preserves missing values as None (never blindly coercing to 0) and records
    any unknown/unrecognized fields in ``metadata`` for forward compatibility.
    """

    case_id: str
    interaction_date: str
    language: str
    text: Optional[NormalizedText]
    behavioural: Mapping[str, Optional[float]]
    engagement: Mapping[str, Any]
    voice: Mapping[str, Optional[float]]
    metadata: Mapping[str, Any]
    missingness: MissingnessReport
    validation: ValidationResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "interaction_date": self.interaction_date,
            "language": self.language,
            "text": None if self.text is None else self.text.to_dict(),
            "behavioural": dict(self.behavioural),
            "engagement": dict(self.engagement),
            "voice": dict(self.voice),
            "metadata": dict(self.metadata),
            "missingness": self.missingness.to_dict(),
            "validation": self.validation.to_dict(),
        }

    @property
    def is_usable(self) -> bool:
        """Indicates whether this record passed critical validation."""
        return self.validation.is_valid
