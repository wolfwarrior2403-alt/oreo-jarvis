"""Device pairing + token issuance/refresh (section 3.1, 6)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.logging_config import get_logger
from app.models import Device, User
from app.schemas import PairRequest, RefreshRequest, TokenResponse
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
logger = get_logger(__name__)


@router.post("/pair", response_model=TokenResponse)
def pair_device(req: PairRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """First-time handshake: a device presents the shared pairing code and
    gets back a JWT pair scoped to a newly created (or existing) user."""
    if req.pairing_code != settings.device_pairing_code:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid pairing code")

    user = None
    if req.user_email:
        user = db.query(User).filter(User.email == req.user_email).first()
    if user is None:
        user = User(display_name=req.user_display_name, email=req.user_email)
        db.add(user)
        db.flush()

    device = Device(user_id=user.id, name=req.device_name)
    db.add(device)
    db.flush()

    access_token = create_access_token(user.id, device.id)
    refresh_token = create_refresh_token(user.id, device.id)
    device.refresh_token_hash = hash_refresh_token(refresh_token)
    db.commit()

    logger.info("device_paired", device_id=device.id, user_id=user.id, device_name=device.name)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        device_id=device.id,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(req: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    payload = decode_token(req.refresh_token, expected_type="refresh")
    device = db.get(Device, payload["device_id"])

    if device is None or not device.is_active or device.user_id != payload["sub"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Device not recognized")

    if device.refresh_token_hash != hash_refresh_token(req.refresh_token):
        # Refresh token reuse/mismatch: revoke the device as a precaution.
        device.is_active = False
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalid")

    access_token = create_access_token(device.user_id, device.id)
    new_refresh_token = create_refresh_token(device.user_id, device.id)
    device.refresh_token_hash = hash_refresh_token(new_refresh_token)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user_id=device.user_id,
        device_id=device.id,
    )
