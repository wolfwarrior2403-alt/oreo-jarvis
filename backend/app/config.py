"""Central application settings, loaded from environment variables / .env.

Nothing in this module hardcodes a secret — every credential-shaped value
must come from the environment. See backend/.env.example for the full list
and backend/README.md's "Key management" section for rotation guidance.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    oreo_env: str = "development"
    log_level: str = "INFO"

    # Auth / JWT
    jwt_secret_key: str = "changeme-generate-a-real-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    device_pairing_code: str = "changeme-pairing-code"

    # Encryption at rest
    data_encryption_key: str = "changeme-generate-a-32-byte-key"

    # Database
    database_url: str = "sqlite:///./data/oreo.db"

    # Vector store
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Speech to text
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # Reasoning agent
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    enable_web_search_tool: bool = True

    # Text to speech
    tts_backend: str = "pyttsx3"
    piper_model_path: str = "./data/tts/en_US-lessac-medium.onnx"

    # Data retention
    retain_raw_audio: bool = False

    @property
    def is_production(self) -> bool:
        return self.oreo_env.lower() in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
