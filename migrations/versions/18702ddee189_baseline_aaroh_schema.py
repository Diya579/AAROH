"""Baseline AAROH schema

Revision ID: 18702ddee189
Revises:
Create Date: 2026-09-04 02:18:57.538859
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "18702ddee189"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the complete baseline AAROH schema."""

    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.String(length=50), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("district_type", sa.String(length=20), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("priority_use_case", sa.String(length=100), nullable=False),
        sa.Column("current_stage", sa.String(length=50), nullable=False),
        sa.Column("voice_opted_in", sa.Boolean(), nullable=True),
        sa.Column("monitoring_consent", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id"),
    )

    op.create_table(
        "case_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("event_date", sa.DateTime(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("case_stage", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "interactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("interaction_date", sa.DateTime(), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("text_response", sa.Text(), nullable=True),
        sa.Column("voice_available", sa.Boolean(), nullable=True),
        sa.Column("response_completed", sa.Boolean(), nullable=True),
        sa.Column("safety_response", sa.Integer(), nullable=True),
        sa.Column("sleep_disruption", sa.Integer(), nullable=True),
        sa.Column("fear_level", sa.Integer(), nullable=True),
        sa.Column("social_support", sa.Integer(), nullable=True),
        sa.Column("help_requested", sa.Boolean(), nullable=True),
        sa.Column("data_quality", sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "text_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interaction_id", sa.Integer(), nullable=False),
        sa.Column("distress_intensity", sa.Float(), nullable=True),
        sa.Column("fear", sa.Float(), nullable=True),
        sa.Column("intimidation", sa.Float(), nullable=True),
        sa.Column("hopelessness", sa.Float(), nullable=True),
        sa.Column("isolation", sa.Float(), nullable=True),
        sa.Column("help_seeking", sa.Float(), nullable=True),
        sa.Column("language_confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "interaction_id",
            name="uq_text_features_interaction_id",
        ),
    )

    op.create_table(
        "voice_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interaction_id", sa.Integer(), nullable=False),
        sa.Column("speech_rate", sa.Float(), nullable=True),
        sa.Column("pause_ratio", sa.Float(), nullable=True),
        sa.Column("response_latency", sa.Float(), nullable=True),
        sa.Column("pitch_variability", sa.Float(), nullable=True),
        sa.Column("energy_variation", sa.Float(), nullable=True),
        sa.Column("audio_quality", sa.Float(), nullable=True),
        sa.Column("baseline_deviation", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "interaction_id",
            name="uq_voice_features_interaction_id",
        ),
    )

    op.create_table(
        "engagement_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interaction_id", sa.Integer(), nullable=False),
        sa.Column("response_delay", sa.Float(), nullable=True),
        sa.Column("missed_checkin", sa.Boolean(), nullable=True),
        sa.Column("engagement_change", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["interaction_id"], ["interactions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "interaction_id",
            name="uq_engagement_features_interaction_id",
        ),
    )

    op.create_table(
        "distress_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("observation_date", sa.DateTime(), nullable=False),
        sa.Column("distress_score", sa.Float(), nullable=True),
        sa.Column("trajectory", sa.String(length=30), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("prediction_date", sa.DateTime(), nullable=False),
        sa.Column("escalation_probability", sa.Float(), nullable=True),
        sa.Column("target_horizon_days", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "consents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("monitoring_consent", sa.Boolean(), nullable=True),
        sa.Column("text_analysis_consent", sa.Boolean(), nullable=True),
        sa.Column("voice_analysis_consent", sa.Boolean(), nullable=True),
        sa.Column("case_linkage_consent", sa.Boolean(), nullable=True),
        sa.Column("safe_channel", sa.String(length=30), nullable=True),
        sa.Column("safe_time", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "case_id",
            name="uq_consents_case_id",
        ),
    )

    op.create_table(
        "interventions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("intervention_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "outcomes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("intervention_id", sa.Integer(), nullable=True),
        sa.Column("outcome_type", sa.String(length=100), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"]),
        sa.ForeignKeyConstraint(["intervention_id"], ["interventions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Query indexes represented by the current SQLAlchemy models.
    op.create_index(
        "ix_case_events_case_id_event_date",
        "case_events",
        ["case_id", "event_date"],
    )

    op.create_index(
        "ix_interactions_case_id_interaction_date",
        "interactions",
        ["case_id", "interaction_date"],
    )

    op.create_index(
        "ix_distress_states_case_id_observation_date",
        "distress_states",
        ["case_id", "observation_date"],
    )

    op.create_index(
        "ix_predictions_case_id_prediction_date",
        "predictions",
        ["case_id", "prediction_date"],
    )

    op.create_index(
        "ix_interventions_case_id_status",
        "interventions",
        ["case_id", "status"],
    )

    op.create_index(
        "ix_outcomes_case_id_recorded_at",
        "outcomes",
        ["case_id", "recorded_at"],
    )


def downgrade() -> None:
    """Drop the complete baseline AAROH schema."""

    op.drop_index(
        "ix_outcomes_case_id_recorded_at",
        table_name="outcomes",
    )
    op.drop_index(
        "ix_interventions_case_id_status",
        table_name="interventions",
    )
    op.drop_index(
        "ix_predictions_case_id_prediction_date",
        table_name="predictions",
    )
    op.drop_index(
        "ix_distress_states_case_id_observation_date",
        table_name="distress_states",
    )
    op.drop_index(
        "ix_interactions_case_id_interaction_date",
        table_name="interactions",
    )
    op.drop_index(
        "ix_case_events_case_id_event_date",
        table_name="case_events",
    )

    op.drop_table("outcomes")
    op.drop_table("interventions")
    op.drop_table("consents")
    op.drop_table("predictions")
    op.drop_table("distress_states")
    op.drop_table("engagement_features")
    op.drop_table("voice_features")
    op.drop_table("text_features")
    op.drop_table("interactions")
    op.drop_table("case_events")
    op.drop_table("cases")
    op.drop_table("model_versions")