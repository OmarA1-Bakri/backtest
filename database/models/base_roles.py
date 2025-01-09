"""Base roles and permissions for the backtesting platform."""

from typing import List, Dict, Any
import uuid

# Base Roles
DEFAULT_ROLES = [
    {
        "name": "admin",
        "description": "Full system access with all permissions",
    },
    {
        "name": "trader",
        "description": "Can create and manage strategies and backtests",
    },
    {
        "name": "analyst",
        "description": "Can view and analyze strategies and backtest results",
    },
    {
        "name": "viewer",
        "description": "Read-only access to public strategies and results",
    },
]

# Resource-based Permissions
PERMISSIONS = {
    "strategy": [
        {"action": "create", "description": "Create new trading strategies"},
        {"action": "read", "description": "View trading strategies"},
        {"action": "update", "description": "Modify existing strategies"},
        {"action": "delete", "description": "Delete strategies"},
        {"action": "execute", "description": "Execute strategy backtests"},
    ],
    "backtest": [
        {"action": "create", "description": "Create new backtests"},
        {"action": "read", "description": "View backtest results"},
        {"action": "update", "description": "Modify backtest parameters"},
        {"action": "delete", "description": "Delete backtest results"},
    ],
    "user": [
        {"action": "create", "description": "Create new users"},
        {"action": "read", "description": "View user information"},
        {"action": "update", "description": "Modify user details"},
        {"action": "delete", "description": "Delete users"},
    ],
    "role": [
        {"action": "create", "description": "Create new roles"},
        {"action": "read", "description": "View roles"},
        {"action": "update", "description": "Modify roles"},
        {"action": "delete", "description": "Delete roles"},
    ],
    "metrics": [
        {"action": "create", "description": "Create performance metrics"},
        {"action": "read", "description": "View performance metrics"},
        {"action": "update", "description": "Update metrics calculations"},
        {"action": "export", "description": "Export metrics data"},
    ],
}

# Role-Permission Mappings
ROLE_PERMISSIONS = {
    "admin": [
        # Admin has all permissions
        f"{resource}:{action['action']}"
        for resource, actions in PERMISSIONS.items()
        for action in actions
    ],
    "trader": [
        # Strategy permissions
        "strategy:create",
        "strategy:read",
        "strategy:update",
        "strategy:delete",
        "strategy:execute",
        # Backtest permissions
        "backtest:create",
        "backtest:read",
        "backtest:update",
        "backtest:delete",
        # Metrics permissions
        "metrics:create",
        "metrics:read",
        "metrics:export",
    ],
    "analyst": [
        # Strategy permissions
        "strategy:read",
        "strategy:execute",
        # Backtest permissions
        "backtest:create",
        "backtest:read",
        # Metrics permissions
        "metrics:read",
        "metrics:export",
    ],
    "viewer": [
        # Read-only permissions
        "strategy:read",
        "backtest:read",
        "metrics:read",
    ],
}


def get_permission_name(resource: str, action: str) -> str:
    """Generate standardized permission name."""
    return f"{resource}:{action}"


def get_all_permissions() -> List[Dict[str, Any]]:
    """Get list of all permissions with standardized names."""
    all_permissions = []
    for resource, actions in PERMISSIONS.items():
        for action in actions:
            all_permissions.append(
                {
                    "id": uuid.uuid4(),
                    "name": get_permission_name(resource, action["action"]),
                    "description": action["description"],
                    "resource": resource,
                    "action": action["action"],
                }
            )
    return all_permissions


def get_role_permissions(role_name: str) -> List[str]:
    """Get list of permission names for a role."""
    return ROLE_PERMISSIONS.get(role_name, [])
