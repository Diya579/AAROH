"""Add database integrity indexes and uniqueness

Revision ID: 50bf48ad60b6
Revises: 18702ddee189
Create Date: 2026-09-04 02:43:09.344126

This revision is retained for migration-history compatibility.
The constraints and indexes it originally added are now part
of the complete baseline migration.
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "50bf48ad60b6"
down_revision: Union[str, Sequence[str], None] = "18702ddee189"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Baseline already contains the integrity constraints and indexes."""
    pass


def downgrade() -> None:
    """Baseline owns the schema; nothing to remove here."""
    pass