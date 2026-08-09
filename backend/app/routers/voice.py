import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.agent.reasoning import get_reasoning_agent
from app.config import get_settings
from app.db import get_db
from app.logging_config import get_logger
from app.memory.vector_store import get_vector_store
from app.models import Device, Interaction
from app.schemas import VoiceProcessResponse
from app.security import get_current_device
from app.stt.emotion import classify_state
from app.stt.prosody import extract_prosody
from app.stt.whisper_stt import get_transcriber

router = APIRouter(prefix="/voice", tags=["voice"])
logger = get_logger(__name__)


@router.post("/process", response_model=VoiceProcessResponse)
async def process_voice(
    audio: UploadFile,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> VoiceProcessResponse:
    settings = get_settings()

    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        transcriber = get_transcriber()
        transcription = transcriber.transcribe(tmp_path)
        transcript = transcription.text

        prosody = extract_prosody(tmp_path, transcript_word_count=len(transcript.split()))
        emotion = classify_state(transcript, prosody)

        vector_store = get_vector_store()
        context_hits = vector_store.query(transcript, n_results=4, where={"user_id": device.user_id})
        context_snippets = [hit.text for hit in context_hits]

        agent = get_reasoning_agent()
        turn = agent.respond(
            db=db,
            user_id=device.user_id,
            device_id=device.id,
            user_text=transcript,
            emotion_state=emotion.state,
            context_snippets=context_snippets,
        )

        interaction = Interaction(
            user_id=device.user_id,
            device_id=device.id,
            transcript=transcript,
            response=turn.response_text,
            emotion_state=emotion.state,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        vector_store.add(
            text=f"User: {transcript}\nOreo: {turn.response_text}",
            metadata={"user_id": device.user_id, "interaction_id": interaction.id, "type": "interaction"},
            doc_id=interaction.id,
        )

        return VoiceProcessResponse(
            transcript=transcript,
            emotion_state=emotion.state,
            response_text=turn.response_text,
            proposed_action_id=turn.proposed_action_id,
        )
    finally:
        # Data minimization (section 6): raw audio is discarded unless the
        # user has explicitly opted in to keep it for training.
        if not settings.retain_raw_audio:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        else:
            logger.info("raw_audio_retained", path=tmp_path, device_id=device.id)
