"""Add RBAC tables.

Revision ID: 2025_01_07_add_rbac
Revises: previous_revision
Create Date: 2025-01-07 14:06:37.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2025_01_07_add_rbac"
down_revision = None  # Update this with the previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    # Create roles table
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(255)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
    )

    # Create permissions table
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(255)),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
    )

    # Create user_roles association table
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    # Create role_permissions association table
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    # Create indexes
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
    op.create_index("ix_permissions_name", "permissions", ["name"], unique=True)
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index("ix_role_permissions_role_id", "role_permissions", ["role_id"])
    op.create_index(
        "ix_role_permissions_permission_id", "role_permissions", ["permission_id"]
    )

    # Import and run RBAC initialization
    from core.security.rbac import initialize_rbac
    from sqlalchemy.ext.asyncio import AsyncSession
    from database.session import async_session_maker

    async def init_rbac():
        async with async_session_maker() as session:
            await initialize_rbac(session)

    import asyncio

    asyncio.run(init_rbac())


def downgrade():
    # Drop tables in reverse order
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
