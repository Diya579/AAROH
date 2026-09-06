"""
AAROH — Operational Intervention & Analytics Integration Service
Author: Preet

Exposes clean, business-ready service methods for:
1. Intervention Decision Evaluation (ML output consumption, uncertainty routing, consent)
2. Assignment & District-Aware Routing (strict isolation, capacity flags, deterministic tie-breaking)
3. SLA Computation & Tracking (UTC standardization, overdue detection, separate status)
4. Outcome Recording & State Machine Transitions (valid transitions, non-causal closed-loop feedback)
5. Multi-Tier Analytics (Case, District, State, National with K<3 privacy suppression and numerator/denominator rollup)

FastAPI endpoints and Frontend dashboards consume these business-ready methods directly
without implementing domain or business logic.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Union

from .engine import (
    InterventionDecision,
    InterventionEngine,
    InterventionReason,
    InterventionStatus,
    InterventionType,
    PriorityLevel,
    InterventionCategory,
)
from .outcomes import (
    ClosedLoopObservation,
    OutcomeManager,
    OutcomeRecord,
    OutcomeType,
    VALID_STATUS_TRANSITIONS,
)
from .prioritization import (
    calculate_priority,
    compute_case_urgency_score,
    rank_intervention_queue,
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
    SLACalculator,
    SLAManager,
    SLARecord,
    SLARule,
    SLAStatus,
    DEFAULT_SLA_RULES,
    ensure_utc,
)

# Relative/absolute import fallback to support both standalone day2 and backend package
try:
    from backend.analytics.case_metrics import CaseMetricsCalculator, CaseSummaryMetrics
    from backend.analytics.district_metrics import (
        DistrictMetricsCalculator,
        DistrictSummaryMetrics,
        mask_small_cell,
    )
    from backend.analytics.state_metrics import StateMetricsCalculator, StateSummaryMetrics
    from backend.analytics.national_metrics import NationalMetricsCalculator, NationalSummaryMetrics
except ImportError:
    from analytics.case_metrics import CaseMetricsCalculator, CaseSummaryMetrics
    from analytics.district_metrics import (
        DistrictMetricsCalculator,
        DistrictSummaryMetrics,
        mask_small_cell,
    )
    from analytics.state_metrics import StateMetricsCalculator, StateSummaryMetrics
    from analytics.national_metrics import NationalMetricsCalculator, NationalSummaryMetrics


class OperationalInterventionService:
    """
    Unified operational service for AAROH intervention, routing, SLA, and analytics.
    """

    def __init__(
        self,
        engine: Optional[InterventionEngine] = None,
        router: Optional[AssignmentRouter] = None,
    ) -> None:
        self.engine = engine or InterventionEngine()
        self.router = router or AssignmentRouter()

    # -------------------------------------------------------------------------
    # 1. INTERVENTION EVALUATION (ML -> Intervention)
    # -------------------------------------------------------------------------
    def evaluate_intervention(
        self,
        case_id: str,
        risk_level: str,
        escalation_probability: float,
        trajectory: str,
        confidence: float = 1.0,
        factors: Optional[Sequence[str]] = None,
        monitoring_consent: bool = True,
        text_analysis_consent: bool = True,
        voice_analysis_consent: bool = True,
        case_linkage_consent: bool = True,
        ml_status: str = "SUCCESS",
        active_interventions: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates upstream ML signals and operational constraints.
        - Consumes ML prediction output as-is without recalculating risk/probability.
        - LOW_CONFIDENCE, ABSTAINED, and INSUFFICIENT_DATA route to PRIORITY_HUMAN_REVIEW (HIGH priority).
        - Absences of monitoring_consent blocks automated intervention.
        """
        decision = self.engine.evaluate(
            case_id=case_id,
            risk_level=risk_level,
            escalation_probability=escalation_probability,
            trajectory=trajectory,
            confidence=confidence,
            factors=factors,
            monitoring_consent=monitoring_consent,
            text_analysis_consent=text_analysis_consent,
            voice_analysis_consent=voice_analysis_consent,
            case_linkage_consent=case_linkage_consent,
            ml_status=ml_status,
            active_interventions=active_interventions,
        )
        return decision.to_dict()

    # -------------------------------------------------------------------------
    # 2. ASSIGNMENT & DISTRICT ROUTING
    # -------------------------------------------------------------------------
    def assign_intervention(
        self,
        case_id: str,
        district: Optional[str],
        intervention_type: Union[InterventionType, str],
        priority: Union[PriorityLevel, str],
        officers: Optional[List[SyntheticOfficer]] = None,
    ) -> Dict[str, Any]:
        """
        Assigns case to local district officer and backup.
        - NEVER allows cross-district assignment.
        - Primary and backup must belong to the target district.
        - If no valid officer exists, leaves unassigned (primary_assignee=None) and flags capacity (capacity_flag=True).
        - Missing or invalid district returns MISSING_JURISDICTION.
        """
        router = AssignmentRouter(officers=officers) if officers is not None else self.router

        itype = (
            intervention_type
            if isinstance(intervention_type, InterventionType)
            else InterventionType(str(intervention_type))
        )
        prio = (
            priority
            if isinstance(priority, PriorityLevel)
            else PriorityLevel(str(priority))
        )

        result = router.route(
            case_id=case_id,
            district=district,
            intervention_type=itype,
            priority=prio,
        )
        return result.to_dict()

    # -------------------------------------------------------------------------
    # 3. SLA COMPUTATION & OVERDUE TRACKING
    # -------------------------------------------------------------------------
    def calculate_sla(
        self,
        intervention_id: int,
        priority: Union[PriorityLevel, str],
        created_at: Union[datetime, str],
        completed_at: Optional[Union[datetime, str]] = None,
        assigned_at: Optional[Union[datetime, str]] = None,
        acknowledged_at: Optional[Union[datetime, str]] = None,
        current_time: Optional[Union[datetime, str]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates SLA deadlines, overdue status, and compliance.
        - SLA Windows: URGENT 4h, HIGH 24h, ROUTINE 72h, LOW 120h.
        - Uses UTC-aware datetimes consistently.
        - Keeps intervention workflow status separate from SLA compliance status.
        - Completed interventions maintain MET or BREACHED and are never actively overdue.
        """
        prio = priority if isinstance(priority, PriorityLevel) else PriorityLevel(str(priority))

        def _to_utc(val: Optional[Union[datetime, str]]) -> Optional[datetime]:
            if val is None:
                return None
            if isinstance(val, str):
                dt = datetime.fromisoformat(val)
            else:
                dt = val
            return ensure_utc(dt)

        c_at = _to_utc(created_at) or datetime.now(timezone.utc)
        comp_at = _to_utc(completed_at)
        as_at = _to_utc(assigned_at)
        ak_at = _to_utc(acknowledged_at)
        now_dt = _to_utc(current_time) or datetime.now(timezone.utc)

        sla_mgr = SLAManager()
        record = sla_mgr.create_record(
            intervention_id=intervention_id,
            priority=prio,
            start_time=c_at,
            assigned_at=as_at,
        )
        record.completed_at = comp_at
        record.acknowledged_at = ak_at

        sla_status = record.evaluate_status(current_time=now_dt)
        is_overdue = record.is_overdue(current_time=now_dt)
        response_time = record.response_time_hours()
        resolution_time = record.resolution_time_hours()
        if response_time is None and record.completed_at is not None:
            response_time = resolution_time

        return {
            "intervention_id": intervention_id,
            "priority": prio.value,
            "created_at": record.created_at.isoformat(),
            "due_at": record.due_at.isoformat(),
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "sla_status": sla_status.value,
            "is_overdue": is_overdue,
            "response_time_hours": response_time,
            "resolution_time_hours": resolution_time,
        }

    # -------------------------------------------------------------------------
    # 4. OUTCOMES & CLOSED-LOOP TRACKING
    # -------------------------------------------------------------------------
    def record_outcome(
        self,
        case_id: str,
        intervention_id: int,
        outcome_type: Union[OutcomeType, str],
        current_status: Union[InterventionStatus, str],
        new_status: Union[InterventionStatus, str],
        completed: bool = True,
        follow_up_required: bool = False,
        notes: Optional[str] = None,
        recorded_at: Optional[Union[datetime, str]] = None,
        pre_distress_score: Optional[float] = None,
        pre_trajectory: Optional[str] = None,
        post_distress_score: Optional[float] = None,
        post_trajectory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validates state machine transitions, records outcomes, and tracks closed-loop distress shifts.
        - Enforces valid status transitions (raises ValueError on invalid transition).
        - Reports only improvement/deterioration/stable association; never claims causation.
        """
        curr = (
            current_status
            if isinstance(current_status, InterventionStatus)
            else InterventionStatus(str(current_status))
        )
        nxt = (
            new_status
            if isinstance(new_status, InterventionStatus)
            else InterventionStatus(str(new_status))
        )
        out_t = (
            outcome_type
            if isinstance(outcome_type, OutcomeType)
            else OutcomeType(str(outcome_type))
        )

        # Enforce valid state machine transition
        OutcomeManager.transition_status(curr, nxt)

        rec_time: datetime
        if recorded_at is None:
            rec_time = datetime.now(timezone.utc)
        elif isinstance(recorded_at, str):
            rec_time = ensure_utc(datetime.fromisoformat(recorded_at)) or datetime.now(timezone.utc)
        else:
            rec_time = ensure_utc(recorded_at) or datetime.now(timezone.utc)

        outcome_rec = OutcomeRecord(
            case_id=case_id,
            intervention_id=intervention_id,
            outcome_type=out_t,
            completed=completed,
            follow_up_required=follow_up_required,
            notes=notes,
            recorded_at=rec_time,
        )

        closed_loop_data: Optional[Dict[str, Any]] = None
        if pre_distress_score is not None and pre_trajectory is not None:
            cl = ClosedLoopObservation(
                case_id=case_id,
                intervention_id=intervention_id,
                outcome_type=out_t,
                pre_distress_score=pre_distress_score,
                pre_trajectory=pre_trajectory,
            )
            if post_distress_score is not None and post_trajectory is not None:
                cl.evaluate_shift(post_distress_score, post_trajectory)
            closed_loop_data = cl.to_dict()

        return {
            "status_transition": {
                "previous_status": curr.value,
                "new_status": nxt.value,
                "transition_valid": True,
            },
            "outcome": outcome_rec.to_dict(),
            "closed_loop_observation": closed_loop_data,
        }

    # -------------------------------------------------------------------------
    # 5. CASE ANALYTICS
    # -------------------------------------------------------------------------
    def get_case_analytics(
        self,
        case_id: str,
        distress_score: float,
        trajectory: str,
        escalation_prob: float,
        risk_level: str,
        confidence: float,
        interventions: Optional[List[Dict[str, Any]]] = None,
        outcomes: Optional[List[Dict[str, Any]]] = None,
        last_interaction_date: Optional[Union[datetime, str]] = None,
    ) -> Dict[str, Any]:
        """
        Computes case longitudinal metrics.
        - Latest outcome selection strictly uses MAX(recorded_at) timestamp.
        """
        last_dt: Optional[datetime] = None
        if last_interaction_date is not None:
            if isinstance(last_interaction_date, str):
                last_dt = ensure_utc(datetime.fromisoformat(last_interaction_date))
            else:
                last_dt = ensure_utc(last_interaction_date)

        summary = CaseMetricsCalculator.calculate(
            case_id=case_id,
            distress_score=distress_score,
            trajectory=trajectory,
            escalation_prob=escalation_prob,
            risk_level=risk_level,
            confidence=confidence,
            interventions=interventions,
            outcomes=outcomes,
            last_interaction_date=last_dt,
        )
        return summary.to_dict()

    # -------------------------------------------------------------------------
    # 6. DISTRICT ANALYTICS
    # -------------------------------------------------------------------------
    def get_district_analytics(
        self,
        district: str,
        case_records: List[Dict[str, Any]],
        intervention_records: List[Dict[str, Any]],
        outcome_records: List[Dict[str, Any]],
        suppress_small_cells: bool = True,
    ) -> Dict[str, Any]:
        """
        Computes district aggregate metrics.
        - Enforces K<3 privacy suppression on sensitive breakdown counts.
        """
        summary = DistrictMetricsCalculator.calculate(
            district=district,
            case_records=case_records,
            intervention_records=intervention_records,
            outcome_records=outcome_records,
        )
        return summary.to_dict(suppress_small_cells=suppress_small_cells)

    # -------------------------------------------------------------------------
    # 7. STATE ANALYTICS
    # -------------------------------------------------------------------------
    def get_state_analytics(
        self,
        state: str,
        district_summaries: List[Union[DistrictSummaryMetrics, Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Computes state-level metrics by rolling up district totals.
        - Aggregates state metrics using raw totals (numerators and denominators first),
          never averages of district percentages.
        """
        parsed_districts: List[DistrictSummaryMetrics] = []
        for d in district_summaries:
            if isinstance(d, DistrictSummaryMetrics):
                parsed_districts.append(d)
            elif isinstance(d, dict):
                perf = d.get("performance", {})
                workload = d.get("intervention_workload", {})
                risk_d = d.get("risk_distribution", {})
                traj_d = d.get("trajectory_alerts", {})
                out_d = d.get("outcome_distribution", {})

                def _val(v: Any) -> int:
                    if v == "<3" or v is None:
                        return 1
                    try:
                        return int(v)
                    except (ValueError, TypeError):
                        return 0

                parsed_districts.append(
                    DistrictSummaryMetrics(
                        district=d.get("district", "Unknown"),
                        total_monitored_cases=int(d.get("total_monitored_cases", 0)),
                        high_risk_cases=_val(risk_d.get("HIGH", 0)),
                        moderate_risk_cases=_val(risk_d.get("MODERATE", 0)),
                        low_risk_cases=_val(risk_d.get("LOW", 0)),
                        rapidly_worsening_cases=_val(traj_d.get("RAPIDLY_WORSENING", 0)),
                        worsening_cases=_val(traj_d.get("WORSENING", 0)),
                        pending_interventions=int(workload.get("pending", 0)),
                        overdue_interventions=int(workload.get("overdue", 0)),
                        completed_interventions=int(workload.get("completed", 0)),
                        met_sla_interventions=int(d.get("met_sla_interventions", 0)),
                        evaluated_sla_interventions=int(d.get("evaluated_sla_interventions", 0)),
                        total_response_time_sum_hours=float(d.get("total_response_time_sum_hours", 0.0)),
                        total_responded_interventions=int(d.get("total_responded_interventions", 0)),
                        avg_response_time_hours=perf.get("avg_response_time_hours"),
                        sla_compliance_rate=perf.get("sla_compliance_rate"),
                        outcome_distribution={k: _val(v) for k, v in out_d.items()},
                    )
                )

        state_summary = StateMetricsCalculator.calculate(
            state=state,
            districts=parsed_districts,
        )
        return state_summary.to_dict()

    # -------------------------------------------------------------------------
    # 8. NATIONAL ANALYTICS
    # -------------------------------------------------------------------------
    def get_national_analytics(
        self,
        state_summaries: List[Union[StateSummaryMetrics, Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Aggregates national metrics soundly across all states using raw totals.
        """
        parsed_states: List[StateSummaryMetrics] = []
        for s in state_summaries:
            if isinstance(s, StateSummaryMetrics):
                parsed_states.append(s)
            elif isinstance(s, dict):
                perf = s.get("performance", {})
                workload = s.get("intervention_workload", {})
                risk_d = s.get("risk_distribution", {})

                parsed_states.append(
                    StateSummaryMetrics(
                        state=s.get("state", "Unknown"),
                        total_districts=int(s.get("total_districts", 0)),
                        total_monitored_cases=int(s.get("total_monitored_cases", 0)),
                        total_high_risk=int(risk_d.get("HIGH", 0)),
                        total_moderate_risk=int(risk_d.get("MODERATE", 0)),
                        total_low_risk=int(risk_d.get("LOW", 0)),
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

        national_summary = NationalMetricsCalculator.calculate(states=parsed_states)
        return national_summary.to_dict()


# Default singleton instance for direct import
intervention_service = OperationalInterventionService()
