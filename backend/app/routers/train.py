"""POST /train/upload — training pipeline entry point (section 5, "Training Pipeline").

Implemented: file upload -> text extraction -> chunk -> embed -> index into
the vector store, plus a Document row for bookkeeping.

Stubbed (documented, not implemented — needs GPU infra this container
doesn't have): LoRA fine-tuning of the local model on the accumulated
corpus. See `queue_lora_finetune` below and backend/README.md.
"""
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.logging_config import get_logger
from app.memory.chunking import chunk_text
from app.memory.vector_store import get_vector_store
from app.models import Device, Document
from app.schemas import UploadResponse
from app.security import get_current_device

router = APIRouter(prefix="/train", tags=["train"])
logger = get_logger(__name__)

# Content types we know how to turn into plain text today. Anything else is
# stored as metadata-only with chunk_count=0 — see the TODO below.
_TEXT_LIKE_TYPES = {"text/plain", "text/markdown", "application/json", "text/csv"}


def queue_lora_finetune(user_id: str) -> None:
    """TODO(follow-up): trigger a LoRA fine-tune job on the accumulated
    training corpus for `user_id` and redeploy the updated model (section 5,
    step 3-4). Needs a GPU training environment this container doesn't have;
    left as a documented stub so the API shape is settled ahead of time.
    """
    logger.info("lora_finetune_stub_called", user_id=user_id)


@router.post("/upload", response_model=list[UploadResponse])
async def upload_training_data(
    files: list[UploadFile],
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> list[UploadResponse]:
    vector_store = get_vector_store()
    responses = []

    for file in files:
        raw = await file.read()
        content_type = file.content_type or "application/octet-stream"

        document = Document(
            user_id=device.user_id,
            filename=file.filename or "upload",
            content_type=content_type,
            size_bytes=len(raw),
        )

        indexed = False
        if content_type in _TEXT_LIKE_TYPES or (file.filename or "").endswith((".txt", ".md")):
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = ""

            chunks = chunk_text(text)
            if chunks:
                metadatas = [
                    {"user_id": device.user_id, "document_id": document.id, "type": "document", "chunk_index": i}
                    for i in range(len(chunks))
                ]
                vector_store.add_many(chunks, metadatas)
                document.chunk_count = len(chunks)
                indexed = True
        else:
            # TODO(follow-up): add parsers for PDF/DOCX/audio uploads (e.g.
            # via pypdf / python-docx / re-using the STT pipeline for voice
            # samples). For now these are stored as metadata only.
            logger.info("upload_not_indexed_unsupported_type", content_type=content_type, filename=file.filename)

        db.add(document)
        db.commit()
        db.refresh(document)

        responses.append(
            UploadResponse(
                document_id=document.id,
                filename=document.filename,
                chunk_count=document.chunk_count,
                indexed=indexed,
            )
        )

    queue_lora_finetune(device.user_id)
    return responses
