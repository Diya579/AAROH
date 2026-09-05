"""
AAROH — Service Level Agreement (SLA) Engine
Author: Preet

Manages response deadlines, overdue detection, and SLA compliance tracking
across all intervention priority tiers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional
from .engine import PriorityLevel


class SLAStatus(str, Enum):
    PENDING = "PENDING"
    DUE_SOON = "DUE_SOON"
    OVERDUE = "OVERDUE"
    MET = "MET"
    BREACHED = "BREACHED"


@dataclass(frozen=True)
class SLARule:
    priority: PriorityLevel
    response_window_hours: float
    due_soon_threshold_ratio: float = 0.80  # Flags 'DUE_SOON' when 80% elapsed


DEFAULT_SLA_RULES: Dict[PriorityLevel, SLARule] = {
    PriorityLevel.URGENT: SLARule(PriorityLevel.URGENT, response_window_hours=4.0),
    PriorityLevel.HIGH: SLARule(PriorityLevel.HIGH, response_window_hours=24.0),
    PriorityLevel.ROUTINE: SLARule(PriorityLevel.ROUTINE, response_window_hours=72.0),
    PriorityLevel.LOW: SLARule(PriorityLevel.LOW, response_window_hours=120.0),
    PriorityLevel.NONE: SLARule(PriorityLevel.NONE, response_window_hours=0.0),
}


@dataclass
class SLARecord:
    intervention_id: int
    priority: PriorityLevel
    created_at: datetime
    due_at: datetime
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def evaluate_status(self, current_time: Optional[datetime] = None) -> SLAStatus:
        now = current_time or datetime.utcnow()

        if self.completed_at is not None:
            if self.completed_at <= self.due_at:
                return SLAStatus.MET
            return SLAStatus.BREACHED

        if now > self.due_at:
            return SLAStatus.OVERDUE

        total_window = (self.due_at - self.created_at).total_seconds()
        elapsed = (now - self.created_at).total_seconds()

        if total_window > 0 and (elapsed / total_window) >= 0.80:
            return SLAStatus.DUE_SOON

        return SLAStatus.PENDING

    def response_time_hours(self) -> Optional[float]:
        """Time from creation to first human acknowledgement."""
        if not self.acknowledged_at:
            return None
        diff = (self.acknowledged_at - self.created_at).total_seconds() / 3600.0
        return round(diff, 2)

    def resolution_time_hours(self) -> Optional[float]:
        """Time from creation to completion."""
        if not self.completed_at:
            return None
        diff = (self.completed_at - self.created_at).total_seconds() / 3600.0
        return round(diff, 2)

    def to_dict(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "due_at": self.due_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.evaluate_status(current_time).value,
            "response_time_hours": self.response_time_hours(),
            "resolution_time_hours": self.resolution_time_hours(),
        }


class SLAManager:
    """
    Computes deadlines and tracks SLA compliance.
    """

    def __init__(self, rules: Optional[Dict[PriorityLevel, SLARule]] = None) -> None:
        self.rules = rules or DEFAULT_SLA_RULES

    def compute_due_time(
        self,
        priority: PriorityLevel,
        start_time: Optional[datetime] = None,
    ) -> datetime:
        start = start_time or datetime.utcnow()
        rule = self.rules.get(priority, self.rules[PriorityLevel.ROUTINE])
        return start + timedelta(hours=rule.response_window_hours)

    def create_record(
        self,
        intervention_id: int,
        priority: PriorityLevel,
        start_time: Optional[datetime] = None,
    ) -> SLARecord:
        start = start_time or datetime.utcnow()
        due = self.compute_due_time(priority, start)
        return SLARecord(
            intervention_id=intervention_id,
            priority=priority,
            created_at=start,
            due_at=due,
        )
