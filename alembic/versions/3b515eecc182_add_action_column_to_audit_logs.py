"""add_action_column_to_audit_logs

Revision ID: 3b515eecc182
Revises: 1e36a16b4fad
Create Date: 2024-12-28 08:51:34.893541

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3b515eecc182"
down_revision: Union[str, None] = "1e36a16b4fad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add action column to audit_logs
    op.add_column(
        "audit_logs", sa.Column("action", sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    # Remove action column from audit_logs
    op.drop_column("audit_logs", "action")
