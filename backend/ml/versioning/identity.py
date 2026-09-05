"""Model identity helpers for versioned artifacts.

Slice 1 records the contract fields only. Artifact files and training
metadata are added in later slices. Predictions are not persisted here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional


@dataclass(frozen=True)
class ModelIdentity:
    model_name: str
    version: str
    created_at: Optional[str] = None
    feature_version: Optional[str] = None
    training_dataset_version: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.model_name or not self.version:
            raise ValueError("model_name and version are required")

    def to_contract_dict(self) -> dict[str, str]:
        return {
            "model_name": self.model_name,
            "model_version": self.version,
        }

    def to_metadata_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "version": self.version,
            "created_at": self.created_at,
            "feature_version": self.feature_version,
            "training_dataset_version": self.training_dataset_version,
        }


def utc_today_iso() -> str:
    return date.today().isoformat()


def format_created_at(value: datetime | date | str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)[:10]
