"""
AAROH — Database-Integrated Operational Workflow Service
Author: Preet

Directly orchestrates the end-to-end operational pipeline against PostgreSQL:
Prediction -> Risk/Priority -> Intervention -> Routing -> SLA -> Human Action -> Outcome -> Re-monitoring -> Analytics

Enforces:
- Direct PostgreSQL integration using existing models (Case, Prediction, Consent, DistressState, Intervention, Outcome).
- As-is ML prediction consumption (no recalculation of probability or risk).
- Safety gating: low-confidence/abstention routes to PRIORITY_HUMAN_REVIEW (HIGH priority), never LOW_RISK.
- Strict district isolation (no cross-district routing, no invented capacity).
- Finite state machine transitions (PENDING -> ASSIGNED -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED, ESCALATED).
- SLA deadlines (URGENT 4h, HIGH 24h, ROUTINE 72h, LOW 120h) in UTC.
- Outcome vocabulary and latest outcome resolution via MAX(recorded_at).
- Non-causal closed-loop distress tracking.
- Role-appropriate notifications without victim leakage.
- RBAC-aware multi-tier analytics with K<3 small-cell privacy suppression.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Union
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from backend.models import (
    Case,
    CaseEvent,
    Prediction,
    Consent,
    DistressState,
    Intervention,
    Outcome,
    Notification,
    TextFeature,
    Interaction,
)
from .engine import (
    InterventionDecision,
    InterventionEngine,
    InterventionReason,
    InterventionStatus,
    InterventionType,
    PriorityLevel,
    InterventionCategory,
)
from .routing import (
    AssigneeRole,
    AssignmentRouter,
    RoutingResult,
    RoutingStatus,
    SyntheticOfficer,
    DEMO_OFFICER_REGISTRY,
)
from .sla import (
    SLAManager,
    SLARecord,
    SLAStatus,
    DEFAULT_SLA_RULES,
    ensure_utc,
)
from .outcomes import (
    OutcomeManager,
    OutcomeType,
    OutcomeRecord,
    ClosedLoopObservation,
    VALID_STATUS_TRANSITIONS,
)
from .notifications import (
    notification_service,
    NotificationRecipientRole,
    NotificationType,
)
from backend.analytics.case_metrics import CaseMetricsCalculator, CaseSummaryMetrics
from backend.analytics.district_metrics import (
    DistrictMetricsCalculator,
    DistrictSummaryMetrics,
)
from backend.analytics.state_metrics import StateMetricsCalculator, StateSummaryMetrics
from backend.analytics.national_metrics import NationalMetricsCalculator, NationalSummaryMetrics


class DatabaseOperationalService:
    """
    Executes operational workflows directly against PostgreSQL databases.
    """

    def __init__(
        self,
        engine: Optional[InterventionEngine] = None,
        router: Optional[AssignmentRouter] = None,
        sla_manager: Optional[SLAManager] = None,
    ) -> None:
        self.engine = engine or InterventionEngine()
        self.router = router or AssignmentRouter()
        self.sla_manager = sla_manager or SLAManager()

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------------------------------
    def _acquire_session(self, db: Optional[Session]) -> tuple[Session, bool]:
        if db is not None:
            return db, False
        import os
        from backend.database import SessionLocal, engine
        if "sqlite" in str(engine.url):
            pg_url = os.environ.get("DATABASE_URL")
            if not pg_url or "sqlite" in pg_url:
                pg_url = "postgresql://postgres:root@localhost:5432/aaroh_db"
            try:
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                pg_engine = create_engine(pg_url, pool_pre_ping=True)
                PgSession = sessionmaker(bind=pg_engine, autocommit=False, autoflush=False)
                return PgSession(), True
            except Exception:
                return SessionLocal(), True
        return SessionLocal(), True

    def _get_case(self, db: Session, case_id: int | str) -> Case:
        """
        Flexible case lookup supporting integer primary key, case string id (e.g. 'AAROH-001'),
        or stringified integer (e.g. '1').
        """
        case = None
        if isinstance(case_id, int):
            case = db.query(Case).filter(Case.id == case_id).first()
        elif isinstance(case_id, str):
            case = db.query(Case).filter(Case.case_id == case_id).first()
            if not case and case_id.isdigit():
                case = db.query(Case).filter(Case.id == int(case_id)).first()
        if not case:
            raise ValueError(f"Case '{case_id}' not found in database.")
        return case

    # -------------------------------------------------------------------------
    # 1. PROCESS CASE INTERVENTION (Prediction -> Risk/Priority -> Routing -> SLA)
    # -------------------------------------------------------------------------
    def process_case_intervention(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        custom_router: Optional[AssignmentRouter] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Loads case records from PostgreSQL and creates an operational intervention:
        - Consumes Prediction and DistressState as-is.
        - Enforces consent gateway and low-confidence/abstention safety.
        - Routes strictly within the case's district (no cross-district).
        - Computes SLA deadline and persists Intervention to PostgreSQL.
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            # 1. Fetch Case (supports int, string, or numeric string)
            case = self._get_case(db, case_id)

            cid_int = case.id
            cid_str = case.case_id

            # 2. Fetch Latest Prediction
            prediction = (
                db.query(Prediction)
                .filter(Prediction.case_id == cid_int)
                .order_by(Prediction.prediction_date.desc(), Prediction.id.desc())
                .first()
            )

            # 3. Fetch Latest DistressState
            distress_state = (
                db.query(DistressState)
                .filter(DistressState.case_id == cid_int)
                .order_by(DistressState.observation_date.desc(), DistressState.id.desc())
                .first()
            )
            trajectory = distress_state.trajectory if distress_state and distress_state.trajectory else "STABLE"
            distress_score = distress_state.distress_score if distress_state and distress_state.distress_score is not None else 0.50

            # 4. Fetch Consent
            consent = (
                db.query(Consent)
                .filter(Consent.case_id == cid_int)
                .order_by(Consent.id.desc())
                .first()
            )
            monitoring_consent = (
                consent.monitoring_consent
                if consent and consent.monitoring_consent is not None
                else bool(case.monitoring_consent)
            )
            text_analysis_consent = bool(consent.text_analysis_consent) if consent and consent.text_analysis_consent is not None else True
            voice_analysis_consent = bool(consent.voice_analysis_consent) if consent and consent.voice_analysis_consent is not None else True
            case_linkage_consent = bool(consent.case_linkage_consent) if consent and consent.case_linkage_consent is not None else True

            # 5. Extract Factors from text features if present
            factors: List[str] = []
            latest_text_feature = (
                db.query(TextFeature)
                .join(Interaction, TextFeature.interaction_id == Interaction.id)
                .filter(Interaction.case_id == cid_int)
                .order_by(TextFeature.id.desc())
                .first()
            )
            if latest_text_feature:
                if latest_text_feature.fear and latest_text_feature.fear >= 0.50:
                    factors.append("acute fear")
                if latest_text_feature.intimidation and latest_text_feature.intimidation >= 0.50:
                    factors.append("severe intimidation")

            # 6. Map ML Outputs via InterventionEngine (as-is consumption)
            # Determine nominal risk_level without altering upstream; handle missing data safely
            ml_status = "SUCCESS"
            if not prediction or prediction.escalation_probability is None or prediction.confidence is None:
                ml_status = "INSUFFICIENT_DATA"
                prob = 0.0
                conf = 0.0
                nominal_risk = "UNKNOWN"
            else:
                prob = float(prediction.escalation_probability)
                conf = float(prediction.confidence)
                if conf < self.engine.min_confidence_threshold:
                    ml_status = "LOW_CONFIDENCE"
                
                # Nominal category for signal matching
                if prob >= 0.75:
                    nominal_risk = "HIGH"
                elif prob >= 0.40:
                    nominal_risk = "MODERATE"
                else:
                    nominal_risk = "LOW"

            # Check existing active interventions in DB to avoid duplicate pending
            existing_interventions = (
                db.query(Intervention)
                .filter(
                    Intervention.case_id == cid_int,
                    Intervention.status.in_(["PENDING", "ASSIGNED", "ACKNOWLEDGED", "IN_PROGRESS", "ROUTING_UNAVAILABLE"]),
                )
                .all()
            )
            active_list = [
                {"intervention_type": i.intervention_type, "status": i.status, "id": i.id}
                for i in existing_interventions
            ]

            decision = self.engine.evaluate(
                case_id=cid_str,
                risk_level=nominal_risk,
                escalation_probability=prob,
                trajectory=trajectory,
                confidence=conf,
                factors=factors,
                monitoring_consent=monitoring_consent,
                text_analysis_consent=text_analysis_consent,
                voice_analysis_consent=voice_analysis_consent,
                case_linkage_consent=case_linkage_consent,
                ml_status=ml_status,
                active_interventions=active_list,
            )

            if decision.is_duplicate:
                return {
                    "id": decision.existing_intervention_id,
                    "intervention_id": decision.existing_intervention_id,
                    "case_id": case.id,
                    "case_string_id": cid_str,
                    "case_ref": cid_str,
                    "intervention_type": decision.intervention_type.value,
                    "priority": decision.priority.value,
                    "status": "PENDING",
                    "assigned_to": None,
                    "backup_assignee": None,
                    "backup_officer": None,
                    "district": case.district,
                    "routing_status": "ROUTING_UNAVAILABLE",
                    "capacity_flag": False,
                    "escalation_probability": prob,
                    "trajectory": trajectory,
                    "is_duplicate": True,
                    "reason": decision.reason.to_dict(),
                    "suggested_categories": [c.value for c in decision.suggested_categories],
                }

            # 7. Route strictly by case district
            router = custom_router or self.router
            routing_res = router.route(
                case_id=cid_str,
                district=case.district,
                intervention_type=decision.intervention_type,
                priority=decision.priority,
            )

            # 8. Compute SLA Deadline (UTC-aware)
            sla_record = self.sla_manager.create_record(
                intervention_id=0,  # Will be updated once persisted
                priority=decision.priority,
                start_time=datetime.now(timezone.utc),
            )

            # 9. Determine Status & Assigned Official
            if routing_res.status == RoutingStatus.ASSIGNED and routing_res.primary_assignee:
                final_status = "ASSIGNED"
                assigned_to = routing_res.primary_assignee
            else:
                # Unassigned status stays PENDING with routing_res preserving routing flags
                final_status = "PENDING"
                assigned_to = None

            # 10. Persist Intervention to PostgreSQL (defensively populates extended columns if present)
            interv_kwargs = {
                "case_id": cid_int,
                "intervention_type": decision.intervention_type.value,
                "status": final_status,
                "assigned_to": assigned_to,
            }
            if hasattr(Intervention, "priority"):
                interv_kwargs["priority"] = decision.priority.value
            if hasattr(Intervention, "reason"):
                interv_kwargs["reason"] = (
                    decision.reason.to_json()
                    if hasattr(decision.reason, "to_json")
                    else str(decision.reason.to_dict())
                )
            if hasattr(Intervention, "assigned_role") and routing_res.assigned_role:
                interv_kwargs["assigned_role"] = (
                    routing_res.assigned_role.value
                    if hasattr(routing_res.assigned_role, "value")
                    else str(routing_res.assigned_role)
                )
            if hasattr(Intervention, "backup_assigned_to"):
                interv_kwargs["backup_assigned_to"] = routing_res.backup_assignee
            if hasattr(Intervention, "assigned_at") and assigned_to:
                interv_kwargs["assigned_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
            if hasattr(Intervention, "due_at") and sla_record:
                interv_kwargs["due_at"] = sla_record.due_at.replace(tzinfo=None)
            if hasattr(Intervention, "created_at"):
                interv_kwargs["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

            new_intervention = Intervention(**interv_kwargs)
            db.add(new_intervention)
            if auto_commit:
                db.commit()
                db.refresh(new_intervention)
            else:
                db.flush()

            # 11. Role-appropriate Notification
            if assigned_to:
                notification_service.notify(
                    recipient_role=NotificationRecipientRole.CASE_OFFICER,
                    recipient_id=assigned_to,
                    notification_type=NotificationType.INTERVENTION_ASSIGNED,
                    title=f"New Intervention Assigned: {cid_str}",
                    message=f"Case {cid_str} assigned ({decision.priority.value} priority). Deadline: {sla_record.due_at.strftime('%Y-%m-%d %H:%M UTC')}.",
                    case_id=cid_str,
                    intervention_id=new_intervention.id,
                    metadata={
                        "priority": decision.priority.value,
                        "due_at": sla_record.due_at.isoformat(),
                        "district": case.district,
                    },
                    db=db,
                    auto_commit=auto_commit,
                )

                # Citizen-safe update for victim (no operational leaks)
                notification_service.notify(
                    recipient_role=NotificationRecipientRole.VICTIM,
                    recipient_id=cid_str,
                    notification_type=NotificationType.SUPPORT_UPDATE,
                    title="AAROH Support Services Update",
                    message="A support officer has been assigned to your case and will follow up with you through your preferred safe communication channel.",
                    case_id=cid_str,
                    intervention_id=new_intervention.id,
                    db=db,
                    auto_commit=auto_commit,
                )

            # High-Risk Case alert for URGENT / HIGH priority interventions
            if decision.priority in (PriorityLevel.HIGH, PriorityLevel.URGENT):
                notification_service.notify(
                    recipient_role=NotificationRecipientRole.DISTRICT_OFFICIAL,
                    recipient_id=assigned_to or f"DISTRICT-{case.district}",
                    notification_type=NotificationType.HIGH_RISK_CASE,
                    title=f"High-Risk Case Alert: {cid_str}",
                    message=f"High-risk intervention '{decision.intervention_type.value}' generated for case {cid_str} (Priority: {decision.priority.value}, Escalation: {round(prob, 2)}). Immediate review required.",
                    case_id=cid_str,
                    intervention_id=new_intervention.id,
                    metadata={
                        "priority": decision.priority.value,
                        "escalation_probability": prob,
                        "district": case.district,
                    },
                    db=db,
                    auto_commit=auto_commit,
                )

            return {
                "id": new_intervention.id,
                "intervention_id": new_intervention.id,
                "case_id": case.id,
                "case_string_id": cid_str,
                "case_ref": cid_str,
                "intervention_type": new_intervention.intervention_type,
                "priority": decision.priority.value,
                "status": new_intervention.status,
                "assigned_to": new_intervention.assigned_to,
                "backup_assignee": routing_res.backup_assignee,
                "backup_officer": routing_res.backup_assignee,
                "district": case.district,
                "routing_status": routing_res.status.value,
                "capacity_flag": routing_res.capacity_flag,
                "sla_due_at": sla_record.due_at.isoformat(),
                "sla_hours": round((sla_record.due_at - sla_record.created_at).total_seconds() / 3600.0, 1),
                "escalation_probability": prob,
                "trajectory": trajectory,
                "reason": decision.reason.to_dict(),
                "suggested_categories": [c.value for c in decision.suggested_categories],
                "is_duplicate": False,
            }
        finally:
            if close_session:
                db.close()

    # -------------------------------------------------------------------------
    # 2. ASSIGNMENT STATE MACHINE TRANSITIONS
    # -------------------------------------------------------------------------
    def transition_status(
        self,
        db: Optional[Session] = None,
        intervention_id: int = None,
        new_status: str = None,
        actor_id: str = None,
        actor_role: str = None,
        actor_district: Optional[str] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Enforces finite state machine transitions:
        PENDING -> ASSIGNED -> ACKNOWLEDGED -> IN_PROGRESS -> COMPLETED (and ESCALATED)
        Raises PermissionError on unauthorized actors.
        Raises ValueError on invalid transition.
        """
        if intervention_id is None or new_status is None or actor_role is None:
            raise ValueError("intervention_id, new_status, and actor_role must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            ALLOWED_OFFICIAL_ROLES = {
                "CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER",
                "DISTRICT_OFFICIAL", "DISTRICT_AUTHORITY", "STATE_OFFICIAL",
                "STATE_AUTHORITY", "NATIONAL_OFFICIAL", "NATIONAL_AUTHORITY",
                "ADMIN", "SYSTEM_SERVICE",
            }
            if not actor_role or actor_role.upper() not in ALLOWED_OFFICIAL_ROLES:
                raise PermissionError(f"Access Denied: Role '{actor_role}' is not authorized to transition interventions.")

            interv = db.query(Intervention).filter(Intervention.id == intervention_id).first()
            if not interv:
                raise ValueError(f"Intervention {intervention_id} not found.")

            # Cross-district check for district-scoped actors
            if actor_district:
                case = db.query(Case).filter(Case.id == interv.case_id).first()
                if case and actor_role.upper() in ("CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER"):
                    if actor_district.strip().lower() != case.district.strip().lower():
                        raise PermissionError(
                            f"Access Denied: Officer from '{actor_district}' cannot modify intervention for case in '{case.district}'."
                        )

            current_enum = InterventionStatus(interv.status)
            new_enum = InterventionStatus(new_status)

            # Validate transition
            OutcomeManager.transition_status(current_enum, new_enum)

            # Update in PostgreSQL
            old_status = interv.status
            interv.status = new_enum.value
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            if new_enum == InterventionStatus.ACKNOWLEDGED and hasattr(interv, "acknowledged_at") and not getattr(interv, "acknowledged_at", None):
                interv.acknowledged_at = now_utc
            elif new_enum == InterventionStatus.COMPLETED and hasattr(interv, "completed_at") and not getattr(interv, "completed_at", None):
                interv.completed_at = now_utc

            if auto_commit:
                db.commit()
                db.refresh(interv)
            else:
                db.flush()

            # Role-appropriate escalation notification
            if new_enum == InterventionStatus.ESCALATED:
                notification_service.notify(
                    recipient_role=NotificationRecipientRole.DISTRICT_AUTHORITY,
                    recipient_id="DISTRICT_SUPERVISOR",
                    notification_type=NotificationType.INTERVENTION_ESCALATED,
                    title=f"Intervention Escalated: Case #{interv.case_id}",
                    message=f"Intervention {interv.id} escalated by {actor_id} ({actor_role}). Immediate supervisory review required.",
                    case_id=str(interv.case_id),
                    intervention_id=interv.id,
                )

            return {
                "id": interv.id,
                "intervention_id": interv.id,
                "case_id": interv.case_id,
                "intervention_type": interv.intervention_type,
                "assigned_to": interv.assigned_to,
                "previous_status": old_status,
                "status": interv.status,
                "current_status": interv.status,
                "actor_id": actor_id,
                "actor_role": actor_role,
            }
        finally:
            if close_session:
                db.close()

    # -------------------------------------------------------------------------
    # 3. OUTCOME RECORDING & SLA EVALUATION
    # -------------------------------------------------------------------------
    def record_outcome(
        self,
        db: Optional[Session] = None,
        case_id: Optional[int | str] = None,
        intervention_id: int = None,
        outcome_type: str = "OTHER",
        completed: bool = True,
        follow_up_required: bool = False,
        notes: Optional[str] = None,
        recorded_at: Optional[datetime] = None,
        officer_id: Optional[str] = None,
        officer_role: Optional[str] = None,
        officer_district: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        actor_district: Optional[str] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Records an outcome in PostgreSQL using the approved vocabulary.
        Transitions intervention to COMPLETED and evaluates SLA compliance.
        Supports case_id as optional (infers from intervention if omitted).
        Raises PermissionError on unauthorized actors.
        Raises ValueError on invalid state machine jumps.
        """
        if intervention_id is None:
            raise ValueError("intervention_id must be provided.")

        effective_role = officer_role or actor_role
        effective_officer_id = officer_id or actor_id
        effective_district = officer_district or actor_district

        db, close_session = self._acquire_session(db)

        try:
            ALLOWED_OFFICIAL_ROLES = {
                "CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER",
                "DISTRICT_OFFICIAL", "DISTRICT_AUTHORITY", "STATE_OFFICIAL",
                "STATE_AUTHORITY", "NATIONAL_OFFICIAL", "NATIONAL_AUTHORITY",
                "ADMIN", "SYSTEM_SERVICE",
            }
            if effective_role and effective_role.upper() not in ALLOWED_OFFICIAL_ROLES:
                raise PermissionError(f"Access Denied: Role '{effective_role}' is not authorized to record outcomes.")

            # Tolerant outcome resolution supporting synonyms and case-insensitivity
            try:
                out_enum = OutcomeType(str(outcome_type).upper())
            except Exception:
                synonym_map = {
                    "REFERRAL_MADE": OutcomeType.REFERRED,
                    "REFERRAL": OutcomeType.REFERRED,
                    "COUNSELLING": OutcomeType.COUNSELLING_PROVIDED,
                    "COUNSELING": OutcomeType.COUNSELLING_PROVIDED,
                    "CONTACT": OutcomeType.CONTACTED,
                    "UNREACHABLE": OutcomeType.UNABLE_TO_CONTACT,
                    "REFUSED": OutcomeType.DECLINED,
                    "SUCCESS": OutcomeType.RESOLVED,
                }
                out_enum = synonym_map.get(str(outcome_type).upper(), OutcomeType.OTHER)

            rec_time = ensure_utc(recorded_at) if recorded_at else datetime.now(timezone.utc)

            # Fetch intervention
            interv = db.query(Intervention).filter(Intervention.id == intervention_id).first()
            if not interv:
                raise ValueError(f"Intervention {intervention_id} not found.")

            # Fetch case
            if case_id is None:
                case = db.query(Case).filter(Case.id == interv.case_id).first()
            else:
                case = self._get_case(db, case_id)
                if case.id != interv.case_id:
                    raise ValueError(f"Intervention {intervention_id} does not belong to case {case_id}.")

            if not case:
                raise ValueError(f"Case associated with intervention {intervention_id} not found.")

            # Cross-district check
            if officer_district and officer_role and officer_role.upper() in ("CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER"):
                if officer_district.strip().lower() != case.district.strip().lower():
                    raise PermissionError(
                        f"Access Denied: Officer from '{officer_district}' cannot record outcome for case in '{case.district}'."
                    )

            # State machine: complete intervention
            if interv.status != InterventionStatus.COMPLETED.value:
                if interv.status == InterventionStatus.PENDING.value:
                    raise ValueError("Invalid status transition: Cannot complete an intervention directly from PENDING status without assignment and progression.")
                OutcomeManager.transition_status(InterventionStatus(interv.status), InterventionStatus.COMPLETED)
                interv.status = InterventionStatus.COMPLETED.value
                if hasattr(interv, "completed_at") and not getattr(interv, "completed_at", None):
                    interv.completed_at = rec_time.replace(tzinfo=None)

            # Create Outcome in PostgreSQL (defensively populates extended columns if present)
            outcome_kwargs = {
                "case_id": case.id,
                "intervention_id": interv.id,
                "outcome_type": out_enum.value,
                "completed": completed,
                "recorded_at": rec_time.replace(tzinfo=None),  # Stored in DB as naive UTC
            }
            if hasattr(Outcome, "follow_up_required"):
                outcome_kwargs["follow_up_required"] = follow_up_required
            if hasattr(Outcome, "notes"):
                outcome_kwargs["notes"] = notes

            outcome = Outcome(**outcome_kwargs)
            db.add(outcome)
            if auto_commit:
                db.commit()
                db.refresh(outcome)
            else:
                db.flush()

            # Notify official
            if interv.assigned_to:
                notification_service.notify(
                    recipient_role=NotificationRecipientRole.CASE_OFFICER,
                    recipient_id=interv.assigned_to,
                    notification_type=NotificationType.OUTCOME_RECORDED,
                    title=f"Outcome Logged: {case.case_id}",
                    message=f"Outcome '{out_enum.value}' recorded for intervention {interv.id}.",
                    case_id=case.case_id,
                    intervention_id=interv.id,
                    outcome_id=outcome.id,
                    db=db,
                    auto_commit=auto_commit,
                )

            # Follow-up required notification if flagged
            if follow_up_required:
                notification_service.notify(
                    recipient_role=NotificationRecipientRole.CASE_OFFICER,
                    recipient_id=interv.assigned_to or f"OFFICER-{case.district}",
                    notification_type=NotificationType.FOLLOW_UP_REQUIRED,
                    title=f"Follow-up Required: {case.case_id}",
                    message=f"Outcome '{out_enum.value}' indicates follow-up monitoring is required for case {case.case_id}. Scheduled follow-up action must be initiated.",
                    case_id=case.case_id,
                    intervention_id=interv.id,
                    outcome_id=outcome.id,
                    db=db,
                    auto_commit=auto_commit,
                )

            # Safe citizen notification for victim (no operational leaks)
            notification_service.notify(
                recipient_role=NotificationRecipientRole.VICTIM,
                recipient_id=case.case_id,
                notification_type=NotificationType.SUPPORT_UPDATE,
                title="Support Services Update",
                message="Your support case check-in has been successfully documented. Contact your case officer if you need further assistance.",
                case_id=case.case_id,
                intervention_id=interv.id,
                outcome_id=outcome.id,
                db=db,
                auto_commit=auto_commit,
            )

            return {
                "id": outcome.id,
                "outcome_id": outcome.id,
                "case_id": case.id,
                "case_string_id": case.case_id,
                "case_ref": case.case_id,
                "intervention_id": interv.id,
                "outcome_type": outcome.outcome_type,
                "completed": outcome.completed,
                "recorded_at": rec_time.isoformat(),
                "intervention_status": interv.status,
                "follow_up_required": follow_up_required,
                "notes": notes,
            }
        finally:
            if close_session:
                db.close()

    # -------------------------------------------------------------------------
    # 3B. FASTAPI QUERY & ASSIGNMENT HELPERS
    # -------------------------------------------------------------------------
    def get_intervention(
        self,
        db: Optional[Session] = None,
        intervention_id: int = None,
    ) -> Dict[str, Any]:
        """
        Retrieves a single intervention by ID with enriched details (case info, outcomes, SLA).
        Directly satisfies GET /api/v1/interventions/{intervention_id}.
        """
        if intervention_id is None:
            raise ValueError("intervention_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            interv = db.query(Intervention).filter(Intervention.id == intervention_id).first()
            if not interv:
                raise ValueError(f"Intervention {intervention_id} not found.")

            case = db.query(Case).filter(Case.id == interv.case_id).first()
            cid_str = case.case_id if case else str(interv.case_id)
            district = case.district if case else None

            # Check for latest outcome
            latest_outcome = (
                db.query(Outcome)
                .filter(Outcome.intervention_id == interv.id)
                .order_by(Outcome.recorded_at.desc(), Outcome.id.desc())
                .first()
            )

            return {
                "id": interv.id,
                "intervention_id": interv.id,
                "case_id": interv.case_id,
                "case_string_id": cid_str,
                "case_ref": cid_str,
                "district": district,
                "intervention_type": interv.intervention_type,
                "status": interv.status,
                "assigned_to": interv.assigned_to,
                "priority": getattr(interv, "priority", None),
                "reason": getattr(interv, "reason", None),
                "assigned_role": getattr(interv, "assigned_role", None),
                "backup_assigned_to": getattr(interv, "backup_assigned_to", None),
                "backup_assignee": getattr(interv, "backup_assigned_to", None),
                "latest_outcome": latest_outcome.outcome_type if latest_outcome else None,
                "completed": latest_outcome.completed if latest_outcome else (interv.status == "COMPLETED"),
                "due_at": getattr(interv, "due_at", None).isoformat() if getattr(interv, "due_at", None) else None,
                "assigned_at": getattr(interv, "assigned_at", None).isoformat() if getattr(interv, "assigned_at", None) else None,
                "acknowledged_at": getattr(interv, "acknowledged_at", None).isoformat() if getattr(interv, "acknowledged_at", None) else None,
                "completed_at": getattr(interv, "completed_at", None).isoformat() if getattr(interv, "completed_at", None) else None,
                "created_at": getattr(interv, "created_at", None).isoformat() if getattr(interv, "created_at", None) else None,
            }
        finally:
            if close_session:
                db.close()

    def get_case_interventions(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all interventions recorded for a case, ordered by id descending.
        Directly satisfies GET /api/v1/cases/{case_id}/interventions.
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)
            interventions = (
                db.query(Intervention)
                .filter(Intervention.case_id == case.id)
                .order_by(Intervention.id.desc())
                .all()
            )
            results = []
            for i in interventions:
                latest_outcome = (
                    db.query(Outcome)
                    .filter(Outcome.intervention_id == i.id)
                    .order_by(Outcome.recorded_at.desc(), Outcome.id.desc())
                    .first()
                )
                results.append({
                    "id": i.id,
                    "intervention_id": i.id,
                    "case_id": case.id,
                    "case_string_id": case.case_id,
                    "case_ref": case.case_id,
                    "district": case.district,
                    "intervention_type": i.intervention_type,
                    "status": i.status,
                    "assigned_to": i.assigned_to,
                    "priority": getattr(i, "priority", None),
                    "reason": getattr(i, "reason", None),
                    "assigned_role": getattr(i, "assigned_role", None),
                    "backup_assigned_to": getattr(i, "backup_assigned_to", None),
                    "backup_assignee": getattr(i, "backup_assigned_to", None),
                    "due_at": getattr(i, "due_at", None).isoformat() if getattr(i, "due_at", None) else None,
                    "assigned_at": getattr(i, "assigned_at", None).isoformat() if getattr(i, "assigned_at", None) else None,
                    "acknowledged_at": getattr(i, "acknowledged_at", None).isoformat() if getattr(i, "acknowledged_at", None) else None,
                    "completed_at": getattr(i, "completed_at", None).isoformat() if getattr(i, "completed_at", None) else None,
                    "created_at": getattr(i, "created_at", None).isoformat() if getattr(i, "created_at", None) else None,
                    "latest_outcome": latest_outcome.outcome_type if latest_outcome else None,
                    "completed": latest_outcome.completed if latest_outcome else (i.status == "COMPLETED"),
                })
            return results
        finally:
            if close_session:
                db.close()

    def assign_intervention(
        self,
        db: Optional[Session] = None,
        intervention_id: int = None,
        assignee_id: str = None,
        actor_id: str = None,
        actor_role: str = None,
        actor_district: Optional[str] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Explicit manual assignment/reassignment of an intervention:
        - Validates actor authorization (supervisors/officials).
        - Enforces district jurisdiction boundaries.
        - Updates assigned_to and transitions status to ASSIGNED.
        - Dispatches assignment notification.
        Directly satisfies POST /api/v1/interventions/{intervention_id}/assign.
        """
        if intervention_id is None or assignee_id is None or actor_role is None:
            raise ValueError("intervention_id, assignee_id, and actor_role must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            ALLOWED_ASSIGN_ROLES = {
                "CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER",
                "DISTRICT_OFFICIAL", "DISTRICT_AUTHORITY", "STATE_OFFICIAL",
                "STATE_AUTHORITY", "NATIONAL_OFFICIAL", "NATIONAL_AUTHORITY",
                "ADMIN", "SYSTEM_SERVICE",
            }
            if actor_role.upper() not in ALLOWED_ASSIGN_ROLES:
                raise PermissionError(f"Access Denied: Role '{actor_role}' cannot assign interventions.")

            interv = db.query(Intervention).filter(Intervention.id == intervention_id).first()
            if not interv:
                raise ValueError(f"Intervention {intervention_id} not found.")

            case = db.query(Case).filter(Case.id == interv.case_id).first()
            if not case:
                raise ValueError(f"Case associated with intervention {intervention_id} not found.")

            # Cross-district check for district-scoped actors
            if actor_district and actor_role.upper() in ("CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER", "DISTRICT_OFFICIAL", "DISTRICT_AUTHORITY"):
                if actor_district.strip().lower() != case.district.strip().lower():
                    raise PermissionError(
                        f"Access Denied: Official from '{actor_district}' cannot assign case in '{case.district}'."
                    )

            old_status = interv.status
            old_assigned = interv.assigned_to
            interv.assigned_to = assignee_id

            if interv.status == InterventionStatus.PENDING.value:
                interv.status = InterventionStatus.ASSIGNED.value
            if hasattr(interv, "assigned_at") and not getattr(interv, "assigned_at", None):
                interv.assigned_at = datetime.now(timezone.utc).replace(tzinfo=None)

            if auto_commit:
                db.commit()
                db.refresh(interv)
            else:
                db.flush()

            # Notify assignee
            notification_service.notify(
                recipient_role=NotificationRecipientRole.CASE_OFFICER,
                recipient_id=assignee_id,
                notification_type=NotificationType.INTERVENTION_ASSIGNED,
                title=f"Intervention Assigned: {case.case_id}",
                message=f"Intervention {interv.id} assigned to you by {actor_id} ({actor_role}).",
                case_id=case.case_id,
                intervention_id=interv.id,
                db=db,
                auto_commit=auto_commit,
            )

            return {
                "id": interv.id,
                "intervention_id": interv.id,
                "case_id": case.id,
                "case_string_id": case.case_id,
                "case_ref": case.case_id,
                "previous_assignee": old_assigned,
                "assigned_to": interv.assigned_to,
                "previous_status": old_status,
                "status": interv.status,
                "district": case.district,
            }
        finally:
            if close_session:
                db.close()

    def check_and_notify_overdue_interventions(
        self,
        db: Optional[Session] = None,
        auto_commit: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Scans active, non-completed interventions for SLA breaches.
        Dispatches INTERVENTION_OVERDUE notifications to assigned officers and district officials,
        and logs SLA_BREACHED events.
        """
        db, close_session = self._acquire_session(db)
        try:
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            active_interventions = (
                db.query(Intervention)
                .filter(
                    Intervention.status.notin_(["COMPLETED", "CANCELLED"]),
                    Intervention.due_at.isnot(None),
                    Intervention.due_at < now_utc,
                )
                .all()
            )

            overdue_list = []
            for interv in active_interventions:
                case = db.query(Case).filter(Case.id == interv.case_id).first()
                cid_str = case.case_id if case else str(interv.case_id)
                district = case.district if case else "Unknown"

                # Log SLA_BREACHED event
                db.add(CaseEvent(
                    case_id=interv.case_id,
                    event_type="SLA_BREACHED",
                    event_date=now_utc,
                    description=f"Intervention {interv.id} ({interv.intervention_type}) breached SLA deadline {interv.due_at.isoformat()}.",
                    case_stage=case.current_stage if case else "MONITORING",
                ))

                # Notify assigned officer
                if interv.assigned_to:
                    notification_service.notify(
                        recipient_role=NotificationRecipientRole.CASE_OFFICER,
                        recipient_id=interv.assigned_to,
                        notification_type=NotificationType.INTERVENTION_OVERDUE,
                        title=f"Intervention Overdue: Case {cid_str}",
                        message=f"Intervention {interv.id} ({interv.intervention_type}) is overdue. Target SLA deadline {interv.due_at.strftime('%Y-%m-%d %H:%M UTC')} was breached.",
                        case_id=cid_str,
                        intervention_id=interv.id,
                        db=db,
                        auto_commit=auto_commit,
                    )

                # Escalate / alert District Official
                notification_service.notify(
                    recipient_role=NotificationRecipientRole.DISTRICT_OFFICIAL,
                    recipient_id=f"DISTRICT-{district}",
                    notification_type=NotificationType.INTERVENTION_OVERDUE,
                    title=f"SLA Breach Escalation: Case {cid_str}",
                    message=f"Intervention {interv.id} in district {district} breached SLA deadline. Immediate supervisor intervention required.",
                    case_id=cid_str,
                    intervention_id=interv.id,
                    db=db,
                    auto_commit=auto_commit,
                )

                overdue_list.append({
                    "intervention_id": interv.id,
                    "case_id": cid_str,
                    "district": district,
                    "due_at": interv.due_at.isoformat(),
                    "status": interv.status,
                    "assigned_to": interv.assigned_to,
                })

            if auto_commit and active_interventions:
                db.commit()

            return overdue_list
        finally:
            if close_session:
                db.close()

    # -------------------------------------------------------------------------
    # 4. CLOSED LOOP (Outcome -> Re-monitoring -> Observed Shift)
    # -------------------------------------------------------------------------
    def record_re_monitoring(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        new_distress_score: float = 0.5,
        new_trajectory: str = "STABLE",
        confidence: float = 1.0,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Records subsequent monitoring observation in PostgreSQL and evaluates
        pre-to-post distress difference strictly as a temporal correlation (never claiming causation).
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)

            # Previous baseline
            previous_state = (
                db.query(DistressState)
                .filter(DistressState.case_id == case.id)
                .order_by(DistressState.observation_date.desc(), DistressState.id.desc())
                .first()
            )
            pre_score = previous_state.distress_score if previous_state and previous_state.distress_score is not None else new_distress_score
            pre_traj = previous_state.trajectory if previous_state and previous_state.trajectory else "STABLE"

            # Insert new observation in PostgreSQL
            new_state = DistressState(
                case_id=case.id,
                observation_date=datetime.now(timezone.utc),
                distress_score=round(new_distress_score, 4),
                trajectory=new_trajectory,
                confidence=round(confidence, 4),
            )
            db.add(new_state)
            if auto_commit:
                db.commit()
                db.refresh(new_state)
            else:
                db.flush()

            # Closed-loop temporal evaluation
            diff = round(new_distress_score - pre_score, 4)
            if diff <= -0.10:
                observed_shift = "SUBSEQUENT_IMPROVEMENT"
            elif diff >= 0.10:
                observed_shift = "SUBSEQUENT_DETERIORATION"
            else:
                observed_shift = "SUBSEQUENT_STABLE"

            return {
                "case_id": case.case_id,
                "new_observation_id": new_state.id,
                "pre_distress_score": pre_score,
                "pre_trajectory": pre_traj,
                "post_distress_score": round(new_distress_score, 4),
                "post_trajectory": new_trajectory,
                "distress_difference": diff,
                "observed_shift": observed_shift,
                "disclaimer": "Observed temporal correlation only. No causal clinical claim.",
            }
        finally:
            if close_session:
                db.close()

    # -------------------------------------------------------------------------
    # 5. RBAC-AWARE MULTI-TIER ANALYTICS
    # -------------------------------------------------------------------------
    def get_rbac_case_analytics(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        user_role: str = None,
        user_district: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Computes case analytics with RBAC check and complete privacy protection:
        - Caseworkers can only access cases in their assigned district.
        - Resolves latest outcome strictly using MAX(recorded_at).
        - NEVER returns raw victim statements, notes, or audio paths.
        """
        if case_id is None or user_role is None:
            raise ValueError("case_id and user_role must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)

            # RBAC Authorization Guard
            role_upper = user_role.upper()
            ALLOWED_ANALYTICS_ROLES = {
                "CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER",
                "DISTRICT_OFFICIAL", "DISTRICT_AUTHORITY", "STATE_OFFICIAL",
                "STATE_AUTHORITY", "NATIONAL_OFFICIAL", "NATIONAL_AUTHORITY",
                "ADMIN", "SYSTEM_SERVICE",
            }
            if role_upper not in ALLOWED_ANALYTICS_ROLES:
                raise PermissionError(f"Access Denied: Role '{user_role}' is not authorized to access case analytics.")

            if role_upper in ("CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER"):
                if not user_district or user_district.strip().lower() != case.district.strip().lower():
                    raise PermissionError(
                        f"Access Denied: Officer assigned to '{user_district}' cannot access case in '{case.district}'."
                    )

            # Fetch latest metrics
            latest_pred = (
                db.query(Prediction)
                .filter(Prediction.case_id == case.id)
                .order_by(Prediction.prediction_date.desc(), Prediction.id.desc())
                .first()
            )
            latest_distress = (
                db.query(DistressState)
                .filter(DistressState.case_id == case.id)
                .order_by(DistressState.observation_date.desc(), DistressState.id.desc())
                .first()
            )

            prob = latest_pred.escalation_probability if latest_pred and latest_pred.escalation_probability is not None else 0.0
            conf = latest_pred.confidence if latest_pred and latest_pred.confidence is not None else 1.0
            score = latest_distress.distress_score if latest_distress and latest_distress.distress_score is not None else 0.50
            traj = latest_distress.trajectory if latest_distress and latest_distress.trajectory else "STABLE"

            risk_level = "HIGH" if prob >= 0.75 else ("MODERATE" if prob >= 0.40 else "LOW")

            # Fetch Interventions & Outcomes
            intervs = db.query(Intervention).filter(Intervention.case_id == case.id).all()
            outs = db.query(Outcome).filter(Outcome.case_id == case.id).all()

            int_records = [
                {
                    "id": i.id,
                    "status": i.status,
                    "intervention_type": i.intervention_type,
                }
                for i in intervs
            ]
            out_records = [
                {
                    "outcome_type": o.outcome_type,
                    "recorded_at": o.recorded_at.replace(tzinfo=timezone.utc) if o.recorded_at else None,
                }
                for o in outs
            ]

            summary = CaseMetricsCalculator.calculate(
                case_id=case.case_id,
                distress_score=score,
                trajectory=traj,
                escalation_prob=prob,
                risk_level=risk_level,
                confidence=conf,
                interventions=int_records,
                outcomes=out_records,
            )
            return summary.to_dict()
        finally:
            if close_session:
                db.close()

    def get_rbac_district_analytics(
        self,
        db: Optional[Session] = None,
        district: str = None,
        user_role: str = None,
        user_district: Optional[str] = None,
        suppress_small_cells: bool = True,
    ) -> Dict[str, Any]:
        """
        Computes aggregate metrics for an administrative district with K<3 privacy suppression.
        RBAC: Caseworkers/District Authorities can only view their assigned district.
        """
        if district is None or user_role is None:
            raise ValueError("district and user_role must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            role_upper = user_role.upper()
            ALLOWED_ANALYTICS_ROLES = {
                "CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER",
                "DISTRICT_OFFICIAL", "DISTRICT_AUTHORITY", "STATE_OFFICIAL",
                "STATE_AUTHORITY", "NATIONAL_OFFICIAL", "NATIONAL_AUTHORITY",
                "ADMIN", "SYSTEM_SERVICE",
            }
            if role_upper not in ALLOWED_ANALYTICS_ROLES:
                raise PermissionError(f"Access Denied: Role '{user_role}' is not authorized to access district analytics.")

            if role_upper in ("CASE_OFFICER", "COUNSELLOR", "DESIGNATED_OFFICER", "DISTRICT_AUTHORITY", "DISTRICT_OFFICIAL"):
                if not user_district or user_district.strip().lower() != district.strip().lower():
                    raise PermissionError(
                        f"Access Denied: Role {user_role} in '{user_district}' cannot access analytics for '{district}'."
                    )

            cases = db.query(Case).filter(Case.district.ilike(district.strip())).all()
            case_ids = [c.id for c in cases]

            case_records = []
            for c in cases:
                pred = (
                    db.query(Prediction)
                    .filter(Prediction.case_id == c.id)
                    .order_by(Prediction.prediction_date.desc(), Prediction.id.desc())
                    .first()
                )
                d_state = (
                    db.query(DistressState)
                    .filter(DistressState.case_id == c.id)
                    .order_by(DistressState.observation_date.desc(), DistressState.id.desc())
                    .first()
                )
                prob = pred.escalation_probability if pred and pred.escalation_probability is not None else 0.0
                r_level = "HIGH" if prob >= 0.75 else ("MODERATE" if prob >= 0.40 else "LOW")
                t_traj = d_state.trajectory if d_state and d_state.trajectory else "STABLE"

                case_records.append({
                    "case_id": c.case_id,
                    "risk_level": r_level,
                    "trajectory": t_traj,
                })

            intervs = db.query(Intervention).filter(Intervention.case_id.in_(case_ids)).all() if case_ids else []
            outs = db.query(Outcome).filter(Outcome.case_id.in_(case_ids)).all() if case_ids else []

            int_records = [
                {"id": i.id, "status": i.status, "is_overdue": False}
                for i in intervs
            ]
            out_records = [
                {"outcome_type": o.outcome_type, "recorded_at": o.recorded_at}
                for o in outs
            ]

            summary = DistrictMetricsCalculator.calculate(
                district=district,
                case_records=case_records,
                intervention_records=int_records,
                outcome_records=out_records,
            )
            return summary.to_dict(suppress_small_cells=suppress_small_cells)
        finally:
            if close_session:
                db.close()

    def get_rbac_state_analytics(
        self,
        db: Optional[Session] = None,
        state: str = None,
        districts: List[str] = None,
        user_role: str = None,
    ) -> Dict[str, Any]:
        """
        Rolls up district summaries into state-level metrics by aggregating
        raw numerators and denominators first.
        RBAC: Requires STATE_AUTHORITY or NATIONAL_AUTHORITY.
        """
        if state is None or districts is None or user_role is None:
            raise ValueError("state, districts, and user_role must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            role_upper = user_role.upper()
            if role_upper not in ("STATE_AUTHORITY", "NATIONAL_AUTHORITY", "ADMIN"):
                raise PermissionError(f"Access Denied: Role {user_role} is unauthorized for state analytics.")

            district_summaries: List[DistrictSummaryMetrics] = []
            for d in districts:
                # Query district metrics without suppression for state rollups
                cases = db.query(Case).filter(Case.district.ilike(d.strip())).all()
                c_ids = [c.id for c in cases]

                c_recs = []
                for c in cases:
                    pred = (
                        db.query(Prediction)
                        .filter(Prediction.case_id == c.id)
                        .order_by(Prediction.prediction_date.desc(), Prediction.id.desc())
                        .first()
                    )
                    d_st = (
                        db.query(DistressState)
                        .filter(DistressState.case_id == c.id)
                        .order_by(DistressState.observation_date.desc(), DistressState.id.desc())
                        .first()
                    )
                    p = pred.escalation_probability if pred and pred.escalation_probability is not None else 0.0
                    c_recs.append({
                        "case_id": c.case_id,
                        "risk_level": "HIGH" if p >= 0.75 else ("MODERATE" if p >= 0.40 else "LOW"),
                        "trajectory": d_st.trajectory if d_st and d_st.trajectory else "STABLE",
                    })

                ints = db.query(Intervention).filter(Intervention.case_id.in_(c_ids)).all() if c_ids else []
                outs = db.query(Outcome).filter(Outcome.case_id.in_(c_ids)).all() if c_ids else []

                d_sum = DistrictMetricsCalculator.calculate(
                    district=d,
                    case_records=c_recs,
                    intervention_records=[{"id": i.id, "status": i.status} for i in ints],
                    outcome_records=[{"outcome_type": o.outcome_type, "recorded_at": o.recorded_at} for o in outs],
                )
                district_summaries.append(d_sum)

            state_summary = StateMetricsCalculator.calculate(state=state, districts=district_summaries)
            return state_summary.to_dict()
        finally:
            if close_session:
                db.close()

    def get_rbac_national_analytics(
        self,
        state_summaries: List[Dict[str, Any]],
        user_role: str,
    ) -> Dict[str, Any]:
        """
        Rolls up state totals into national aggregates.
        RBAC: Requires NATIONAL_AUTHORITY or ADMIN.
        """
        role_upper = user_role.upper()
        if role_upper not in ("NATIONAL_AUTHORITY", "ADMIN"):
            raise PermissionError(f"Access Denied: Role {user_role} is unauthorized for national analytics.")

        # Reconstruct StateSummaryMetrics for sound rollup
        parsed: List[StateSummaryMetrics] = []
        for s in state_summaries:
            perf = s.get("performance", {})
            workload = s.get("intervention_totals", {})
            risk = s.get("risk_totals", {})

            parsed.append(
                StateSummaryMetrics(
                    state=s.get("state", "Unknown"),
                    total_districts=int(s.get("total_districts", 0)),
                    total_monitored_cases=int(s.get("total_monitored_cases", 0)),
                    total_high_risk=int(risk.get("HIGH", 0)),
                    total_moderate_risk=int(risk.get("MODERATE", 0)),
                    total_low_risk=int(risk.get("LOW", 0)),
                    total_pending_interventions=int(workload.get("pending", 0)),
                    total_overdue_interventions=int(workload.get("overdue", 0)),
                    total_completed_interventions=int(workload.get("completed", 0)),
                    total_met_sla_interventions=int(s.get("total_met_sla_interventions", 0)),
                    total_evaluated_sla_interventions=int(s.get("total_evaluated_sla_interventions", 0)),
                    total_response_time_sum_hours=float(s.get("total_response_time_sum_hours", 0.0)),
                    total_responded_interventions=int(s.get("total_responded_interventions", 0)),
                    overall_sla_compliance_rate=perf.get("overall_sla_compliance_rate"),
                    avg_response_time_hours=perf.get("avg_response_time_hours"),
                    district_summaries=s.get("district_comparison", []),
                )
            )

        nat_summary = NationalMetricsCalculator.calculate(states=parsed)
        return nat_summary.to_dict()


# Default singleton instance
db_operational_service = DatabaseOperationalService()
