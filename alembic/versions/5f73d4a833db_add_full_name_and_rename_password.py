"""add_full_name_and_rename_password

Revision ID: 5f73d4a833db
Revises: 805e84d3200f
Create Date: 2024-12-26 23:14:07.230759

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f73d4a833db"
down_revision: Union[str, None] = "805e84d3200f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add full_name column
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Drop full_name column
    op.drop_column("users", "full_name")
