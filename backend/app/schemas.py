"""Pydantic request/response models for the API surface."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# --- Auth ---
class PairRequest(BaseModel):
    pairing_code: str
    device_name: str
    user_display_name: str = "Owner"
    user_email: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    device_id: str


class RefreshRequest(BaseModel):
    refresh_token: str


# --- Voice ---
class VoiceProcessResponse(BaseModel):
    transcript: str
    emotion_state: str
    response_text: str
    proposed_action_id: str | None = None
    audio_response_url: str | None = None


# --- Context ---
class UserContextResponse(BaseModel):
    user_id: str
    display_name: str
    recent_interactions: list[dict]
    document_count: int


# --- Actions ---
class ProposedActionOut(BaseModel):
    id: str
    tool_name: str
    tool_args: dict
    summary: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionDecisionRequest(BaseModel):
    action_id: str
    approve: bool


class ActionExecutionResult(BaseModel):
    id: str
    status: str
    result: str | None = None
    error: str | None = None
    executed_at: datetime | None = None


# --- Search ---
class WebSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    max_results: int = Field(default=5, ge=1, le=20)


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class WebSearchResponse(BaseModel):
    query: str
    results: list[WebSearchResult]


# --- Train / upload ---
class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    indexed: bool


# --- Health ---
class HealthResponse(BaseModel):
    status: str
    version: str
    ollama_reachable: bool | None = None
