"""Utilities for managing the Telegram bot application lifecycle."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from functools import lru_cache
from urllib.parse import urlparse

from telegram.error import TelegramError
from telegram.ext import Application, ApplicationBuilder

from app.shared.config import settings
from app.bot.yandex_gpt import (
    YandexGPTConfigurationError,
    get_yandex_gpt_client,
)


logger = logging.getLogger(__name__)

WEBHOOK_ROUTE = "/bot/webhook"


def _normalize_https_endpoint(raw_url: str | None) -> str | None:
    if not raw_url:
        return None

    parsed = urlparse(raw_url)
    if parsed.scheme != "https" or not parsed.netloc:
        return None

    hostname = parsed.hostname or ""
    if hostname in {"localhost", "127.0.0.1"} or hostname.endswith("example.com"):
        return None

    return raw_url.rstrip("/")


def _resolve_webhook_url() -> str | None:
    """Return the webhook URL if it can be constructed from settings."""

    explicit_url = _normalize_https_endpoint(settings.telegram_webhook_url)
    if explicit_url:
        return explicit_url
    if settings.telegram_webhook_url:
        logger.warning("Ignoring TELEGRAM_WEBHOOK_URL – must be public HTTPS endpoint")

    base_url = _normalize_https_endpoint(settings.backend_base_url)
    if base_url:
        return f"{base_url}{WEBHOOK_ROUTE}"
    if settings.backend_base_url:
        logger.info(
            "Skipping webhook derivation from BACKEND_BASE_URL – requires public HTTPS endpoint"
        )

    return None


@lru_cache(maxsize=1)
def create_application() -> Application:
    """Create a Telegram application instance."""
    from app.bot.handlers import register_handlers

    logger.info(f"Initializing Telegram bot with token: {settings.telegram_bot_token[:10]}...")
    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .updater(None)
        .build()
    )
    register_handlers(application)
    return application


async def start_telegram_application(application: Application) -> None:
    """Start the Telegram application in webhook mode."""

    await application.initialize()
    await application.start()

    await _log_bot_identity(application)
    _log_ai_status()

    webhook_url = _resolve_webhook_url()
    if not webhook_url:
        await _ensure_webhook_disabled(application)
        _start_polling(application)
        logger.info(
            "Telegram webhook not configured – running without inbound updates. Set TELEGRAM_WEBHOOK_URL to a public HTTPS endpoint if needed."
        )
        return

    try:
        await application.bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    except TelegramError as exc:  # noqa: PERF203
        logger.warning("Failed to set Telegram webhook at %s: %s", webhook_url, exc)
    else:
        logger.info("Telegram webhook set to %s", webhook_url)


async def stop_telegram_application(application: Application) -> None:
    """Gracefully stop the Telegram application."""

    await _stop_polling()

    if application.bot:
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Telegram webhook removed")

    await application.stop()
    await application.shutdown()


_polling_task: asyncio.Task[None] | None = None


def _start_polling(application: Application) -> None:
    global _polling_task
    if _polling_task and not _polling_task.done():
        return

    logger.info("Starting Telegram long polling loop")
    _polling_task = asyncio.create_task(_poll_updates(application))


async def _stop_polling() -> None:
    global _polling_task
    if not _polling_task:
        return

    _polling_task.cancel()
    with suppress(asyncio.CancelledError):
        await _polling_task
    _polling_task = None
    logger.info("Stopped Telegram long polling loop")


async def _ensure_webhook_disabled(application: Application) -> None:
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
    except TelegramError as exc:  # noqa: PERF203
        logger.debug("Unable to delete Telegram webhook before polling: %s", exc)


async def _poll_updates(application: Application) -> None:
    offset = 0
    while True:
        try:
            updates = await application.bot.get_updates(offset=offset, timeout=30)
        except TelegramError as exc:  # noqa: PERF203
            logger.warning("Polling getUpdates failed: %s", exc)
            await asyncio.sleep(5)
            continue

        for update in updates:
            offset = max(offset, update.update_id + 1)
            await application.process_update(update)


async def _log_bot_identity(application: Application) -> None:
    try:
        profile = await application.bot.get_me()
    except TelegramError as exc:  # noqa: PERF203
        logger.error("Failed to authenticate Telegram bot token: %s", exc)
        raise

    username = f"@{profile.username}" if profile.username else profile.full_name or profile.id
    logger.info("Telegram bot authorized as %s (id=%s)", username, profile.id)


def _log_ai_status() -> None:
    try:
        client = get_yandex_gpt_client()
    except YandexGPTConfigurationError as exc:
        logger.warning("Yandex GPT disabled: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to initialize Yandex GPT client: %s", exc)
    else:
        logger.info("Yandex GPT client ready (folder_id=%s)", client.folder_id)
