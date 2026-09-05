"""
AAROH — Operational Assignment & Routing Engine
Author: Preet

Implements district-aware, role-based, capacity-informed routing with
primary and backup assignee failover logic.
Uses clearly marked synthetic officials for prototype demonstrations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from .engine import InterventionType, PriorityLevel


class AssigneeRole(str, Enum):
    COUNSELLOR = "COUNSELLOR"
    CASE_OFFICER = "CASE_OFFICER"
    DESIGNATED_OFFICER = "DESIGNATED_OFFICER"
    DISTRICT_AUTHORITY = "DISTRICT_AUTHORITY"


@dataclass
class SyntheticOfficer:
    official_id: str
    name: str
    role: AssigneeRole
    district: str
    active_caseload: int = 0
    is_available: bool = True


@dataclass
class RoutingResult:
    case_id: str
    assigned_role: AssigneeRole
    primary_assignee: str
    backup_assignee: Optional[str]
    district: str
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "assigned_role": self.assigned_role.value,
            "primary_assignee": self.primary_assignee,
            "backup_assignee": self.backup_assignee,
            "district": self.district,
            "assigned_at": self.assigned_at.isoformat(),
            "notes": self.notes,
        }


# Clearly marked synthetic pool for prototyping and validation
DEMO_OFFICER_REGISTRY: List[SyntheticOfficer] = [
    SyntheticOfficer("SYNTH-COUNS-01", "[SIMULATED] Dr. A. Verma", AssigneeRole.COUNSELLOR, "Patna", active_caseload=2),
    SyntheticOfficer("SYNTH-COUNS-02", "[SIMULATED] S. Mukherjee", AssigneeRole.COUNSELLOR, "Patna", active_caseload=5),
    SyntheticOfficer("SYNTH-OFFCR-01", "[SIMULATED] R. K. Singh", AssigneeRole.CASE_OFFICER, "Patna", active_caseload=3),
    SyntheticOfficer("SYNTH-DSGNT-01", "[SIMULATED] Insp. M. Rathore", AssigneeRole.DESIGNATED_OFFICER, "Patna", active_caseload=1),
    SyntheticOfficer("SYNTH-DISTA-01", "[SIMULATED] Dist. Magistrate Desk", AssigneeRole.DISTRICT_AUTHORITY, "Patna", active_caseload=0),

    SyntheticOfficer("SYNTH-COUNS-03", "[SIMULATED] N. Joshi", AssigneeRole.COUNSELLOR, "Ahmedabad", active_caseload=1),
    SyntheticOfficer("SYNTH-OFFCR-02", "[SIMULATED] P. Patel", AssigneeRole.CASE_OFFICER, "Ahmedabad", active_caseload=2),
    SyntheticOfficer("SYNTH-DSGNT-02", "[SIMULATED] Insp. V. Solanki", AssigneeRole.DESIGNATED_OFFICER, "Ahmedabad", active_caseload=0),
    SyntheticOfficer("SYNTH-DISTA-02", "[SIMULATED] Dist. Magistrate Desk", AssigneeRole.DISTRICT_AUTHORITY, "Ahmedabad", active_caseload=0),
]


class AssignmentRouter:
    """
    Allocates an intervention to an appropriate role, district officer, and backup.
    """

    def __init__(self, officers: Optional[List[SyntheticOfficer]] = None) -> None:
        self.officers = officers if officers is not None else list(DEMO_OFFICER_REGISTRY)

    def determine_target_role(
        self,
        intervention_type: InterventionType,
        priority: PriorityLevel
    ) -> AssigneeRole:
        """
        Determines the appropriate operational role based on the recommended intervention.
        """
        if intervention_type == InterventionType.PRIORITY_HUMAN_REVIEW:
            if priority == PriorityLevel.URGENT:
                return AssigneeRole.DESIGNATED_OFFICER
            return AssigneeRole.COUNSELLOR

        elif intervention_type == InterventionType.HUMAN_FOLLOW_UP:
            return AssigneeRole.COUNSELLOR

        elif intervention_type in (InterventionType.ROUTINE_MONITORING, InterventionType.CONTINUE_MONITORING):
            return AssigneeRole.CASE_OFFICER

        return AssigneeRole.CASE_OFFICER

    def route(
        self,
        case_id: str,
        district: str,
        intervention_type: InterventionType,
        priority: PriorityLevel,
    ) -> RoutingResult:
        """
        Performs capacity-informed district assignment.
        """
        target_role = self.determine_target_role(intervention_type, priority)

        # 1. Match available officers in the target district with matching role
        candidates = [
            o for o in self.officers
            if o.district.lower() == district.lower()
            and o.role == target_role
            and o.is_available
        ]

        # 2. If no exact match in district, fall back to any available officer of that role
        if not candidates:
            candidates = [
                o for o in self.officers
                if o.role == target_role and o.is_available
            ]

        # 3. If still no candidates, fall back to District Authority desk
        if not candidates:
            primary = f"[SIMULATED] Regional Escalation Authority ({district})"
            backup = None
            notes = "No available officers found; routed directly to regional authority."
            return RoutingResult(
                case_id=case_id,
                assigned_role=target_role,
                primary_assignee=primary,
                backup_assignee=backup,
                district=district,
                notes=notes,
            )

        # 4. Capacity-aware sort: assign to officer with lowest current caseload
        sorted_candidates = sorted(candidates, key=lambda c: c.active_caseload)
        primary_officer = sorted_candidates[0]

        # 5. Select backup assignee (especially critical for URGENT / HIGH priority)
        backup_officer = None
        if len(sorted_candidates) > 1:
            backup_officer = sorted_candidates[1].official_id
        else:
            # Fall back to supervisory role in district
            supervisors = [
                o for o in self.officers
                if o.district.lower() == district.lower()
                and o.role == AssigneeRole.DISTRICT_AUTHORITY
            ]
            if supervisors:
                backup_officer = supervisors[0].official_id

        # Update local simulated load
        primary_officer.active_caseload += 1

        return RoutingResult(
            case_id=case_id,
            assigned_role=target_role,
            primary_assignee=primary_officer.official_id,
            backup_assignee=backup_officer,
            district=district,
            notes=f"Routed to {primary_officer.name} (caseload: {primary_officer.active_caseload})",
        )
