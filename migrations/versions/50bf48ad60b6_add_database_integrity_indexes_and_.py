"""Add database integrity indexes and uniqueness

Revision ID: 50bf48ad60b6
Revises: 18702ddee189
Create Date: 2026-09-04 02:43:09.344126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50bf48ad60b6'
down_revision: Union[str, Sequence[str], None] = '18702ddee189'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Enforce one feature record per interaction.
    op.create_unique_constraint(
        "uq_text_features_interaction_id",
        "text_features",
        ["interaction_id"],
    )
    op.create_unique_constraint(
        "uq_voice_features_interaction_id",
        "voice_features",
        ["interaction_id"],
    )
    op.create_unique_constraint(
        "uq_engagement_features_interaction_id",
        "engagement_features",
        ["interaction_id"],
    )

    # Consent is currently modeled as one current consent record per case.
    op.create_unique_constraint(
        "uq_consents_case_id",
        "consents",
        ["case_id"],
    )

    # High-value query indexes.
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
    """Downgrade schema."""

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

    op.drop_constraint(
        "uq_consents_case_id",
        "consents",
        type_="unique",
    )
    op.drop_constraint(
        "uq_engagement_features_interaction_id",
        "engagement_features",
        type_="unique",
    )
    op.drop_constraint(
        "uq_voice_features_interaction_id",
        "voice_features",
        type_="unique",
    )
    op.drop_constraint(
        "uq_text_features_interaction_id",
        "text_features",
        type_="unique",
    )