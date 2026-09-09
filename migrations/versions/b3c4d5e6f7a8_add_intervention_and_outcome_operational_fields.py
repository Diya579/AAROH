"""add_intervention_and_outcome_operational_fields

Revision ID: b3c4d5e6f7a8
Revises: baab7db3eede
Create Date: 2026-09-09 08:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "baab7db3eede"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Additive columns to interventions (safe defaults preserve existing rows)
    op.add_column(
        "interventions",
        sa.Column("priority", sa.String(length=20), server_default="ROUTINE", nullable=False),
    )
    op.add_column(
        "interventions",
        sa.Column("reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "interventions",
        sa.Column("assigned_role", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "interventions",
        sa.Column("backup_assigned_to", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "interventions",
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "interventions",
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "interventions",
        sa.Column("due_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "interventions",
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # Data preservation: Copy existing data from legacy backup_assignee if present
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c["name"] for c in inspector.get_columns("interventions")}
    if "backup_assignee" in existing_cols:
        op.execute(
            "UPDATE interventions SET backup_assigned_to = backup_assignee "
            "WHERE backup_assigned_to IS NULL AND backup_assignee IS NOT NULL"
        )

    op.create_index("ix_interventions_priority", "interventions", ["priority"])
    op.create_index("ix_interventions_due_at", "interventions", ["due_at"])

    # Additive columns to outcomes (safe defaults preserve existing rows)
    op.add_column(
        "outcomes",
        sa.Column("follow_up_required", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "outcomes",
        sa.Column("notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_index("ix_interventions_due_at", table_name="interventions")
    op.drop_index("ix_interventions_priority", table_name="interventions")
    op.drop_column("outcomes", "notes")
    op.drop_column("outcomes", "follow_up_required")
    op.drop_column("interventions", "completed_at")
    op.drop_column("interventions", "due_at")
    op.drop_column("interventions", "acknowledged_at")
    op.drop_column("interventions", "assigned_at")
    op.drop_column("interventions", "backup_assigned_to")
    op.drop_column("interventions", "assigned_role")
    op.drop_column("interventions", "reason")
    op.drop_column("interventions", "priority")
