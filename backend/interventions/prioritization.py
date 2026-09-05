"""
AAROH — Intervention Prioritization Engine
Author: Preet

Calculates dynamic operational urgency and generates prioritized case queues
to ensure officials address high-risk and deteriorating cases first.
"""

from __future__ import annotations

from typing import Any, List, Optional
from .engine import PriorityLevel


def calculate_priority(
    risk_level: str,
    escalation_probability: float,
    trajectory: str,
    confidence: float = 1.0,
    has_unresolved_urgent: bool = False,
    is_overdue: bool = False,
) -> PriorityLevel:
    """
    Computes priority based on multi-signal risk and trajectory analysis.
    """
    risk = risk_level.upper()
    traj = trajectory.upper()

    # Breached SLA or unresolved critical items escalate immediately to URGENT
    if is_overdue or has_unresolved_urgent:
        return PriorityLevel.URGENT

    # Rapid worsening or High risk with high escalation probability
    if risk == "HIGH" or escalation_probability >= 0.75 or traj == "RAPIDLY_WORSENING":
        return PriorityLevel.URGENT

    # Moderate risk or worsening trajectory
    if risk == "MODERATE" or escalation_probability >= 0.40 or traj == "WORSENING":
        return PriorityLevel.HIGH

    # Improving cases require minimal immediate intervention
    if traj in ("IMPROVING", "RAPIDLY_IMPROVING"):
        return PriorityLevel.LOW

    # Stable baseline
    return PriorityLevel.ROUTINE


def compute_case_urgency_score(case_data: dict[str, Any]) -> float:
    """
    Computes a composite urgency ranking score (0.0 to 100.0) for sorting casework queues.
    Considers:
    - Escalation probability (weight: 40)
    - Risk level (weight: 25)
    - Trajectory (weight: 20)
    - Overdue / SLA breach penalty (weight: 15)
    """
    score = 0.0

    # 1. Escalation probability (up to 40 pts)
    escalation_prob = float(case_data.get("escalation_probability") or 0.0)
    score += escalation_prob * 40.0

    # 2. Risk Level (up to 25 pts)
    risk = str(case_data.get("risk_level") or "LOW").upper()
    if risk == "HIGH":
        score += 25.0
    elif risk == "MODERATE":
        score += 15.0
    elif risk == "LOW":
        score += 5.0

    # 3. Trajectory (up to 20 pts)
    traj = str(case_data.get("trajectory") or "STABLE").upper()
    if traj == "RAPIDLY_WORSENING":
        score += 20.0
    elif traj == "WORSENING":
        score += 12.0
    elif traj == "STABLE":
        score += 5.0
    elif traj in ("IMPROVING", "RAPIDLY_IMPROVING"):
        score += 0.0

    # 4. Overdue penalty (15 pts)
    if case_data.get("is_overdue", False):
        score += 15.0

    return round(score, 2)


def rank_cases_by_priority(cases: List[dict[str, Any]]) -> List[dict[str, Any]]:
    """
    Returns case list sorted in descending order of operational urgency.
    """
    return sorted(cases, key=compute_case_urgency_score, reverse=True)
