"""RBAC (Role-Based Access Control) utility functions."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models.role import Role, Permission
from database.models.user import User
from database.models.base_roles import (
    DEFAULT_ROLES,
    get_all_permissions,
    get_role_permissions,
)


async def initialize_rbac(session: AsyncSession) -> None:
    """Initialize RBAC system with default roles and permissions.

    This should be run once during system setup or migration.
    """
    # Create default permissions
    permissions_data = get_all_permissions()
    for perm_data in permissions_data:
        perm = Permission(
            name=perm_data["name"],
            description=perm_data["description"],
            resource=perm_data["resource"],
            action=perm_data["action"],
        )
        session.add(perm)

    # Create default roles
    for role_data in DEFAULT_ROLES:
        role = Role(
            name=role_data["name"],
            description=role_data["description"],
        )
        session.add(role)

    # Commit to get IDs
    await session.commit()

    # Assign permissions to roles
    for role_data in DEFAULT_ROLES:
        role = await get_role_by_name(session, role_data["name"])
        if role:
            permission_names = get_role_permissions(role_data["name"])
            permissions = await get_permissions_by_names(session, permission_names)
            role.permissions.extend(permissions)

    await session.commit()


async def get_role_by_name(session: AsyncSession, role_name: str) -> Optional[Role]:
    """Get role by name."""
    stmt = select(Role).where(Role.name == role_name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_permissions_by_names(
    session: AsyncSession, permission_names: List[str]
) -> List[Permission]:
    """Get permissions by their names."""
    stmt = select(Permission).where(Permission.name.in_(permission_names))
    result = await session.execute(stmt)
    return result.scalars().all()


async def assign_role_to_user(
    session: AsyncSession, user: User, role_name: str
) -> bool:
    """Assign role to user.

    Args:
        session: Database session
        user: User to assign role to
        role_name: Name of role to assign

    Returns:
        bool: True if role was assigned, False if role not found
    """
    role = await get_role_by_name(session, role_name)
    if not role:
        return False

    if role not in user.roles:
        user.roles.append(role)
        await session.commit()
    return True


async def remove_role_from_user(
    session: AsyncSession, user: User, role_name: str
) -> bool:
    """Remove role from user.

    Args:
        session: Database session
        user: User to remove role from
        role_name: Name of role to remove

    Returns:
        bool: True if role was removed, False if role not found
    """
    role = await get_role_by_name(session, role_name)
    if not role:
        return False

    if role in user.roles:
        user.roles.remove(role)
        await session.commit()
    return True


async def get_user_permissions(session: AsyncSession, user: User) -> List[str]:
    """Get all permission names for a user.

    Args:
        session: Database session
        user: User to get permissions for

    Returns:
        List[str]: List of permission names
    """
    if user.is_superuser:
        # Superuser has all permissions
        stmt = select(Permission.name)
        result = await session.execute(stmt)
        return result.scalars().all()

    # Get permissions from user's roles
    permissions = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.name)

    return list(permissions)
