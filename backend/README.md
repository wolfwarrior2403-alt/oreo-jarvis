# Oreo Backend

FastAPI gateway implementing architecture doc sections 3 and parts of 5/6:
auth (JWT + device pairing), speech-to-text, prosody/emotion detection, a
Chroma-backed context engine, a LangChain+Ollama reasoning agent with a
confirmation-gated action queue, TTS, structured audit logging, and a
training-data upload/indexing pipeline.

## Status at a glance

| Piece | Status |
|---|---|
| FastAPI app + all 6 endpoints from section 3.1 | ✅ Implemented |
| JWT auth + device pairing + refresh | ✅ Implemented |
| Faster-Whisper STT | ✅ Implemented (lazy-loaded; default model is small, not large-v3-turbo — see below) |
| Prosody extraction (librosa) | ✅ Implemented |
| Emotion classification | ✅ Implemented as a **rule-based** classifier (documented as a placeholder for a trained model — see `app/stt/emotion.py`) |
| Chroma vector store + SQLAlchemy profile DB | ✅ Implemented |
| Reasoning agent (LangChain + Ollama, tool calling) | ✅ Implemented; requires a running Ollama instance to actually respond (degrades gracefully with a clear message if unreachable) |
| Confirmation gate (propose → approve/reject → execute) | ✅ Implemented and covered by tests — this is the hard security requirement from section 6 |
| TTS (pyttsx3 default, Piper optional) | ✅ Implemented |
| AES-256-GCM encryption at rest for transcripts | ✅ Implemented (`app/crypto.py`) |
| `/train/upload` — text file chunk+embed+index | ✅ Implemented |
| `/train/upload` — PDF/DOCX/audio parsing | ⚠️ Stubbed (stored as metadata only, TODO in `app/routers/train.py`) |
| LoRA fine-tuning | ⚠️ Documented stub (`queue_lora_finetune` in `app/routers/train.py`) — needs GPU infra |
| Docker / docker-compose (Option B) | ✅ Implemented |
| pytest suite | ✅ 17 tests, all heavy model calls mocked, no downloads required |

## Setup

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `JWT_SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `DATA_ENCRYPTION_KEY` — generate with `python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`
- `DEVICE_PAIRING_CODE` — pick a code you'll hand to your phone during pairing

### Key management

`DATA_ENCRYPTION_KEY` is the AES-256 key protecting transcripts and other
sensitive columns at rest (section 6). Full details and rotation guidance
live in the docstring at the top of `app/crypto.py`; short version: for
personal/local use, keeping it in `.env` (which is gitignored) is enough;
for a cloud deployment, inject it via your provider's secrets manager
instead of baking it into the image. There's no automated key-rotation
tool yet — that's a documented follow-up.

### Run locally (Deployment Option A)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend creates its SQLite DB and Chroma persistence directory under
`./data/` on first run. Point your phone at `http://<this-machine's-LAN-IP>:8000`.

### Local LLM

Install [Ollama](https://ollama.com), then:
```bash
ollama pull llama3.2
```
`OLLAMA_MODEL`/`OLLAMA_BASE_URL` in `.env` control which model/host the
reasoning agent talks to. If Ollama isn't running, `/voice/process` still
responds (with a message saying it couldn't reach the reasoning model)
instead of crashing — see `app/agent/reasoning.py`.

### Speech-to-text model size

`WHISPER_MODEL_SIZE` defaults to `small` so local dev doesn't require a
multi-GB download. The architecture doc calls for `large-v3-turbo` for
production quality — set `WHISPER_MODEL_SIZE=large-v3-turbo` once you've
got the disk space and hardware for it (see faster-whisper's model list).

### Text-to-speech

`TTS_BACKEND=pyttsx3` (default) works out of the box using your OS's TTS
engine — on Linux this needs `espeak-ng` installed (`apt install
espeak-ng`; already included in the Dockerfile). Set `TTS_BACKEND=piper`
and `PIPER_MODEL_PATH` once you've downloaded a Piper voice model from
https://github.com/rhasspy/piper for more natural-sounding output.

## Running tests

```bash
pip install -r requirements.txt   # or just the test-relevant subset
pytest
```

The suite stubs every heavy dependency (Whisper, Chroma's embedding model,
Ollama) via `tests/conftest.py`'s `stub_heavy_dependencies` fixture, so it
runs in well under a second, fully offline, with no model downloads.

## Docker (Deployment Option B)

```bash
cp .env.example .env   # fill in real secrets
docker compose up -d
docker compose exec ollama ollama pull llama3.2   # first run only
```

This starts the backend plus a local Ollama container on the same Docker
network. Put a real reverse proxy / TLS terminator (nginx, Caddy, your
cloud provider's load balancer) in front of it before exposing it outside
your own network — the container itself serves plain HTTP.

For a pure-cloud deployment (no local Ollama container), delete the
`ollama` service from `docker-compose.yml`, point `OLLAMA_BASE_URL` at
wherever you're running Ollama instead, and deploy the `backend` service
with your cloud provider's container runtime (Cloud Run, ECS, etc.),
attaching a persistent volume for `/app/data` (SQLite DB + Chroma index).

## API surface

See `app/main.py` for the full router list; interactive docs are available
at `/docs` (Swagger UI) once the server is running.

| Endpoint | Auth | Notes |
|---|---|---|
| `GET /health` | none | liveness + whether Ollama is reachable |
| `POST /auth/pair` | pairing code | first-time handshake, returns JWT pair |
| `POST /auth/refresh` | refresh token | rotates both tokens |
| `POST /voice/process` | JWT | audio in, transcript+response+emotion out |
| `GET /context/user/{id}` | JWT (own user only) | recent interactions + doc count |
| `GET /actions/pending` | JWT | actions awaiting confirmation |
| `POST /execute/action` | JWT | approve/reject a pending action; only approval executes it |
| `POST /search/web` | JWT | read-only, no confirmation needed |
| `POST /train/upload` | JWT | upload + index training documents |

## Extending the tool registry

Custom, team-defined tools (section 3.5) go in `app/agent/tools.py` via
`register_tool(ToolSpec(...))`. Set `read_only=True` only for tools that
truly can't change anything — anything else automatically goes through the
confirmation gate the moment it's registered, with no extra wiring needed
(see that file's module docstring for how the gate actually works).
