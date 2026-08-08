"""SQLAlchemy ORM models for structured profile/action data (section 3.4 / 6)."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.crypto import decrypt_str, encrypt_str
from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EncryptedText(TypeDecorator):
    """A TEXT column that is transparently AES-256-GCM encrypted at rest.

    Used for anything privacy-sensitive: transcripts, voice-derived text,
    uploaded document contents. See app/crypto.py for key management.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt_str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt_str(value)


class ActionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    executed = "executed"
    failed = "failed"
    expired = "expired"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    display_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    devices: Mapped[list["Device"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    interactions: Mapped[list["Interaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Device(Base):
    """A paired mobile client. Auth tokens are scoped to a device, not just a user."""

    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    paired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    # Hash of the current valid refresh token (never store refresh tokens in plaintext).
    refresh_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="devices")


class Interaction(Base):
    """One voice exchange: transcript + response + detected emotional state.

    The embedding itself lives in the vector store (app/memory); this row is
    the structured/audit trail and what the vector store's metadata points
    back to.
    """

    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    device_id: Mapped[str | None] = mapped_column(ForeignKey("devices.id"), nullable=True)
    transcript: Mapped[str] = mapped_column(EncryptedText)
    response: Mapped[str] = mapped_column(EncryptedText)
    emotion_state: Mapped[str] = mapped_column(String(32), default="neutral")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User"] = relationship(back_populates="interactions")


class PendingAction(Base):
    """The confirmation-gate queue (section 3.5 / 6 "Action gating").

    Every non-read action the reasoning agent wants to take is written here
    as `pending` FIRST. It only becomes `executed` after an explicit
    approval via POST /execute/action. Nothing executes on proposal.
    """

    __tablename__ = "pending_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    device_id: Mapped[str | None] = mapped_column(ForeignKey("devices.id"), nullable=True)

    tool_name: Mapped[str] = mapped_column(String(128))
    # JSON-encoded arguments for the tool call, stored as text.
    tool_args: Mapped[str] = mapped_column(Text)
    # Human-readable description shown in the mobile confirmation dialog.
    summary: Mapped[str] = mapped_column(Text)

    status: Mapped[ActionStatus] = mapped_column(Enum(ActionStatus), default=ActionStatus.pending)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class ActionLog(Base):
    """Immutable audit log of every action that actually executed, with a timestamp."""

    __tablename__ = "action_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    pending_action_id: Mapped[str] = mapped_column(ForeignKey("pending_actions.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    tool_name: Mapped[str] = mapped_column(String(128))
    outcome: Mapped[str] = mapped_column(String(32))  # success | failure
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)


class Document(Base):
    """Metadata for a file uploaded via /train/upload and indexed into the context engine."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column()
    chunk_count: Mapped[int] = mapped_column(default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
