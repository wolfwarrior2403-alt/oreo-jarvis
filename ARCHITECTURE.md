# Oreo — Personal AI Assistant: Complete System Architecture

> This is the original architecture doc this repository was built from,
> preserved verbatim for reference. See the top-level [README.md](README.md)
> for what's actually implemented today vs. still stubbed.

## 1. Overview

Oreo is a voice-first, context-aware AI assistant. It runs its heavy computation (LLM, speech processing, memory) on a laptop or cloud server, and connects to a lightweight mobile client. The wake word is "Oreo" and it works even when the phone is locked. Every action that changes something (sends a message, executes a command, modifies a file) requires voice confirmation before it runs.

The system is designed to be installed by other founders/teams, who can train it on their own voice data, documents, and workflows so it adapts to their specific business context.

## 2. High-Level Architecture

MOBILE CLIENT (Android/iOS) <--HTTPS/WSS--> BACKEND (Laptop/Cloud)
- Mobile: wake word detect, mic capture, confirmation UI, TTS playback
- Backend: FastAPI Gateway with: Auth (JWT), Speech-to-Text (Whisper), Emotion/Context Detector, Context Engine (Vector DB), Reasoning Agent (LLM+Tools), Text-to-Speech (XTTS/Piper), Action Executor (gated)

## 3. Backend

### 3.1 API Gateway (FastAPI)
Core endpoints:
- POST /voice/process — accepts audio, returns transcript + response
- GET /context/user/{id} — returns stored user profile/history
- POST /execute/action — runs a confirmed action
- POST /search/web — triggers web search when the model needs current info
- POST /train/upload — accepts voice/doc uploads for fine-tuning
- GET /health — status check

Each request is authenticated with a JWT bearer token issued at device pairing time.

### 3.2 Speech-to-Text
- Faster-Whisper (large-v3-turbo) for transcription
- Extracts prosody features (pitch, pace, jitter) alongside text for emotion detection

### 3.3 Emotion & Context Detection
- Sentiment/tone classifier runs on the transcript + prosody features
- Produces a lightweight state label (e.g., neutral, urgent, frustrated) that's passed to the reasoning layer so responses match the user's state

### 3.4 Context Engine (Memory)
- Vector store (FAISS or Chroma) holds embeddings of past conversations, decisions, and uploaded documents
- SQL database (SQLite for personal use, PostgreSQL for team deployments) holds structured user/team profile data
- Every interaction is embedded and stored so future queries can retrieve relevant history

### 3.5 Reasoning Layer
- Local LLM via Ollama or LM Studio (e.g., Llama 3.2, Qwen 3.5)
- LangChain or CrewAI for multi-step tool orchestration
- Tools: web search, calendar, file read/write, custom team-defined tools
- Every non-read action is gated behind explicit voice confirmation — the agent proposes, the user approves, then it executes

### 3.6 Text-to-Speech
- XTTS (Coqui) or Piper for natural-sounding responses, tone-matched to the detected emotional context

## 4. Frontend (Mobile Client)

### 4.1 Platform
Cross-platform build (Kivy/Flutter) targeting Android and iOS, so one codebase covers both.

### 4.2 Screens
1. Home/Listening screen — shows a passive listening indicator, waveform animation when active
2. Confirmation dialog — appears before any action executes; shows what Oreo intends to do, with Approve/Cancel
3. Conversation history — scrollable transcript of recent exchanges
4. Settings — wake word sensitivity, backend connection (local IP or cloud URL), voice/data retention controls

### 4.3 Background Behavior
- On-device wake-word model (Porcupine) runs continuously in a low-power background service, so it responds even when the phone is locked, without needing to unlock first
- On wake, it streams audio to the backend over the paired connection (local Wi-Fi or authenticated remote link)

## 5. Deployment

### Option A — Personal, Local
Backend runs on your own laptop. Phone connects over the same Wi-Fi network. Nothing leaves your machine.

### Option B — Cloud (for remote access or team use)
1. Containerize the backend with Docker
2. Deploy to your cloud provider (e.g., via Cloud Code / Cloud Run)
3. Attach persistent storage for the vector DB and user data
4. Put the API behind HTTPS with a real TLS certificate
5. Phone connects to the cloud URL instead of a local IP; same JWT auth applies

### Option C — Hybrid
Inference stays on your laptop (for speed and privacy); context/history is periodically synced to the cloud as backup, so multiple devices can share the same memory.

### Training Pipeline (for founders adapting it to their team)
1. Upload team voice recordings, documents, and workflow descriptions via /train/upload
2. Backend embeds and indexes them into the context engine
3. Optionally, LoRA fine-tune the local model on that data
4. Redeploy the updated model to the team's instance

## 6. Security

- Transport: TLS/HTTPS for all network traffic between phone and backend
- Auth: JWT tokens issued at pairing; short-lived, refreshable
- Storage: AES-256 encryption at rest for stored voice data and context DB
- Action gating: no destructive or external-facing action executes without explicit voice confirmation, logged with a timestamp
- Data minimization: raw audio is discarded after transcription unless the user opts in to keep it for training
- Local-first default: no data leaves the device/backend pair unless the user explicitly enables cloud sync

## 7. Suggested Build Order

1. FastAPI backend skeleton + Ollama integration
2. Speech-to-text pipeline (Faster-Whisper)
3. Context engine (vector store + SQL)
4. Reasoning agent with tool calling + confirmation gate
5. Text-to-speech output
6. Mobile client: wake word + mic capture + confirmation UI
7. Dockerize and deploy to cloud
8. Training/upload pipeline for team customization
