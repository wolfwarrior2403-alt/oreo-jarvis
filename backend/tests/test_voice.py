"""app.routers.voice with STT/prosody/emotion/agent all stubbed by the
autouse `stub_heavy_dependencies` fixture in conftest.py — this exercises
the request/response wiring and persistence, not the ML models themselves.
"""
import io


def test_process_voice_returns_transcript_and_response(client, auth_headers):
    audio_bytes = io.BytesIO(b"fake-wav-bytes")
    resp = client.post(
        "/voice/process",
        headers=auth_headers,
        files={"audio": ("clip.wav", audio_bytes, "audio/wav")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["transcript"] == "hello oreo, what's the weather"
    assert body["emotion_state"] == "neutral"
    assert body["response_text"] == "It's sunny today."
    assert body["proposed_action_id"] is None


def test_process_voice_requires_auth(client):
    audio_bytes = io.BytesIO(b"fake-wav-bytes")
    resp = client.post("/voice/process", files={"audio": ("clip.wav", audio_bytes, "audio/wav")})
    assert resp.status_code in (401, 403)


def test_process_voice_persists_interaction(client, auth_headers, paired_device):
    from app.db import SessionLocal
    from app.models import Interaction

    audio_bytes = io.BytesIO(b"fake-wav-bytes")
    client.post(
        "/voice/process",
        headers=auth_headers,
        files={"audio": ("clip.wav", audio_bytes, "audio/wav")},
    )

    db = SessionLocal()
    try:
        rows = db.query(Interaction).filter(Interaction.user_id == paired_device["user_id"]).all()
        assert len(rows) == 1
        # Transcript is stored via the EncryptedText type but reads back in plaintext.
        assert rows[0].transcript == "hello oreo, what's the weather"
    finally:
        db.close()
