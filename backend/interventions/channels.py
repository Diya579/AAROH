"""
AAROH — Multi-Channel Intake & Event Lifecycle Service
Author: Preet (Senior Backend Engineer — Intervention, Routing, SLA, Outcomes & Analytics Owner)

Integrates incoming communication channels (IVR, SMS, Chatbot) into AAROH's end-to-end
operational pipeline using the SAME, FROZEN intervention engine:
Channel Intake -> Consent Check -> Interaction/Event Logging -> Prediction -> Intervention -> Routing -> SLA

Supports channel event edge cases:
- PERIODIC: Scheduled routine check-ins.
- MISSED: Check-in window passed without response -> flags human review.
- INCOMPLETE: Call dropped or response aborted -> triggers INSUFFICIENT_DATA safety routing.
- DUPLICATE: Idempotent duplicate event suppression within deduplication window.
- LATE: Interaction received after scheduled SLA window -> evaluates delay and logs SLA breach.
- UNSAFE: Unauthorized channel attempt or distress trigger -> triggers EMERGENCY_ESCALATION or DE_ESCALATION_PROTOCOL.

NON-NEGOTIABLES:
- ML is FROZEN: Consumes prediction models and contracts as-is.
- Zero cross-district routing: Enforces strict district boundaries.
- Uses existing SQLAlchemy PostgreSQL models: Case, Consent, Interaction, CaseEvent, Prediction, DistressState, Intervention.
- All timestamps are UTC-aware.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from backend.models import (
    Case,
    Consent,
    Interaction,
    CaseEvent,
    DistressState,
    Prediction,
    Intervention,
)
from backend.interventions.engine import (
    InterventionDecision,
    InterventionEngine,
    InterventionReason,
    InterventionStatus,
    InterventionType,
    PriorityLevel,
    InterventionCategory,
)
from backend.interventions.routing import AssignmentRouter
from backend.interventions.sla import ensure_utc
from backend.interventions.db_service import db_operational_service


class ChannelType(str, Enum):
    IVR = "IVR"
    SMS = "SMS"
    CHATBOT = "CHATBOT"


class ChannelEventType(str, Enum):
    PERIODIC_CHECK_IN = "PERIODIC_CHECK_IN"
    CHECK_IN_RECEIVED = "CHECK_IN_RECEIVED"
    CHECK_IN_MISSED = "CHECK_IN_MISSED"
    INTERACTION_INCOMPLETE = "INTERACTION_INCOMPLETE"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    LATE_RESPONSE = "LATE_RESPONSE"
    UNSAFE_CHANNEL_DETECTED = "UNSAFE_CHANNEL_DETECTED"


# Emergency panic keywords that immediately trigger unsafe escalation
PANIC_KEYWORDS = {
    "danger", "help", "threat", "kill", "suicide", "emergency",
    "bachao", "khatra", "madad", "mar", "chot", "attack",
}


class ChannelWorkflowService:
    """
    Channel intake orchestration service connecting IVR, SMS, and Chatbot
    to the existing database operational intervention pipeline.
    """

    def __init__(self, deduplication_window_minutes: int = 15) -> None:
        self.deduplication_window = timedelta(minutes=deduplication_window_minutes)
        self.intervention_service = db_operational_service

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
        Robust case lookup supporting:
        1. Integer primary key: Case.id == case_id (e.g. 1)
        2. Alphanumeric Case ID: Case.case_id == case_id (e.g. "AAROH-001")
        3. Stringified integer ID: Case.id == int(case_id) when case_id.isdigit()
        """
        if isinstance(case_id, int):
            case = db.query(Case).filter(Case.id == case_id).first()
        else:
            cid_str = str(case_id).strip()
            case = db.query(Case).filter(Case.case_id == cid_str).first()
            if not case and cid_str.isdigit():
                case = db.query(Case).filter(Case.id == int(cid_str)).first()

        if not case:
            raise ValueError(f"Case '{case_id}' not found in database.")
        return case

    def _get_consent(self, db: Session, case_id: int) -> Optional[Consent]:
        return db.query(Consent).filter(Consent.case_id == case_id).first()

    def _log_event(
        self,
        db: Session,
        case: Case,
        event_type: str,
        description: str,
        event_date: Optional[datetime] = None,
        auto_commit: bool = True,
    ) -> CaseEvent:
        evt_date = ensure_utc(event_date) if event_date else datetime.now(timezone.utc)
        event = CaseEvent(
            case_id=case.id,
            event_date=evt_date.replace(tzinfo=None),
            event_type=event_type,
            description=description,
            case_stage=case.current_stage or "MONITORING",
        )
        db.add(event)
        if auto_commit:
            db.commit()
            db.refresh(event)
        else:
            db.flush()
        return event

    def _is_duplicate_interaction(
        self,
        db: Session,
        case_id: int,
        channel: str,
        text_response: Optional[str],
        now_utc: datetime,
    ) -> Optional[Interaction]:
        """Detects if an identical interaction arrived within the deduplication window."""
        window_start = (now_utc - self.deduplication_window).replace(tzinfo=None)
        query = (
            db.query(Interaction)
            .filter(
                Interaction.case_id == case_id,
                Interaction.channel == channel,
                Interaction.interaction_date >= window_start,
            )
            .order_by(Interaction.interaction_date.desc())
        )
        recent = query.first()
        if recent:
            if (recent.text_response or "").strip().lower() == (text_response or "").strip().lower():
                return recent
        return None

    def _contains_panic_trigger(self, text: Optional[str]) -> bool:
        if not text:
            return False
        tokens = text.lower().split()
        for token in tokens:
            clean_token = "".join(c for c in token if c.isalnum())
            if clean_token in PANIC_KEYWORDS:
                return True
        return False

    def _derive_distress_and_prediction(
        self,
        db: Session,
        case: Case,
        safety_response: Optional[int],
        fear_level: Optional[int],
        sleep_disruption: Optional[int],
        help_requested: bool,
        incomplete: bool = False,
    ) -> Tuple[DistressState, Prediction]:
        """
        Derives or records distress and prediction observations in PostgreSQL
        strictly preserving ML contract consistency (fails closed, never fake LOW).
        """
        now_utc = datetime.now(timezone.utc)

        if incomplete:
            distress_score = 0.50
            trajectory = "UNCERTAIN"
            conf = 0.40  # Under 0.60 threshold -> triggers low-confidence / human review
            escalation_prob = None  # Missing probability -> triggers INSUFFICIENT_DATA
            risk_level = "HIGH"
        else:
            score_acc = 0.0
            divisor = 0.0

            if safety_response is not None:
                score_acc += (5.0 - float(safety_response)) / 4.0
                divisor += 1.0
            if fear_level is not None:
                score_acc += float(fear_level) / 5.0
                divisor += 1.0
            if sleep_disruption is not None:
                score_acc += float(sleep_disruption) / 5.0
                divisor += 1.0
            if help_requested:
                score_acc += 1.0
                divisor += 1.0

            distress_score = round(score_acc / divisor, 2) if divisor > 0 else 0.50

            prev_dstate = (
                db.query(DistressState)
                .filter(DistressState.case_id == case.id)
                .order_by(DistressState.observation_date.desc(), DistressState.id.desc())
                .first()
            )

            if prev_dstate and prev_dstate.distress_score is not None:
                delta = round(distress_score - prev_dstate.distress_score, 2)
                if delta >= 0.15:
                    trajectory = "RAPIDLY_WORSENING"
                elif delta >= 0.05:
                    trajectory = "WORSENING"
                elif delta <= -0.15:
                    trajectory = "RAPIDLY_IMPROVING"
                elif delta <= -0.05:
                    trajectory = "IMPROVING"
                else:
                    trajectory = "STABLE"
            else:
                trajectory = "WORSENING" if distress_score >= 0.60 else "STABLE"

            conf = 0.90
            if distress_score >= 0.75 or help_requested:
                escalation_prob = 0.85
                risk_level = "HIGH"
            elif distress_score >= 0.50 or trajectory in ("WORSENING", "RAPIDLY_WORSENING"):
                escalation_prob = 0.55
                risk_level = "MEDIUM"
            else:
                escalation_prob = 0.20
                risk_level = "LOW"

        dstate = DistressState(
            case_id=case.id,
            observation_date=now_utc.replace(tzinfo=None),
            distress_score=distress_score,
            trajectory=trajectory,
            confidence=conf,
        )
        db.add(dstate)
        db.flush()

        pred = Prediction(
            case_id=case.id,
            prediction_date=now_utc.replace(tzinfo=None),
            escalation_probability=escalation_prob,
            confidence=conf,
            target_horizon_days=7,
        )
        if hasattr(Prediction, "risk_level"):
            pred.risk_level = risk_level
        if hasattr(Prediction, "explanation"):
            pred.explanation = json.dumps({"source": "channel_intake", "distress": distress_score, "trajectory": trajectory})

        db.add(pred)
        db.flush()

        return dstate, pred

    # -------------------------------------------------------------------------
    # 1. IVR CHANNEL WORKFLOW
    # -------------------------------------------------------------------------
    def process_ivr_check_in(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        safety_response: Optional[int] = None,
        fear_level: Optional[int] = None,
        sleep_disruption: Optional[int] = None,
        help_requested: bool = False,
        audio_transcript: Optional[str] = None,
        voice_available: bool = True,
        custom_router: Optional[AssignmentRouter] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        IVR Workflow:
        Check-in call -> Consent Verification -> Interaction Logging -> ML Prediction -> Intervention Engine
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)
            now_utc = datetime.now(timezone.utc)

            consent = self._get_consent(db, case.id)
            if consent:
                if not consent.monitoring_consent:
                    self._log_event(db, case, "MONITORING_CONSENT_REVOKED", "IVR call received but monitoring consent revoked.", now_utc, auto_commit=False)
                    return self.intervention_service.process_case_intervention(db, case.id, custom_router=custom_router, auto_commit=auto_commit)

                if not consent.voice_analysis_consent and voice_available:
                    self._log_event(db, case, "VOICE_CONSENT_DENIED", "Voice analysis not consented. Audio discarded.", now_utc, auto_commit=False)
                    voice_available = False

                if consent.safe_channel and consent.safe_channel.upper() not in ("IVR", "VOICE", "ALL"):
                    return self.handle_unsafe_channel_event(
                        db=db,
                        case_id=case.id,
                        attempted_channel="IVR",
                        reason=f"Beneficiary safe channel is restricted to '{consent.safe_channel}'.",
                        custom_router=custom_router,
                        auto_commit=auto_commit,
                    )

            if self._contains_panic_trigger(audio_transcript):
                return self.handle_unsafe_channel_event(
                    db=db,
                    case_id=case.id,
                    attempted_channel="IVR",
                    reason=f"Panic distress keyword detected in audio transcript: '{audio_transcript}'.",
                    custom_router=custom_router,
                    auto_commit=auto_commit,
                )

            dup = self._is_duplicate_interaction(db, case.id, "IVR", audio_transcript, now_utc)
            if dup:
                self._log_event(db, case, ChannelEventType.DUPLICATE_EVENT.value, f"Duplicate IVR event ignored. Existing interaction {dup.id}.", now_utc, auto_commit=False)
                return {
                    "channel": ChannelType.IVR.value,
                    "interaction_id": dup.id,
                    "is_duplicate": True,
                    "status": "DUPLICATE_IGNORED",
                }

            interaction = Interaction(
                case_id=case.id,
                interaction_date=now_utc.replace(tzinfo=None),
                channel=ChannelType.IVR.value,
                language=case.language or "hi",
                text_response=audio_transcript,
                voice_available=voice_available,
                response_completed=True,
                safety_response=safety_response,
                sleep_disruption=sleep_disruption,
                fear_level=fear_level,
                social_support=3,
                help_requested=help_requested,
                data_quality="good",
            )
            db.add(interaction)
            db.flush()

            self._log_event(db, case, ChannelEventType.CHECK_IN_RECEIVED.value, f"IVR check-in completed. Interaction #{interaction.id}.", now_utc, auto_commit=False)
            self._derive_distress_and_prediction(db, case, safety_response, fear_level, sleep_disruption, help_requested)

            intervention_res = self.intervention_service.process_case_intervention(
                db=db,
                case_id=case.id,
                custom_router=custom_router,
                auto_commit=auto_commit,
            )

            return {
                "channel": ChannelType.IVR.value,
                "interaction_id": interaction.id,
                "case_id": case.id,
                "case_string_id": case.case_id,
                "intervention": intervention_res,
            }
        finally:
            if close_session:
                db.close()

    # -------------------------------------------------------------------------
    # 2. SMS CHANNEL WORKFLOW
    # -------------------------------------------------------------------------
    def process_sms_check_in(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        text_response: str = "",
        safety_response: Optional[int] = None,
        fear_level: Optional[int] = None,
        help_requested: bool = False,
        custom_router: Optional[AssignmentRouter] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        SMS Workflow:
        Scheduled check-in -> Beneficiary response -> Text Analysis Consent -> Interaction Logging -> ML -> Intervention
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)
            now_utc = datetime.now(timezone.utc)

            consent = self._get_consent(db, case.id)
            if consent:
                if not consent.monitoring_consent:
                    self._log_event(db, case, "MONITORING_CONSENT_REVOKED", "SMS response received but monitoring consent revoked.", now_utc, auto_commit=False)
                    return self.intervention_service.process_case_intervention(db, case.id, custom_router=custom_router, auto_commit=auto_commit)

                if consent.safe_channel and consent.safe_channel.upper() not in ("SMS", "TEXT", "ALL"):
                    return self.handle_unsafe_channel_event(
                        db=db,
                        case_id=case.id,
                        attempted_channel="SMS",
                        reason=f"Beneficiary safe channel is restricted to '{consent.safe_channel}'.",
                        custom_router=custom_router,
                        auto_commit=auto_commit,
                    )

            if self._contains_panic_trigger(text_response):
                return self.handle_unsafe_channel_event(
                    db=db,
                    case_id=case.id,
                    attempted_channel="SMS",
                    reason=f"Panic keyword detected in SMS: '{text_response}'.",
                    custom_router=custom_router,
                    auto_commit=auto_commit,
                )

            dup = self._is_duplicate_interaction(db, case.id, "SMS", text_response, now_utc)
            if dup:
                self._log_event(db, case, ChannelEventType.DUPLICATE_EVENT.value, f"Duplicate SMS ignored. Existing interaction {dup.id}.", now_utc, auto_commit=False)
                return {
                    "channel": ChannelType.SMS.value,
                    "interaction_id": dup.id,
                    "is_duplicate": True,
                    "status": "DUPLICATE_IGNORED",
                }

            interaction = Interaction(
                case_id=case.id,
                interaction_date=now_utc.replace(tzinfo=None),
                channel=ChannelType.SMS.value,
                language=case.language or "en",
                text_response=text_response,
                voice_available=False,
                response_completed=True,
                safety_response=safety_response or (1 if help_requested else 4),
                fear_level=fear_level or (4 if help_requested else 1),
                sleep_disruption=2,
                social_support=3,
                help_requested=help_requested,
                data_quality="good",
            )
            db.add(interaction)
            db.flush()

            self._log_event(db, case, ChannelEventType.CHECK_IN_RECEIVED.value, f"SMS check-in documented. Interaction #{interaction.id}.", now_utc, auto_commit=False)
            self._derive_distress_and_prediction(db, case, safety_response, fear_level, sleep_disruption=2, help_requested=help_requested)

            intervention_res = self.intervention_service.process_case_intervention(
                db=db,
                case_id=case.id,
                custom_router=custom_router,
                auto_commit=auto_commit,
            )

            return {
                "channel": ChannelType.SMS.value,
                "interaction_id": interaction.id,
                "case_id": case.id,
                "case_string_id": case.case_id,
                "intervention": intervention_res,
            }
        finally:
            if close_session:
                db.close()

    # -------------------------------------------------------------------------
    # 3. CHATBOT CHANNEL WORKFLOW
    # -------------------------------------------------------------------------
    def process_chatbot_interaction(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        message_text: str = "",
        safety_response: Optional[int] = None,
        fear_level: Optional[int] = None,
        help_requested: bool = False,
        custom_router: Optional[AssignmentRouter] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Chatbot Workflow:
        Authorized Case Session -> Consent Check -> Interaction -> ML -> Intervention
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)
            now_utc = datetime.now(timezone.utc)

            consent = self._get_consent(db, case.id)
            if consent and not consent.monitoring_consent:
                self._log_event(db, case, "MONITORING_CONSENT_REVOKED", "Chatbot session attempted without monitoring consent.", now_utc, auto_commit=False)
                return self.intervention_service.process_case_intervention(db, case.id, custom_router=custom_router, auto_commit=auto_commit)

            if self._contains_panic_trigger(message_text):
                return self.handle_unsafe_channel_event(
                    db=db,
                    case_id=case.id,
                    attempted_channel="CHATBOT",
                    reason=f"Panic keyword detected in Chatbot message: '{message_text}'.",
                    custom_router=custom_router,
                    auto_commit=auto_commit,
                )

            dup = self._is_duplicate_interaction(db, case.id, "CHATBOT", message_text, now_utc)
            if dup:
                self._log_event(db, case, ChannelEventType.DUPLICATE_EVENT.value, f"Duplicate Chatbot message ignored. Interaction {dup.id}.", now_utc, auto_commit=False)
                return {
                    "channel": ChannelType.CHATBOT.value,
                    "interaction_id": dup.id,
                    "is_duplicate": True,
                    "status": "DUPLICATE_IGNORED",
                }

            interaction = Interaction(
                case_id=case.id,
                interaction_date=now_utc.replace(tzinfo=None),
                channel=ChannelType.CHATBOT.value,
                language=case.language or "en",
                text_response=message_text,
                voice_available=False,
                response_completed=True,
                safety_response=safety_response or 4,
                fear_level=fear_level or 2,
                sleep_disruption=2,
                social_support=3,
                help_requested=help_requested,
                data_quality="good",
            )
            db.add(interaction)
            db.flush()

            self._log_event(db, case, ChannelEventType.CHECK_IN_RECEIVED.value, f"Chatbot interaction documented. Interaction #{interaction.id}.", now_utc, auto_commit=False)
            self._derive_distress_and_prediction(db, case, safety_response, fear_level, sleep_disruption=2, help_requested=help_requested)

            intervention_res = self.intervention_service.process_case_intervention(
                db=db,
                case_id=case.id,
                custom_router=custom_router,
                auto_commit=auto_commit,
            )

            return {
                "channel": ChannelType.CHATBOT.value,
                "interaction_id": interaction.id,
                "case_id": case.id,
                "case_string_id": case.case_id,
                "intervention": intervention_res,
            }
        finally:
            if close_session:
                db.close()

    # -------------------------------------------------------------------------
    # 4. EDGE CASE WORKFLOWS (Periodic, Missed, Incomplete, Late, Unsafe)
    # -------------------------------------------------------------------------
    def handle_missed_check_in(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        scheduled_time: Optional[datetime] = None,
        custom_router: Optional[AssignmentRouter] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        MISSED Check-In:
        Triggered when a scheduled check-in window expires without contact.
        Logs CHECK_IN_MISSED event, synthesizes INSUFFICIENT_DATA / uncertainty state,
        and routes to PRIORITY_HUMAN_REVIEW (HIGH priority, 24h SLA).
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)
            now_utc = datetime.now(timezone.utc)
            sched = ensure_utc(scheduled_time) if scheduled_time else now_utc - timedelta(hours=2)

            self._log_event(
                db=db,
                case=case,
                event_type=ChannelEventType.CHECK_IN_MISSED.value,
                description=f"Scheduled check-in at {sched.strftime('%Y-%m-%d %H:%M UTC')} was missed. Contact window lapsed.",
                event_date=now_utc,
                auto_commit=False,
            )

            dstate = DistressState(
                case_id=case.id,
                observation_date=now_utc.replace(tzinfo=None),
                distress_score=0.60,
                trajectory="UNCERTAIN",
                confidence=0.45,
            )
            db.add(dstate)

            pred = Prediction(
                case_id=case.id,
                prediction_date=now_utc.replace(tzinfo=None),
                escalation_probability=None,
                confidence=0.45,
                target_horizon_days=7,
            )
            if hasattr(Prediction, "risk_level"):
                pred.risk_level = "INSUFFICIENT_DATA"
            db.add(pred)
            db.flush()

            intervention_res = self.intervention_service.process_case_intervention(
                db=db,
                case_id=case.id,
                custom_router=custom_router,
                auto_commit=auto_commit,
            )

            return {
                "event_type": ChannelEventType.CHECK_IN_MISSED.value,
                "case_id": case.id,
                "case_string_id": case.case_id,
                "scheduled_time": sched.isoformat(),
                "intervention": intervention_res,
            }
        finally:
            if close_session:
                db.close()

    def handle_incomplete_interaction(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        channel: str = "IVR",
        reason: str = "Call dropped before survey completion",
        custom_router: Optional[AssignmentRouter] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        INCOMPLETE Interaction:
        Call dropped or survey abandoned midway (response_completed=False).
        Logs INTERACTION_INCOMPLETE event and safely routes to PRIORITY_HUMAN_REVIEW.
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)
            now_utc = datetime.now(timezone.utc)

            interaction = Interaction(
                case_id=case.id,
                interaction_date=now_utc.replace(tzinfo=None),
                channel=channel.upper(),
                language=case.language or "en",
                response_completed=False,
                data_quality="incomplete",
            )
            db.add(interaction)
            db.flush()

            self._log_event(
                db=db,
                case=case,
                event_type=ChannelEventType.INTERACTION_INCOMPLETE.value,
                description=f"Incomplete {channel} interaction (ID #{interaction.id}): {reason}.",
                event_date=now_utc,
                auto_commit=False,
            )

            self._derive_distress_and_prediction(db, case, safety_response=None, fear_level=None, sleep_disruption=None, help_requested=False, incomplete=True)

            intervention_res = self.intervention_service.process_case_intervention(
                db=db,
                case_id=case.id,
                custom_router=custom_router,
                auto_commit=auto_commit,
            )

            return {
                "event_type": ChannelEventType.INTERACTION_INCOMPLETE.value,
                "interaction_id": interaction.id,
                "case_id": case.id,
                "case_string_id": case.case_id,
                "reason": reason,
                "intervention": intervention_res,
            }
        finally:
            if close_session:
                db.close()

    def handle_late_response(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        channel: str = "SMS",
        delay_hours: float = 1.0,
        text_response: Optional[str] = None,
        custom_router: Optional[AssignmentRouter] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        LATE Response:
        Interaction received after scheduled check-in window.
        Logs LATE_RESPONSE event with delay metrics, then proceeds with evaluation.
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)
            now_utc = datetime.now(timezone.utc)

            self._log_event(
                db=db,
                case=case,
                event_type=ChannelEventType.LATE_RESPONSE.value,
                description=f"Late {channel} response received with delay of {delay_hours:.1f} hours.",
                event_date=now_utc,
                auto_commit=False,
            )

            if channel.upper() == ChannelType.IVR.value:
                return self.process_ivr_check_in(
                    db=db,
                    case_id=case.id,
                    audio_transcript=text_response,
                    custom_router=custom_router,
                    auto_commit=auto_commit,
                )
            else:
                return self.process_sms_check_in(
                    db=db,
                    case_id=case.id,
                    text_response=text_response or "Late check-in response",
                    custom_router=custom_router,
                    auto_commit=auto_commit,
                )
        finally:
            if close_session:
                db.close()

    def handle_unsafe_channel_event(
        self,
        db: Optional[Session] = None,
        case_id: int | str = None,
        attempted_channel: str = "UNKNOWN",
        reason: str = "Unsafe channel detected",
        custom_router: Optional[AssignmentRouter] = None,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        UNSAFE Channel Event:
        Triggered when an unauthorized/insecure channel is used or distress panic is detected.
        Immediately logs UNSAFE_CHANNEL_DETECTED event and triggers EMERGENCY_ESCALATION
        with URGENT priority (4h SLA).
        """
        if case_id is None:
            raise ValueError("case_id must be provided.")

        db, close_session = self._acquire_session(db)

        try:
            case = self._get_case(db, case_id)
            now_utc = datetime.now(timezone.utc)

            self._log_event(
                db=db,
                case=case,
                event_type=ChannelEventType.UNSAFE_CHANNEL_DETECTED.value,
                description=f"Security alert on channel '{attempted_channel}': {reason}. Emergency protocol activated.",
                event_date=now_utc,
                auto_commit=False,
            )

            dstate = DistressState(
                case_id=case.id,
                observation_date=now_utc.replace(tzinfo=None),
                distress_score=0.95,
                trajectory="RAPIDLY_WORSENING",
                confidence=0.99,
            )
            db.add(dstate)

            pred = Prediction(
                case_id=case.id,
                prediction_date=now_utc.replace(tzinfo=None),
                escalation_probability=0.95,
                confidence=0.99,
                target_horizon_days=1,
            )
            if hasattr(Prediction, "risk_level"):
                pred.risk_level = "CRITICAL"
            db.add(pred)
            db.flush()

            # Document intake attempt as an interaction
            interaction = Interaction(
                case_id=case.id,
                interaction_date=now_utc.replace(tzinfo=None),
                channel=attempted_channel,
                language=case.language or "en",
                text_response=f"UNSAFE: {reason}",
                voice_available=False,
                response_completed=False,
                help_requested=True,
                data_quality="unsafe",
            )
            db.add(interaction)
            db.flush()

            intervention_res = self.intervention_service.process_case_intervention(
                db=db,
                case_id=case.id,
                custom_router=custom_router,
                auto_commit=auto_commit,
            )

            return {
                "channel": attempted_channel,
                "event_type": ChannelEventType.UNSAFE_CHANNEL_DETECTED.value,
                "interaction_id": interaction.id,
                "case_id": case.id,
                "case_string_id": case.case_id,
                "attempted_channel": attempted_channel,
                "reason": reason,
                "intervention": intervention_res,
            }
        finally:
            if close_session:
                db.close()


# Global singleton instance
channel_service = ChannelWorkflowService()
