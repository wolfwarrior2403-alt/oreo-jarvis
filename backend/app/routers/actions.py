"""The confirmation-gate HTTP surface (section 3.1 / 3.5 / 6).

GET  /actions/pending   — list actions awaiting the user's voice confirmation
POST /execute/action    — the doc's endpoint: approve or reject a pending
                           action, and if approved, execute it immediately.
                           Rejecting never executes anything.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.actions import (
    ActionNotApprovedError,
    ActionNotFoundError,
    UnknownToolError,
    decide_action,
    execute_action,
)
from app.db import get_db
from app.models import Device, PendingAction
from app.schemas import ActionDecisionRequest, ActionExecutionResult, ProposedActionOut
from app.security import get_current_device

router = APIRouter(tags=["actions"])


@router.get("/actions/pending", response_model=list[ProposedActionOut])
def list_pending_actions(
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> list[ProposedActionOut]:
    rows = (
        db.execute(
            select(PendingAction)
            .where(PendingAction.user_id == device.user_id, PendingAction.status == "pending")
            .order_by(PendingAction.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [
        ProposedActionOut(
            id=r.id,
            tool_name=r.tool_name,
            tool_args=json.loads(r.tool_args),
            summary=r.summary,
            status=r.status.value,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("/execute/action", response_model=ActionExecutionResult)
def confirm_and_execute_action(
    req: ActionDecisionRequest,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> ActionExecutionResult:
    action = db.get(PendingAction, req.action_id)
    if action is None or action.user_id != device.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    try:
        action = decide_action(db, req.action_id, req.approve)
        if req.approve:
            action = execute_action(db, req.action_id)
    except ActionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found") from exc
    except ActionNotApprovedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except UnknownToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown tool: {exc}") from exc

    return ActionExecutionResult(
        id=action.id,
        status=action.status.value,
        result=action.result,
        error=action.error,
        executed_at=action.executed_at,
    )
