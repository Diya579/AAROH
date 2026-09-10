# AAROH — Proposed Database Contract Extensions for Interventions & Outcomes
**To:** Diya (Architecture & Database Lead)  
**From:** Preet (Operations & Analytics Owner)  
**Date:** Day 1 Architecture Freeze  
**Target Migration:** Day 2 Core Implementation

---

## 1. Context & Motivation

To fulfill the requirements of AAROH's operational workflow (prioritization, district/role routing, SLA tracking, and outcome verification), the existing baseline `interventions` and `outcomes` tables need minimal, non-breaking schema extensions.

---

## 2. Proposed Column Additions for `interventions` Table

Existing columns:
- `id` (Integer PK)
- `case_id` (Integer FK -> cases.id)
- `intervention_type` (String 100)
- `status` (String 50)
- `assigned_to` (String 100)

### Recommended New Columns:

| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `priority` | `String(20)` | `False` | `'ROUTINE'` | Operational urgency (`URGENT`, `HIGH`, `ROUTINE`, `LOW`, `NONE`) |
| `reason` | `Text` / `JSON` | `True` | `None` | Grounded explanation for generation (distress, trajectory, escalation prob, factors) |
| `assigned_role` | `String(50)` | `True` | `None` | Responsible role (`COUNSELLOR`, `CASE_OFFICER`, `DESIGNATED_OFFICER`, etc.) |
| `backup_assigned_to` | `String(100)` | `True` | `None` | Secondary fallback assignee for urgent cases |
| `assigned_at` | `DateTime` | `True` | `None` | Timestamp when assignee was set |
| `acknowledged_at` | `DateTime` | `True` | `None` | Timestamp when official acknowledged intervention |
| `due_at` | `DateTime` | `True` | `None` | Target SLA deadline |
| `completed_at` | `DateTime` | `True` | `None` | Timestamp when intervention was completed |
| `created_at` | `DateTime` | `False` | `utcnow` | Creation timestamp |

---

## 3. Proposed Column Additions for `outcomes` Table

Existing columns:
- `id` (Integer PK)
- `case_id` (Integer FK -> cases.id)
- `intervention_id` (Integer FK -> interventions.id)
- `outcome_type` (String 100)
- `completed` (Boolean)
- `recorded_at` (DateTime)

### Recommended New Columns:

| Column | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `follow_up_required` | `Boolean` | `False` | `False` | Flag indicating whether subsequent follow-up check is required |
| `notes` | `Text` | `True` | `None` | Operational caseworker notes (subject to access control) |

---

## 4. Draft Alembic Migration Script for Diya

```python
"""add_intervention_operational_and_sla_fields

Revision ID: preet_day1_ops
Revises: 50bf48ad60b6
Create Date: 2026-09-06
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # interventions extensions
    op.add_column('interventions', sa.Column('priority', sa.String(length=20), server_default='ROUTINE', nullable=False))
    op.add_column('interventions', sa.Column('reason', sa.Text(), nullable=True))
    op.add_column('interventions', sa.Column('assigned_role', sa.String(length=50), nullable=True))
    op.add_column('interventions', sa.Column('backup_assigned_to', sa.String(length=100), nullable=True))
    op.add_column('interventions', sa.Column('assigned_at', sa.DateTime(), nullable=True))
    op.add_column('interventions', sa.Column('acknowledged_at', sa.DateTime(), nullable=True))
    op.add_column('interventions', sa.Column('due_at', sa.DateTime(), nullable=True))
    op.add_column('interventions', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.add_column('interventions', sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))

    op.create_index('ix_interventions_priority', 'interventions', ['priority'])
    op.create_index('ix_interventions_due_at', 'interventions', ['due_at'])

    # outcomes extensions
    op.add_column('outcomes', sa.Column('follow_up_required', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('outcomes', sa.Column('notes', sa.Text(), nullable=True))

def downgrade():
    op.drop_index('ix_interventions_due_at', table_name='interventions')
    op.drop_index('ix_interventions_priority', table_name='interventions')
    op.drop_column('outcomes', 'notes')
    op.drop_column('outcomes', 'follow_up_required')
    op.drop_column('interventions', 'created_at')
    op.drop_column('interventions', 'completed_at')
    op.drop_column('interventions', 'due_at')
    op.drop_column('interventions', 'acknowledged_at')
    op.drop_column('interventions', 'assigned_at')
    op.drop_column('interventions', 'backup_assigned_to')
    op.drop_column('interventions', 'assigned_role')
    op.drop_column('interventions', 'reason')
    op.drop_column('interventions', 'priority')
```
