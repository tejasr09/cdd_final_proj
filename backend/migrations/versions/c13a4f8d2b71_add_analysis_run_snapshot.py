"""add immutable analysis run snapshots

Revision ID: c13a4f8d2b71
Revises: b4fceea3f1e2
Create Date: 2026-11-07 14:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c13a4f8d2b71"
down_revision: str | Sequence[str] | None = "b4fceea3f1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("impact_runs") as batch_op:
        batch_op.add_column(
            sa.Column(
                "input_snapshot",
                sa.JSON(),
                server_default=sa.text("'{}'"),
                nullable=False,
            )
        )
        batch_op.drop_constraint("ck_impact_runs_status", type_="check")
        batch_op.create_check_constraint(
            "ck_impact_runs_status",
            "status IN ('pending', 'running', 'completed', 'completed_with_limits', "
            "'incomplete', 'failed')",
        )
        batch_op.alter_column("input_snapshot", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("impact_runs") as batch_op:
        batch_op.drop_constraint("ck_impact_runs_status", type_="check")
        batch_op.drop_column("input_snapshot")
        batch_op.create_check_constraint(
            "ck_impact_runs_status",
            "status IN ('pending', 'completed', 'incomplete', 'failed')",
        )
