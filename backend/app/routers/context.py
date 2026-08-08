from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Device, Document, Interaction
from app.schemas import UserContextResponse
from app.security import get_current_device

router = APIRouter(prefix="/context", tags=["context"])


@router.get("/user/{user_id}", response_model=UserContextResponse)
def get_user_context(
    user_id: str,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> UserContextResponse:
    if device.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your profile")

    interactions = (
        db.execute(
            select(Interaction)
            .where(Interaction.user_id == user_id)
            .order_by(Interaction.created_at.desc())
            .limit(20)
        )
        .scalars()
        .all()
    )
    doc_count = db.execute(
        select(func.count()).select_from(Document).where(Document.user_id == user_id)
    ).scalar_one()

    return UserContextResponse(
        user_id=user_id,
        display_name=device.user.display_name,
        recent_interactions=[
            {
                "id": i.id,
                "transcript": i.transcript,
                "response": i.response,
                "emotion_state": i.emotion_state,
                "created_at": i.created_at.isoformat(),
            }
            for i in interactions
        ],
        document_count=doc_count,
    )
