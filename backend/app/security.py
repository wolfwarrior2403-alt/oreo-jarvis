"""JWT issuance/verification and the device-pairing handshake (section 3.1 / 6).

Flow:
  1. A new phone calls POST /auth/pair with the shared DEVICE_PAIRING_CODE
     (given out of-band by the person running the backend) and a device name.
  2. The backend creates a Device row and returns a short-lived access
     token plus a longer-lived refresh token.
  3. Every other endpoint requires `Authorization: Bearer <access token>`.
  4. When the access token expires, the client calls POST /auth/refresh
     with the refresh token to get a new pair (refresh token rotates).
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Device

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=True)


class TokenPayloadError(Exception):
    pass


def _create_token(subject: str, device_id: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "device_id": device_id,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        # Random nonce so two tokens minted within the same second still
        # differ (JWT `iat`/`exp` only have second resolution).
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, device_id: str) -> str:
    return _create_token(
        user_id, device_id, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: str, device_id: str) -> str:
    return _create_token(
        user_id, device_id, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_pairing_secret() -> str:
    """A random value, unrelated to the shared pairing code, used nowhere yet
    but exposed for callers that want a per-device secret in the future."""
    return secrets.token_urlsafe(32)


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")
    return payload


def get_current_device(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Device:
    payload = decode_token(credentials.credentials, expected_type="access")
    device = db.get(Device, payload["device_id"])
    if device is None or not device.is_active or device.user_id != payload["sub"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device not recognized")
    return device
