"""Covers the section 6 "action gating" requirement end-to-end: a proposed
action must NOT execute until explicitly approved via POST /execute/action,
and a rejected action must never execute at all.
"""
from app.agent import actions as agent_actions
from app.db import SessionLocal


def _propose(paired_device, tool_name="calendar_create_event", tool_args=None, summary="do a thing"):
    db = SessionLocal()
    try:
        return agent_actions.propose_action(
            db,
            user_id=paired_device["user_id"],
            device_id=paired_device["device_id"],
            tool_name=tool_name,
            tool_args=tool_args or {"title": "Standup", "date": "2026-08-10", "time": "09:00"},
            summary=summary,
        )
    finally:
        db.close()


def test_proposed_action_appears_pending_and_does_not_auto_execute(client, paired_device, auth_headers):
    action = _propose(paired_device)

    resp = client.get("/actions/pending", headers=auth_headers)
    assert resp.status_code == 200
    pending_ids = [a["id"] for a in resp.json()]
    assert action.id in pending_ids

    db = SessionLocal()
    try:
        from app.models import PendingAction

        row = db.get(PendingAction, action.id)
        assert row.status.value == "pending"
        assert row.executed_at is None
    finally:
        db.close()


def test_approving_action_executes_it_and_logs_it(client, paired_device, auth_headers):
    action = _propose(paired_device, summary="Create event 'Standup' on 2026-08-10 at 09:00")

    resp = client.post(
        "/execute/action", json={"action_id": action.id, "approve": True}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "executed"
    assert body["executed_at"] is not None
    assert "Standup" in body["result"]

    resp = client.get("/actions/pending", headers=auth_headers)
    assert action.id not in [a["id"] for a in resp.json()]

    db = SessionLocal()
    try:
        from app.models import ActionLog

        logs = db.query(ActionLog).filter(ActionLog.pending_action_id == action.id).all()
        assert len(logs) == 1
        assert logs[0].outcome == "success"
        assert logs[0].executed_at is not None
    finally:
        db.close()


def test_rejecting_action_never_executes_it(client, paired_device, auth_headers):
    action = _propose(paired_device)

    resp = client.post(
        "/execute/action", json={"action_id": action.id, "approve": False}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejected"
    assert body["executed_at"] is None
    assert body["result"] is None


def test_cannot_execute_an_already_decided_action_again(client, paired_device, auth_headers):
    action = _propose(paired_device)

    first = client.post(
        "/execute/action", json={"action_id": action.id, "approve": True}, headers=auth_headers
    )
    assert first.status_code == 200

    second = client.post(
        "/execute/action", json={"action_id": action.id, "approve": True}, headers=auth_headers
    )
    assert second.status_code == 409


def test_cannot_act_on_another_users_action(client, paired_device, auth_headers):
    action = _propose(paired_device)

    other = client.post(
        "/auth/pair",
        json={"pairing_code": "test-pairing-code", "device_name": "other-phone", "user_email": "other@example.com"},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

    resp = client.post(
        "/execute/action", json={"action_id": action.id, "approve": True}, headers=other_headers
    )
    assert resp.status_code == 404
