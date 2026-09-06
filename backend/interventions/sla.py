"""
AAROH — Service Level Agreement (SLA) Engine
Author: Preet

Manages response deadlines, overdue detection, and SLA compliance tracking
across all intervention priority tiers.
Enforces UTC timezone-awareness and strictly separates workflow status
from SLA compliance status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional
from .engine import PriorityLevel


class SLAStatus(str, Enum):
    """Operational SLA compliance status, distinct from intervention workflow status."""
    PENDING = "PENDING"
    DUE_SOON = "DUE_SOON"
    OVERDUE = "OVERDUE"
    MET = "MET"
    BREACHED = "BREACHED"


@dataclass(frozen=True)
class SLARule:
    priority: PriorityLevel
    response_window_hours: float
    due_soon_threshold_ratio: float = 0.80  # Flags 'DUE_SOON' when 80% of window elapsed


# Centralised SLA Configuration
# SLA Start Event: The moment an intervention is created / assigned.
DEFAULT_SLA_RULES: Dict[PriorityLevel, SLARule] = {
    PriorityLevel.URGENT: SLARule(PriorityLevel.URGENT, response_window_hours=4.0),
    PriorityLevel.HIGH: SLARule(PriorityLevel.HIGH, response_window_hours=24.0),
    PriorityLevel.ROUTINE: SLARule(PriorityLevel.ROUTINE, response_window_hours=72.0),
    PriorityLevel.LOW: SLARule(PriorityLevel.LOW, response_window_hours=120.0),
    PriorityLevel.NONE: SLARule(PriorityLevel.NONE, response_window_hours=0.0),
}


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensures a datetime object is timezone-aware UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass
class SLARecord:
    """
    Tracks lifecycle timestamps and SLA compliance for an intervention.
    Start Event: created_at (or assigned_at when assigned).
    """
    intervention_id: int
    priority: PriorityLevel
    created_at: datetime
    due_at: datetime
    assigned_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        self.created_at = ensure_utc(self.created_at)  # type: ignore[assignment]
        self.due_at = ensure_utc(self.due_at)  # type: ignore[assignment]
        if self.assigned_at is not None:
            self.assigned_at = ensure_utc(self.assigned_at)
        if self.acknowledged_at is not None:
            self.acknowledged_at = ensure_utc(self.acknowledged_at)
        if self.completed_at is not None:
            self.completed_at = ensure_utc(self.completed_at)

    def is_overdue(self, current_time: Optional[datetime] = None) -> bool:
        """
        Rule 4: Overdue strictly means current_time > due_at AND not completed.
        Completed interventions are never active 'OVERDUE' (they are MET or BREACHED).
        """
        if self.completed_at is not None:
            return False
        now = ensure_utc(current_time) if current_time else datetime.now(timezone.utc)
        return now > self.due_at

    def evaluate_status(self, current_time: Optional[datetime] = None) -> SLAStatus:
        """
        Evaluates SLA compliance status based on current time or completion timestamp.
        """
        now = ensure_utc(current_time) if current_time else datetime.now(timezone.utc)

        # 1. Terminal evaluation if completed
        if self.completed_at is not None:
            if self.completed_at <= self.due_at:
                return SLAStatus.MET
            return SLAStatus.BREACHED

        # 2. Active overdue check
        if self.is_overdue(now):
            return SLAStatus.OVERDUE

        # 3. Approaching deadline check (80% of window elapsed)
        total_window = (self.due_at - self.created_at).total_seconds()
        elapsed = (now - self.created_at).total_seconds()

        if total_window > 0 and (elapsed / total_window) >= 0.80:
            return SLAStatus.DUE_SOON

        return SLAStatus.PENDING

    def response_time_hours(self) -> Optional[float]:
        """Time in hours from SLA start (created_at) to first acknowledgement."""
        if not self.acknowledged_at:
            return None
        diff = (self.acknowledged_at - self.created_at).total_seconds() / 3600.0
        return round(diff, 2)

    def resolution_time_hours(self) -> Optional[float]:
        """Time in hours from SLA start (created_at) to completion."""
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
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_overdue": self.is_overdue(current_time),
            "sla_status": self.evaluate_status(current_time).value,
            "response_time_hours": self.response_time_hours(),
            "resolution_time_hours": self.resolution_time_hours(),
        }


class SLAManager:
    """
    Computes deadlines and tracks SLA compliance.
    """

    def __init__(self, rules: Optional[Dict[PriorityLevel, SLARule]] = None) -> None:
        self.rules = rules or DEFAULT_SLA_RULES

    def get_response_window_hours(self, priority: PriorityLevel) -> float:
        """Returns the configured SLA response window for a priority."""
        rule = self.rules.get(priority, self.rules[PriorityLevel.ROUTINE])
        return rule.response_window_hours

    def compute_due_time(
        self,
        priority: PriorityLevel,
        start_time: Optional[datetime] = None,
    ) -> datetime:
        """
        SLA start event: start_time defaults to now (UTC).
        due_at = start_time + response_window_hours
        """
        start = ensure_utc(start_time) if start_time else datetime.now(timezone.utc)
        hours = self.get_response_window_hours(priority)
        return start + timedelta(hours=hours)

    def create_record(
        self,
        intervention_id: int,
        priority: PriorityLevel,
        start_time: Optional[datetime] = None,
        assigned_at: Optional[datetime] = None,
    ) -> SLARecord:
        start = ensure_utc(start_time) if start_time else datetime.now(timezone.utc)
        due = self.compute_due_time(priority, start)
        return SLARecord(
            intervention_id=intervention_id,
            priority=priority,
            created_at=start,
            due_at=due,
            assigned_at=ensure_utc(assigned_at) if assigned_at else start,
        )
