"""Security utilities for MISIX backend."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.shared.config import settings


logger = logging.getLogger(__name__)


class EncryptionNotConfiguredError(RuntimeError):
    """Raised when encryption is required but no key is configured."""


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    key = (settings.encryption_key or "").strip()
    if not key:
        raise EncryptionNotConfiguredError(
            "MISIX_ENCRYPTION_KEY is not configured. Set it to a Fernet key."
        )

    try:
        return Fernet(key.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise EncryptionNotConfiguredError(
            "Invalid MISIX_ENCRYPTION_KEY. It must be a valid Fernet key."
        ) from exc


def is_encryption_available() -> bool:
    try:
        _get_fernet()
        return True
    except EncryptionNotConfiguredError:
        return False


def encrypt_text(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return value

    fernet = _get_fernet()
    token = fernet.encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return value

    fernet = _get_fernet()
    try:
        plaintext = fernet.decrypt(value.encode("utf-8"))
        return plaintext.decode("utf-8")
    except InvalidToken as exc:
        logger.error("Failed to decrypt value: invalid token")
        raise ValueError("Invalid encrypted value") from exc


def decrypt_safely(value: Optional[str]) -> Optional[str]:
    try:
        return decrypt_text(value)
    except (EncryptionNotConfiguredError, ValueError):
        return value
