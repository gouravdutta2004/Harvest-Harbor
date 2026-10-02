"""API-key authentication and role-based authorization for Harvest Harbor.

DEVELOPMENT AUTH:
Uses default dev keys (dev-farmer-key, dev-agronomist-key, dev-auditor-key, dev-admin-key)
when environment variable HARVEST_HARBOR_API_KEYS is not explicitly provided.

PRODUCTION AUTH:
In production, HARVEST_HARBOR_API_KEYS should be set to a JSON mapping of role -> secure secret key.
For session security, standard Bearer token or HttpOnly cookie authorization should wrap these endpoints.
"""
import hmac
import json
import os
from typing import Dict, Optional

from fastapi import Header, HTTPException, status

DEFAULT_ROLE_KEYS = {
    "farmer": "dev-farmer-key",
    "agronomist": "dev-agronomist-key",
    "auditor": "dev-auditor-key",
    "admin": "dev-admin-key",
}

ROLE_PERMISSIONS = {
    "farmer": {"scan", "view_reports", "print_reports", "print_certificates"},
    "agronomist": {
        "scan",
        "view_reports",
        "verify_blockchain",
        "calibrate_severity",
        "export_protocols",
        "review_reports",
        "print_reports",
        "print_certificates",
    },
    "auditor": {
        "view_reports",
        "verify_blockchain",
        "audit_hashes",
        "export_raw_json",
    },
    "admin": {"all"},
}


def _load_keys() -> Dict[str, str]:
    raw = os.getenv("HARVEST_HARBOR_API_KEYS", "").strip()
    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()
    is_production = env in {"production", "prod"}

    if not raw:
        if is_production:
            raise RuntimeError(
                "CRITICAL: Production environment detected, but HARVEST_HARBOR_API_KEYS is not configured. "
                "Authentication fails closed. Please set HARVEST_HARBOR_API_KEYS to a secure JSON role-key mapping."
            )
        return dict(DEFAULT_ROLE_KEYS)
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("HARVEST_HARBOR_API_KEYS must be a JSON object")
        result = {}
        for role, key in data.items():
            role = str(role).strip().lower()
            if role in ROLE_PERMISSIONS and isinstance(key, str) and key.strip():
                result[role] = key.strip()
        if not result:
            raise ValueError("No valid role keys configured")
        return result
    except Exception as exc:
        raise RuntimeError(f"Invalid HARVEST_HARBOR_API_KEYS: {exc}") from exc


def auth_required() -> bool:
    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()
    if env in {"production", "prod"}:
        return True
    return os.getenv("HARVEST_HARBOR_AUTH_REQUIRED", "true").strip().lower() in {"1", "true", "yes", "on"}


def authenticate(authorization: Optional[str], api_key: Optional[str], requested_role: Optional[str], inspector_id: Optional[str] = None) -> Dict[str, str]:
    if not auth_required():
        role = (requested_role or "agronomist").strip().lower()
        if role not in ROLE_PERMISSIONS:
            role = "agronomist"
        # identity is always the authenticated role; inspector_label is non-authoritative client metadata
        return {
            "role": role,
            "auth_type": "disabled",
            "authenticated": "false",
            "identity": f"unauthenticated:{role}",
            "inspector_label": inspector_id or "",
        }

    token = None
    auth_type = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        auth_type = "bearer"
    elif api_key:
        token = api_key.strip()
        auth_type = "apikey"

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Configure a valid API key or Bearer token.",
        )

    keys = _load_keys()
    matched_role = None
    for role, configured_key in keys.items():
        if hmac.compare_digest(token, configured_key):
            matched_role = role
            break

    if matched_role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API credentials.",
        )

    if requested_role and requested_role.strip().lower() != matched_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Credential is bound to role '{matched_role}'. Select the matching frontend role.",
        )

    # identity is derived from the verified API key — client cannot override it
    return {
        "role": matched_role,
        "auth_type": auth_type or "apikey",
        "authenticated": "true",
        "identity": f"authenticated:{matched_role}",
        "inspector_label": inspector_id or "",  # non-authoritative, for display only
    }


def require_auth(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    x_user_role: Optional[str] = Header(default=None),
    x_inspector_id: Optional[str] = Header(default=None),
) -> Dict[str, str]:
    return authenticate(authorization, x_api_key, x_user_role, x_inspector_id)


def authorize(user: Dict[str, str], permission: str) -> Dict[str, str]:
    role = user.get("role")
    permissions = ROLE_PERMISSIONS.get(role, set())
    if "all" not in permissions and permission not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' does not have permission '{permission}'.",
        )
    return user
