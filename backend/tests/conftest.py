"""Test configuration.

Sets throwaway env vars BEFORE importing any `app.*` module (settings are
cached with lru_cache on first access), points the DB/vector-store/file
sandbox at a temp directory, and stubs out every heavy model call (Whisper,
Chroma embeddings, Ollama) so the suite runs fast and offline. See
backend/README.md for how to run against the real models locally.
"""
import base64
import os
import tempfile

_TMP_DIR = tempfile.mkdtemp(prefix="oreo-test-")
os.environ.setdefault("OREO_ENV", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key-that-is-long-enough-for-hs256")
os.environ.setdefault("DEVICE_PAIRING_CODE", "test-pairing-code")
os.environ.setdefault("DATA_ENCRYPTION_KEY", base64.urlsafe_b64encode(os.urandom(32)).decode())
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TMP_DIR}/test.db")
os.environ.setdefault("CHROMA_PERSIST_DIR", f"{_TMP_DIR}/chroma")
os.environ.setdefault("OREO_FILE_SANDBOX", f"{_TMP_DIR}/files")
os.environ.setdefault("TTS_BACKEND", "pyttsx3")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.agent.reasoning import AgentTurn  # noqa: E402
from app.db import init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.stt.emotion import EmotionResult  # noqa: E402
from app.stt.prosody import ProsodyFeatures  # noqa: E402
from app.stt.whisper_stt import TranscriptionResult  # noqa: E402


class FakeVectorStore:
    """In-memory stand-in for the Chroma-backed VectorStore, so tests never
    need to load a sentence-transformers embedding model."""

    def __init__(self):
        self.items: dict[str, tuple[str, dict]] = {}

    def add(self, text, metadata, doc_id=None):
        doc_id = doc_id or f"fake-{len(self.items)}"
        self.items[doc_id] = (text, metadata)
        return doc_id

    def add_many(self, texts, metadatas, ids=None):
        ids = ids or [f"fake-{len(self.items) + i}" for i in range(len(texts))]
        for doc_id, text, meta in zip(ids, texts, metadatas):
            self.items[doc_id] = (text, meta)
        return ids

    def query(self, text, n_results=5, where=None):
        return []

    def delete(self, doc_id):
        self.items.pop(doc_id, None)


@pytest.fixture(scope="session", autouse=True)
def _init_database():
    init_db()
    yield


@pytest.fixture(autouse=True)
def stub_heavy_dependencies(monkeypatch):
    """Replace Whisper/prosody/emotion-driven-by-audio/vector-store/LLM calls
    with deterministic fakes for every test, per the requirement that tests
    not need multi-GB model downloads to pass."""
    fake_store = FakeVectorStore()
    monkeypatch.setattr("app.routers.voice.get_vector_store", lambda: fake_store)
    monkeypatch.setattr("app.routers.train.get_vector_store", lambda: fake_store)

    fake_transcription = TranscriptionResult(
        text="hello oreo, what's the weather", language="en", duration_seconds=1.5, segments=[]
    )

    class FakeTranscriber:
        def transcribe(self, audio_path):
            return fake_transcription

    monkeypatch.setattr("app.routers.voice.get_transcriber", lambda: FakeTranscriber())

    fake_prosody = ProsodyFeatures(
        pitch_mean_hz=150.0, pitch_std_hz=10.0, jitter=0.01, pace_wpm=140.0, energy_rms=0.05
    )
    monkeypatch.setattr("app.routers.voice.extract_prosody", lambda *a, **k: fake_prosody)
    monkeypatch.setattr(
        "app.routers.voice.classify_state",
        lambda transcript, prosody: EmotionResult(state="neutral", confidence=0.5, signals={}),
    )

    class FakeAgent:
        def respond(self, **kwargs):
            return AgentTurn(response_text="It's sunny today.", proposed_action_id=None)

    monkeypatch.setattr("app.routers.voice.get_reasoning_agent", lambda: FakeAgent())

    yield fake_store


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def paired_device(client):
    resp = client.post(
        "/auth/pair",
        json={
            "pairing_code": os.environ["DEVICE_PAIRING_CODE"],
            "device_name": "test-phone",
            "user_display_name": "Test User",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture()
def auth_headers(paired_device):
    return {"Authorization": f"Bearer {paired_device['access_token']}"}
