"""
AAROH — Operational Assignment & Routing Engine
Author: Preet

Implements strictly district-aware, role-based, capacity-informed routing with
primary and backup assignee failover logic.
Cross-district routing is strictly prohibited to preserve case jurisdiction.
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


class RoutingStatus(str, Enum):
    ASSIGNED = "ASSIGNED"
    ROUTING_UNAVAILABLE = "ROUTING_UNAVAILABLE"
    MISSING_JURISDICTION = "MISSING_JURISDICTION"
    INVALID_JURISDICTION = "MISSING_JURISDICTION"  # Backwards-compatible alias


@dataclass
class SyntheticOfficer:
    official_id: str
    name: str
    role: AssigneeRole
    district: str
    active_caseload: int = 0
    max_capacity: int = 10
    is_available: bool = True


@dataclass
class RoutingResult:
    case_id: str
    assigned_role: Optional[AssigneeRole]
    primary_assignee: Optional[str]
    backup_assignee: Optional[str]
    district: Optional[str]
    status: RoutingStatus = RoutingStatus.ASSIGNED
    assigned_at: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None
    capacity_flag: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "assigned_role": self.assigned_role.value if self.assigned_role else None,
            "primary_assignee": self.primary_assignee,
            "backup_assignee": self.backup_assignee,
            "district": self.district,
            "status": self.status.value,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "notes": self.notes,
            "capacity_flag": self.capacity_flag,
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

    # Synthetic Urban District (Demo PostgreSQL Database)
    SyntheticOfficer("SYNTH-URBAN-DSGNT", "[SIMULATED] Insp. R. Sharma", AssigneeRole.DESIGNATED_OFFICER, "Synthetic Urban District", active_caseload=1),
    SyntheticOfficer("SYNTH-URBAN-COUNS", "[SIMULATED] Dr. P. Mehta", AssigneeRole.COUNSELLOR, "Synthetic Urban District", active_caseload=2),
    SyntheticOfficer("SYNTH-URBAN-OFFCR", "[SIMULATED] Officer K. Nair", AssigneeRole.CASE_OFFICER, "Synthetic Urban District", active_caseload=2),
    SyntheticOfficer("SYNTH-URBAN-DISTA", "[SIMULATED] Urban Magistrate Desk", AssigneeRole.DISTRICT_AUTHORITY, "Synthetic Urban District", active_caseload=0),

    # Synthetic Rural District (Demo PostgreSQL Database)
    SyntheticOfficer("SYNTH-RURAL-DSGNT", "[SIMULATED] Insp. S. Yadav", AssigneeRole.DESIGNATED_OFFICER, "Synthetic Rural District", active_caseload=1),
    SyntheticOfficer("SYNTH-RURAL-COUNS", "[SIMULATED] Dr. A. Das", AssigneeRole.COUNSELLOR, "Synthetic Rural District", active_caseload=2),
    SyntheticOfficer("SYNTH-RURAL-OFFCR", "[SIMULATED] Officer M. Gowda", AssigneeRole.CASE_OFFICER, "Synthetic Rural District", active_caseload=3),
    SyntheticOfficer("SYNTH-RURAL-DISTA", "[SIMULATED] Rural Magistrate Desk", AssigneeRole.DISTRICT_AUTHORITY, "Synthetic Rural District", active_caseload=0),
]


class AssignmentRouter:
    """
    Allocates an intervention to an appropriate role, district officer, and backup.
    Strictly preserves district boundaries. Never cross-routes cases across jurisdictions.
    """

    def __init__(self, officers: Optional[List[SyntheticOfficer]] = None) -> None:
        self.officers = officers if officers is not None else [
            SyntheticOfficer(
                official_id=o.official_id,
                name=o.name,
                role=o.role,
                district=o.district,
                active_caseload=o.active_caseload,
                max_capacity=o.max_capacity,
                is_available=o.is_available,
            )
            for o in DEMO_OFFICER_REGISTRY
        ]

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
        district: Optional[str],
        intervention_type: InterventionType,
        priority: PriorityLevel,
    ) -> RoutingResult:
        """
        Performs strictly district-aware, capacity-informed assignment.
        Never cross-routes across districts.
        """
        # 1. Authoritative jurisdiction check: missing district must be handled explicitly
        if not district or not isinstance(district, str) or not district.strip():
            return RoutingResult(
                case_id=case_id,
                assigned_role=None,
                primary_assignee=None,
                backup_assignee=None,
                district=None,
                status=RoutingStatus.MISSING_JURISDICTION,
                assigned_at=None,
                notes="Missing or invalid district jurisdiction; cannot route without authoritative case district.",
                capacity_flag=False,
            )

        clean_district = district.strip()
        target_role = self.determine_target_role(intervention_type, priority)

        # 2. Strict district filtering: match officers ONLY within the same district
        candidates = [
            o for o in self.officers
            if o.district.strip().lower() == clean_district.lower()
            and o.role == target_role
            and o.is_available
            and o.active_caseload < o.max_capacity
        ]

        # 3. If no eligible officer in district, leave unassigned and flag capacity. Never cross-route.
        if not candidates:
            return RoutingResult(
                case_id=case_id,
                assigned_role=target_role,
                primary_assignee=None,
                backup_assignee=None,
                district=clean_district,
                status=RoutingStatus.ROUTING_UNAVAILABLE,
                assigned_at=None,
                notes=f"ROUTING_UNAVAILABLE: No eligible local {target_role.value} with available capacity found in {clean_district}.",
                capacity_flag=True,
            )

        # 4. Deterministic tie-breaking:
        # Sort by: (1) lowest active caseload, (2) stable alphabetical official_id
        sorted_candidates = sorted(candidates, key=lambda c: (c.active_caseload, c.official_id))
        primary_officer = sorted_candidates[0]

        # 5. Backup assignee selection strictly within the same district
        backup_officer_id: Optional[str] = None
        if len(sorted_candidates) > 1:
            backup_officer_id = sorted_candidates[1].official_id
        else:
            # Fallback to local supervisory authority in the SAME district
            supervisors = [
                o for o in self.officers
                if o.district.strip().lower() == clean_district.lower()
                and o.role == AssigneeRole.DISTRICT_AUTHORITY
                and o.is_available
                and o.active_caseload < o.max_capacity
            ]
            if supervisors:
                sorted_supervisors = sorted(supervisors, key=lambda c: (c.active_caseload, c.official_id))
                backup_officer_id = sorted_supervisors[0].official_id

        # Update caseload for primary
        primary_officer.active_caseload += 1

        return RoutingResult(
            case_id=case_id,
            assigned_role=target_role,
            primary_assignee=primary_officer.official_id,
            backup_assignee=backup_officer_id,
            district=clean_district,
            status=RoutingStatus.ASSIGNED,
            notes=f"Assigned to {primary_officer.name} (caseload: {primary_officer.active_caseload}) in {clean_district}.",
        )
