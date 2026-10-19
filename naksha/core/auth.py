"""Authentication, JWT tokens, and FastAPI dependencies for NAKSHA."""
import time
from typing import Optional, List, Dict
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from naksha.core.config import settings
from naksha.models.auth import OfficerRole, OfficerContext
from naksha.core.policy import check_role_permission, check_jurisdiction_permission

security_bearer = HTTPBearer(auto_error=False)


def create_officer_token(context: OfficerContext, expires_in: Optional[int] = None) -> str:
    """Generates an HS256-signed JWT for an authenticated officer session."""
    now = int(time.time())
    expiry = now + (expires_in if expires_in is not None else settings.jwt_expiry_seconds)
    payload = {
        "sub": context.officer_id,
        "name": context.name,
        "role": context.role.value if isinstance(context.role, OfficerRole) else str(context.role),
        "designation": context.designation,
        "office": context.office,
        "jurisdiction": context.jurisdiction,
        "iat": now,
        "exp": expiry,
        "iss": settings.jwt_issuer,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_officer_token(token: str) -> OfficerContext:
    """Decodes, verifies signature, issuer, expiration, and claims of a JWT token.

    Raises HTTPException(401) on any failure.
    """
    if not token or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authorization token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iss", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token signature or claims: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    required_fields = ["sub", "name", "role", "designation", "office", "jurisdiction"]
    missing = [f for f in required_fields if f not in payload]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token missing required officer claims: {', '.join(missing)}.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        role = OfficerRole(payload["role"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token contains unrecognized officer role: '{payload['role']}'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return OfficerContext(
        officer_id=payload["sub"],
        name=payload["name"],
        role=role,
        designation=payload["designation"],
        office=payload["office"],
        jurisdiction=payload["jurisdiction"],
    )


def get_current_officer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> OfficerContext:
    """FastAPI dependency: authenticates Bearer token from header or raises 401."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer authorization token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_officer_token(credentials.credentials)


def require_role(route_group: str):
    """FastAPI dependency factory enforcing allowed roles for a route group."""
    def _role_checker(officer: OfficerContext = Depends(get_current_officer)) -> OfficerContext:
        if not check_role_permission(officer.role, route_group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Officer role '{officer.role.value}' is not authorized to access '{route_group}'.",
            )
        return officer
    return _role_checker
