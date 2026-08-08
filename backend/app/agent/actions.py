"""The confirmation-gate queue: propose -> approve/reject -> execute.

This module is the ONLY place non-read-only tool executors are ever
invoked, and only from execute_action(), and only when the action's status
is already `approved`. Every execution — success or failure — writes an
ActionLog row with a timestamp, per section 6's "action gating ... logged
with a timestamp" requirement.
"""
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agent.tools import get_tool
from app.logging_config import get_audit_logger
from app.models import ActionLog, ActionStatus, PendingAction

audit_logger = get_audit_logger()


class ActionNotFoundError(Exception):
    pass


class ActionNotApprovedError(Exception):
    pass


class UnknownToolError(Exception):
    pass


def propose_action(
    db: Session,
    user_id: str,
    device_id: str | None,
    tool_name: str,
    tool_args: dict,
    summary: str,
) -> PendingAction:
    action = PendingAction(
        user_id=user_id,
        device_id=device_id,
        tool_name=tool_name,
        tool_args=json.dumps(tool_args),
        summary=summary,
        status=ActionStatus.pending,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    audit_logger.info(
        "action_proposed",
        action_id=action.id,
        user_id=user_id,
        tool_name=tool_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return action


def decide_action(db: Session, action_id: str, approve: bool) -> PendingAction:
    action = db.get(PendingAction, action_id)
    if action is None:
        raise ActionNotFoundError(action_id)
    if action.status != ActionStatus.pending:
        raise ActionNotApprovedError(f"Action {action_id} is not pending (status={action.status}).")

    action.status = ActionStatus.approved if approve else ActionStatus.rejected
    action.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(action)

    audit_logger.info(
        "action_decided",
        action_id=action.id,
        approved=approve,
        timestamp=action.decided_at.isoformat(),
    )
    return action


def execute_action(db: Session, action_id: str) -> PendingAction:
    """Execute a previously-approved action. This is the single choke point
    where a proposed tool call actually takes effect."""
    action = db.get(PendingAction, action_id)
    if action is None:
        raise ActionNotFoundError(action_id)
    if action.status != ActionStatus.approved:
        raise ActionNotApprovedError(
            f"Action {action_id} must be approved before execution (status={action.status})."
        )

    tool = get_tool(action.tool_name)
    if tool is None:
        raise UnknownToolError(action.tool_name)

    args = json.loads(action.tool_args)
    now = datetime.now(timezone.utc)

    try:
        result = tool.executor(**args)
        action.status = ActionStatus.executed
        action.result = result
        action.executed_at = now
        outcome = "success"
        detail = result
    except Exception as exc:  # noqa: BLE001 — must always log + persist, even on unexpected tool errors
        action.status = ActionStatus.failed
        action.error = str(exc)
        action.executed_at = now
        outcome = "failure"
        detail = str(exc)

    db.add(
        ActionLog(
            pending_action_id=action.id,
            user_id=action.user_id,
            tool_name=action.tool_name,
            outcome=outcome,
            executed_at=now,
            detail=detail,
        )
    )
    db.commit()
    db.refresh(action)

    audit_logger.info(
        "action_executed",
        action_id=action.id,
        tool_name=action.tool_name,
        outcome=outcome,
        timestamp=now.isoformat(),
    )
    return action
