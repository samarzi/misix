"""Supabase client wrapper and async helpers for MISIX backend."""

from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from app.shared.config import settings


logger = logging.getLogger(__name__)


class SupabaseNotConfiguredError(RuntimeError):
    """Raised when Supabase credentials are missing."""


USERS_TABLE = "users"
NOTES_TABLE = "notes"
TASKS_TABLE = "tasks"
ASSISTANT_SESSIONS_TABLE = "assistant_sessions"
ASSISTANT_MESSAGES_TABLE = "assistant_messages"


def supabase_available() -> bool:
    url = (settings.supabase_url or "").strip()
    service_key = (settings.supabase_service_key or "").strip()

    if not url or not service_key:
        return False

    if "your-project" in url or url.endswith("example.com"):
        return False

    if "replace-with" in service_key:
        return False

    return True


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    if not supabase_available():
        raise SupabaseNotConfiguredError("Supabase URL or service key not configured")

    try:
        return create_client(settings.supabase_url, settings.supabase_service_key)
    except TypeError as exc:  # Supabase SDK vs httpx version mismatch
        raise SupabaseNotConfiguredError(
            "Supabase client could not be initialized (httpx compatibility issue)."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise SupabaseNotConfiguredError(f"Supabase client initialization failed: {exc}") from exc


def _get_supabase_client_or_none() -> Client | None:
    if not supabase_available():
        return None

    try:
        return get_supabase_client()
    except SupabaseNotConfiguredError as exc:
        logger.warning("Supabase integration disabled: %s", exc)
        return None


async def _run_db_call(callable_: Any) -> Any:
    return await asyncio.to_thread(callable_)


async def ensure_user_record(
    telegram_id: int,
    *,
    username: str | None,
    full_name: str | None,
    language_code: str | None,
) -> None:
    client = _get_supabase_client_or_none()
    if client is None:
        logger.debug("Skipping ensure_user_record – Supabase not configured")
        return
    
    logger.debug(f"Upserting user record for telegram_id={telegram_id}")
    
    payload = {
        "telegram_id": telegram_id,
        "username": username,
        "full_name": full_name,
        "language_code": language_code,
    }

    try:
        await _run_db_call(
            lambda: client.table(USERS_TABLE).upsert(payload, on_conflict="telegram_id").execute()
        )
        logger.debug(f"Successfully upserted user record for telegram_id={telegram_id}")
    except Exception as e:
        logger.error(f"Failed to upsert user record for telegram_id={telegram_id}: {e}", exc_info=True)
        raise


async def create_note(
    telegram_id: int,
    content: str,
    *,
    source: str = "telegram",
) -> None:
    client = _get_supabase_client_or_none()
    if client is None:
        logger.debug("Skipping create_note – Supabase not configured")
        return
    
    logger.debug(f"Creating note for telegram_id={telegram_id}, source={source}")
    
    payload = {
        "telegram_id": telegram_id,
        "content": content,
        "source": source,
    }

    try:
        result = await _run_db_call(lambda: client.table(NOTES_TABLE).insert(payload).execute())
        logger.info(f"✅ Note created for telegram_id={telegram_id}")
        return result
    except Exception as e:
        logger.error(f"❌ Failed to create note for telegram_id={telegram_id}: {e}", exc_info=True)
        raise


async def create_task(
    telegram_id: int,
    title: str,
    *,
    status: str = "new",
    source: str = "telegram",
) -> None:
    client = _get_supabase_client_or_none()
    if client is None:
        logger.debug("Skipping create_task – Supabase not configured")
        return
    
    logger.debug(f"Creating task for telegram_id={telegram_id}, title='{title}', source={source}")
    
    payload = {
        "telegram_id": telegram_id,
        "title": title,
        "status": status,
        "source": source,
    }

    try:
        result = await _run_db_call(lambda: client.table(TASKS_TABLE).insert(payload).execute())
        logger.info(f"✅ Task created for telegram_id={telegram_id}: '{title}'")
        return result
    except Exception as e:
        logger.error(f"❌ Failed to create task for telegram_id={telegram_id}: {e}", exc_info=True)
        raise


async def log_assistant_message(
    telegram_id: int,
    role: str,
    content: str,
    *,
    session_id: str | None = None,
) -> None:
    client = _get_supabase_client_or_none()
    if client is None:
        logger.debug("Skipping log_assistant_message – Supabase not configured")
        return
    
    logger.debug(f"Logging assistant message for telegram_id={telegram_id}, role={role}")
    
    payload = {
        "telegram_id": telegram_id,
        "role": role,
        "content": content,
        "session_id": session_id,
    }

    try:
        result = await _run_db_call(
            lambda: client.table(ASSISTANT_MESSAGES_TABLE).insert(payload).execute()
        )
        logger.debug(f"Assistant message logged for telegram_id={telegram_id}")
        return result
    except Exception as e:
        logger.error(f"❌ Failed to log assistant message for telegram_id={telegram_id}: {e}", exc_info=True)
        raise
