from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
    JSON,
    func
)

from sqlalchemy.orm import relationship

from backend.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)

    case_id = Column(String(50), unique=True, nullable=False)
    language = Column(String(20), nullable=False)

    district_type = Column(String(20), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)  # Required for STATE_OFFICIAL scoping

    priority_use_case = Column(String(100), nullable=False)

    current_stage = Column(String(50), nullable=False)

    voice_opted_in = Column(Boolean, default=False)
    monitoring_consent = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship(
        "CaseEvent",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    interactions = relationship(
        "Interaction",
        back_populates="case",
        cascade="all, delete-orphan"
    )


class CaseEvent(Base):
    __tablename__ = "case_events"

    __table_args__ = (
        Index(
            "ix_case_events_case_id_event_date",
            "case_id",
            "event_date"
        ),
    )

    id = Column(Integer, primary_key=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    event_date = Column(DateTime, nullable=False)

    event_type = Column(String(100), nullable=False)

    description = Column(Text)

    case_stage = Column(String(50), nullable=False)

    case = relationship(
        "Case",
        back_populates="events"
    )


class Interaction(Base):
    __tablename__ = "interactions"

    __table_args__ = (
        Index(
            "ix_interactions_case_id_interaction_date",
            "case_id",
            "interaction_date"
        ),
    )

    id = Column(Integer, primary_key=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    interaction_date = Column(DateTime, nullable=False)

    channel = Column(String(30), nullable=False)

    language = Column(String(20), nullable=False)

    text_response = Column(Text)

    voice_available = Column(Boolean, default=False)

    response_completed = Column(Boolean, default=True)

    safety_response = Column(Integer)

    sleep_disruption = Column(Integer)

    fear_level = Column(Integer)

    social_support = Column(Integer)

    help_requested = Column(Boolean, default=False)

    data_quality = Column(String(30), default="good")

    case = relationship(
        "Case",
        back_populates="interactions"
    )


class TextFeature(Base):
    __tablename__ = "text_features"

    __table_args__ = (
        UniqueConstraint(
            "interaction_id",
            name="uq_text_features_interaction_id"
        ),
    )

    id = Column(Integer, primary_key=True)

    interaction_id = Column(
        Integer,
        ForeignKey("interactions.id"),
        nullable=False
    )

    distress_intensity = Column(Float)
    fear = Column(Float)
    intimidation = Column(Float)
    hopelessness = Column(Float)
    isolation = Column(Float)
    help_seeking = Column(Float)

    language_confidence = Column(Float)


class VoiceFeature(Base):
    __tablename__ = "voice_features"

    __table_args__ = (
        UniqueConstraint(
            "interaction_id",
            name="uq_voice_features_interaction_id"
        ),
    )

    id = Column(Integer, primary_key=True)

    interaction_id = Column(
        Integer,
        ForeignKey("interactions.id"),
        nullable=False
    )

    speech_rate = Column(Float)
    pause_ratio = Column(Float)
    response_latency = Column(Float)
    pitch_variability = Column(Float)
    energy_variation = Column(Float)

    audio_quality = Column(Float)

    baseline_deviation = Column(Float)


class EngagementFeature(Base):
    __tablename__ = "engagement_features"

    __table_args__ = (
        UniqueConstraint(
            "interaction_id",
            name="uq_engagement_features_interaction_id"
        ),
    )

    id = Column(Integer, primary_key=True)

    interaction_id = Column(
        Integer,
        ForeignKey("interactions.id"),
        nullable=False
    )

    response_delay = Column(Float)
    missed_checkin = Column(Boolean)
    engagement_change = Column(Float)


class DistressState(Base):
    __tablename__ = "distress_states"

    __table_args__ = (
        Index(
            "ix_distress_states_case_id_observation_date",
            "case_id",
            "observation_date"
        ),
    )

    id = Column(Integer, primary_key=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    observation_date = Column(DateTime, nullable=False)

    distress_score = Column(Float)

    trajectory = Column(String(30))

    confidence = Column(Float)


class Prediction(Base):
    __tablename__ = "predictions"

    __table_args__ = (
        Index(
            "ix_predictions_case_id_prediction_date",
            "case_id",
            "prediction_date"
        ),
    )

    id = Column(Integer, primary_key=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    prediction_date = Column(DateTime, nullable=False)

    escalation_probability = Column(Float)

    target_horizon_days = Column(Integer, default=7)

    confidence = Column(Float)

    risk_level = Column(String(50))
    
    explanation = Column(JSON)


class Consent(Base):
    __tablename__ = "consents"

    __table_args__ = (
        UniqueConstraint(
            "case_id",
            name="uq_consents_case_id"
        ),
    )

    id = Column(Integer, primary_key=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    monitoring_consent = Column(Boolean, default=False)
    text_analysis_consent = Column(Boolean, default=False)
    voice_analysis_consent = Column(Boolean, default=False)
    case_linkage_consent = Column(Boolean, default=False)

    safe_channel = Column(String(30))
    safe_time = Column(String(50))


class Intervention(Base):
    __tablename__ = "interventions"

    __table_args__ = (
        Index(
            "ix_interventions_case_id_status",
            "case_id",
            "status"
        ),
    )

    id = Column(Integer, primary_key=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    intervention_type = Column(String(100))

    status = Column(String(50))

    assigned_to = Column(String(100))

    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Outcome(Base):
    __tablename__ = "outcomes"

    __table_args__ = (
        Index(
            "ix_outcomes_case_id_recorded_at",
            "case_id",
            "recorded_at"
        ),
    )

    id = Column(Integer, primary_key=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    intervention_id = Column(
        Integer,
        ForeignKey("interventions.id")
    )

    outcome_type = Column(String(100))

    completed = Column(Boolean, default=False)

    recorded_at = Column(DateTime, default=datetime.utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True)

    model_name = Column(String(100))
    version = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)