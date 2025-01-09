"""Make user_id nullable in audit_logs

Revision ID: 1e36a16b4fad
Revises: 5f73d4a833db
Create Date: 2024-12-28 08:35:14.090423

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1e36a16b4fad"
down_revision: Union[str, None] = "5f73d4a833db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing foreign key constraint
    op.drop_constraint("audit_logs_user_id_fkey", "audit_logs", type_="foreignkey")

    # Make user_id and action nullable
    op.alter_column("audit_logs", "user_id", existing_type=sa.UUID(), nullable=True)

    # Add ON DELETE SET NULL to the foreign key constraint
    op.create_foreign_key(
        "audit_logs_user_id_fkey",
        "audit_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drop the foreign key constraint with ON DELETE SET NULL
    op.drop_constraint("audit_logs_user_id_fkey", "audit_logs", type_="foreignkey")

    # Make user_id non-nullable again
    op.alter_column("audit_logs", "user_id", existing_type=sa.UUID(), nullable=False)

    # Recreate the foreign key constraint without ON DELETE SET NULL
    op.create_foreign_key(
        "audit_logs_user_id_fkey", "audit_logs", "users", ["user_id"], ["id"]
    )
