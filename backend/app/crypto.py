"""AES-256-GCM encryption helpers for data-at-rest (section 6: "Storage").

Key management
--------------
The encryption key is read from the ``DATA_ENCRYPTION_KEY`` environment
variable (see .env.example) — it is never hardcoded and never logged.
It must be 32 url-safe base64-encoded bytes, generated with:

    python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"

For a personal/local deployment, keeping the key in the backend's own
environment (outside of git) is sufficient — the threat model is "someone
steals the laptop's disk," not "someone has root on the laptop while it's
running." For a team/cloud deployment (Option B), inject the key via your
cloud provider's secrets manager (e.g. a mounted secret / KMS-backed env
var) rather than a plain .env file baked into the image.

Key rotation is NOT implemented automatically: rotating the key requires
decrypting all existing encrypted columns with the old key and
re-encrypting with the new one. This module exposes ``encrypt``/``decrypt``
as the single choke point so a future migration script can do that; there
is no rotation tooling yet (tracked as a follow-up).
"""
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import get_settings

_NONCE_SIZE = 12  # 96-bit nonce, recommended size for AES-GCM


class EncryptionKeyError(RuntimeError):
    """Raised when DATA_ENCRYPTION_KEY is missing/malformed."""


def _load_key() -> bytes:
    settings = get_settings()
    raw = settings.data_encryption_key
    if not raw or raw.startswith("changeme"):
        raise EncryptionKeyError(
            "DATA_ENCRYPTION_KEY is not set to a real value. Generate one with "
            "`python -c \"import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())\"` "
            "and put it in your .env (see .env.example)."
        )
    try:
        key = base64.urlsafe_b64decode(raw)
    except Exception as exc:  # noqa: BLE001
        raise EncryptionKeyError("DATA_ENCRYPTION_KEY is not valid url-safe base64.") from exc
    if len(key) != 32:
        raise EncryptionKeyError("DATA_ENCRYPTION_KEY must decode to exactly 32 bytes for AES-256.")
    return key


def encrypt_bytes(plaintext: bytes) -> bytes:
    """Encrypt with AES-256-GCM. Returns nonce || ciphertext || tag."""
    key = _load_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return nonce + ciphertext


def decrypt_bytes(blob: bytes) -> bytes:
    key = _load_key()
    aesgcm = AESGCM(key)
    nonce, ciphertext = blob[:_NONCE_SIZE], blob[_NONCE_SIZE:]
    return aesgcm.decrypt(nonce, ciphertext, associated_data=None)


def encrypt_str(plaintext: str) -> str:
    """Encrypt a UTF-8 string, returning a base64 string suitable for a TEXT column."""
    return base64.b64encode(encrypt_bytes(plaintext.encode("utf-8"))).decode("ascii")


def decrypt_str(token: str) -> str:
    return decrypt_bytes(base64.b64decode(token)).decode("utf-8")
