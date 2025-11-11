"""Telegram bot handlers for MOZG assistant with natural language understanding."""

from __future__ import annotations

import logging
import re
import json
from datetime import datetime, timedelta, date, timezone
from zoneinfo import ZoneInfo
from typing import Final, Optional
from collections import deque


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from app.shared.config import settings
from app.shared.supabase import (
    get_supabase_client,
    supabase_available,
)
from app.bot.yandex_speech import get_yandex_speech_kit
from app.bot.yandex_gpt import (
    YandexGPTConfigurationError,
    get_yandex_gpt_client,
)


SLEEP_DELAY_MINUTES: Final = 15

CONVERSATION_BUFFER_LIMIT: Final = 6
SUMMARY_TRIGGER_MESSAGES: Final = 12
SUMMARY_TABLE_NAME: Final = "assistant_conversation_summaries"
MAX_STORED_MESSAGES_PER_USER: Final = 200
DEFAULT_TEASING_PERSONA_NAME: Final = "teasing"

_conversation_buffers: dict[str, deque] = {}
_conversation_message_counts: dict[str, int] = {}
_conversation_summary_cache: dict[str, Optional[str]] = {}

_default_teasing_persona_id: Optional[str] = None
_default_persona_lookup_failed: bool = False

def _get_conversation_buffer(user_id: str) -> deque:
    buffer = _conversation_buffers.get(user_id)
    if buffer is None:
        buffer = deque(maxlen=CONVERSATION_BUFFER_LIMIT)
        _conversation_buffers[user_id] = buffer
    return buffer

async def _load_latest_summary(user_id: str) -> Optional[str]:
    if not supabase_available():
        return None

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table(SUMMARY_TABLE_NAME)
            .select("summary")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            summary_value = response.data[0].get("summary")
            _conversation_summary_cache[user_id] = summary_value
            return summary_value
    except Exception as exc:
        logger.warning("Failed to load summary for %s: %s", user_id, exc)
    return None


async def _get_default_teasing_persona_id() -> Optional[str]:
    global _default_teasing_persona_id, _default_persona_lookup_failed

    if _default_teasing_persona_id is not None:
        return _default_teasing_persona_id
    if _default_persona_lookup_failed or not supabase_available():
        return None

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("assistant_personas")
            .select("id")
            .eq("name", DEFAULT_TEASING_PERSONA_NAME)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        if response.data:
            _default_teasing_persona_id = response.data[0].get("id")
            return _default_teasing_persona_id
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch default persona %s: %s", DEFAULT_TEASING_PERSONA_NAME, exc)

    _default_persona_lookup_failed = True
    return None

async def _store_summary(user_id: str, summary: str, telegram_id: int | None = None) -> None:
    if not supabase_available():
        return
    try:
        supabase = get_supabase_client()
        payload = {
            "user_id": user_id,
            "summary": summary,
        }
        if telegram_id is not None:
            payload["telegram_id"] = telegram_id
        supabase.table(SUMMARY_TABLE_NAME).insert(payload).execute()
        _conversation_summary_cache[user_id] = summary
    except Exception as exc:
        logger.warning("Failed to store summary for %s: %s", user_id, exc)

async def _prune_conversation_messages(user_id: str) -> None:
    if not supabase_available():
        return

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("assistant_messages")
            .select("id")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(MAX_STORED_MESSAGES_PER_USER, MAX_STORED_MESSAGES_PER_USER + 200)
            .execute()
        )

        if response.data:
            ids_to_delete = [row["id"] for row in response.data if row.get("id")]
            if ids_to_delete:
                supabase.table("assistant_messages").delete().in_("id", ids_to_delete).execute()
    except Exception as exc:
        logger.warning("Failed to prune conversation messages for %s: %s", user_id, exc)

async def _generate_summary(user_id: str, history: list[dict], previous_summary: Optional[str]) -> Optional[str]:
    try:
        client = get_yandex_gpt_client()
    except YandexGPTConfigurationError:
        return None

    summary_prompt_parts = [
        "Ты — MISIX, персональный ассистент. Сформулируй краткое резюме разговора.",
        "Используй не более 3 предложений. Укажи ключевые намерения пользователя и принятое ботом действие.",
    ]
    if previous_summary:
        summary_prompt_parts.append("Вот резюме предыдущих разговоров:")
        summary_prompt_parts.append(previous_summary)
    summary_prompt_parts.append("Вот последние сообщения:")

    conversation_text = []
    for msg in history:
        role = "Пользователь" if msg.get("role") == "user" else "Ассистент"
        conversation_text.append(f"{role}: {msg.get('text', '')}")

    summary_prompt_parts.append("\n".join(conversation_text))
    summary_prompt_parts.append("Ответь только резюме, без списка и без обращений.")

    summary_prompt = "\n\n".join(summary_prompt_parts)

    try:
        response = await client.chat([
            {"role": "system", "text": "Ты помогаешь вести краткие резюмы диалогов."},
            {"role": "user", "text": summary_prompt},
        ])
        return response.strip()
    except Exception as exc:
        logger.warning("Failed to generate summary for %s: %s", user_id, exc)
        return None


async def _record_conversation_piece(
    user_id: str,
    role: str,
    text: str,
    *,
    telegram_id: int | None,
    attempt_summary: bool = False,
) -> None:
    buffer = _get_conversation_buffer(user_id)
    buffer.append({"role": role, "text": text})

    count = _conversation_message_counts.get(user_id, 0) + 1
    # Cap count to avoid uncontrolled growth if summary fails repeatedly
    _conversation_message_counts[user_id] = min(count, SUMMARY_TRIGGER_MESSAGES + CONVERSATION_BUFFER_LIMIT)

    if not attempt_summary or _conversation_message_counts[user_id] < SUMMARY_TRIGGER_MESSAGES:
        return

    history_snapshot = list(buffer)
    previous_summary = _conversation_summary_cache.get(user_id)
    if previous_summary is None:
        previous_summary = await _load_latest_summary(user_id)
    summary = await _generate_summary(user_id, history_snapshot, previous_summary)
    if not summary:
        return

    await _store_summary(user_id, summary, telegram_id)

    # Keep only the last couple of exchanges in memory for continuation
    trimmed = deque(history_snapshot[-2:], maxlen=CONVERSATION_BUFFER_LIMIT)
    _conversation_buffers[user_id] = trimmed
    _conversation_message_counts[user_id] = 0
    await _prune_conversation_messages(user_id)


BUTTON_HELP: Final = "Помощь"
BUTTON_SLEEP_START: Final = "Я спать"
BUTTON_SLEEP_PAUSE: Final = "Пауза"
BUTTON_SLEEP_RESUME: Final = "Пуск"
BUTTON_SLEEP_STOP: Final = "Я проснулся"

ACTIVE_SLEEP_STATUSES: Final = {"pending", "sleeping"}
ANY_SLEEP_STATUSES: Final = ACTIVE_SLEEP_STATUSES | {"paused"}

SLEEP_START_PHRASES: Final = {BUTTON_SLEEP_START.lower(), "иду спать", "ложусь спать", "пора спать"}
SLEEP_STOP_PHRASES: Final = {BUTTON_SLEEP_STOP.lower(), "проснулся", "проснулась", "встал", "встала"}
SLEEP_PAUSE_PHRASES: Final = {BUTTON_SLEEP_PAUSE.lower(), "пауза"}
SLEEP_RESUME_PHRASES: Final = {BUTTON_SLEEP_RESUME.lower(), "продолжить", "продолжай"}

PERSONA_CALLBACK_PREFIX: Final = "persona:"

CONFIRMATION_ACCEPT_WORDS: Final = {"подтверждаю", "да", "ок", "верно", "хорошо", "согласен"}
CONFIRMATION_CANCEL_WORDS: Final = {"отмена", "отмени", "нет", "не надо", "откажись", "останови"}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except Exception:  # noqa: BLE001
        return None


def _format_datetime(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours} ч")
    if minutes:
        parts.append(f"{minutes} мин")
    if not parts:
        parts.append("< 1 минуты") if secs else parts.append("0 мин")
    return " ".join(parts)


def _build_default_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BUTTON_HELP, BUTTON_SLEEP_START]],
        resize_keyboard=True,
    )


def _build_sleep_keyboard(paused: bool) -> ReplyKeyboardMarkup:
    if paused:
        buttons = [[BUTTON_SLEEP_RESUME], [BUTTON_SLEEP_STOP]]
    else:
        buttons = [[BUTTON_SLEEP_PAUSE], [BUTTON_SLEEP_STOP]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def _current_keyboard(session: Optional[dict]) -> ReplyKeyboardMarkup:
    if session and session.get("status") in ANY_SLEEP_STATUSES:
        return _build_sleep_keyboard(session.get("status") == "paused")
    return _build_default_keyboard()


async def get_active_personas() -> list[dict]:
    if not supabase_available():
        return []

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("assistant_personas")
            .select("id", "display_name", "description")
            .eq("is_active", True)
            .order("display_name")
            .execute()
        )
        return response.data or []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch assistant personas: %s", exc)
        return []


async def get_persona_by_id(persona_id: str) -> Optional[dict]:
    if not supabase_available():
        return None

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("assistant_personas")
            .select("id", "display_name", "description", "system_prompt")
            .eq("id", persona_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch persona %s: %s", persona_id, exc)

    return None


async def ensure_user_assistant_settings(user_id: str) -> Optional[dict]:
    if not supabase_available():
        return None

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("user_assistant_settings")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        default_persona_id = await _get_default_teasing_persona_id()

        if response.data:
            settings_row = response.data[0]
            if settings_row.get("current_persona_id") or not default_persona_id:
                return settings_row

            updated = (
                supabase
                .table("user_assistant_settings")
                .update({"current_persona_id": default_persona_id})
                .eq("user_id", user_id)
                .execute()
            )
            if updated.data:
                return updated.data[0]
            settings_row["current_persona_id"] = default_persona_id
            return settings_row

        created = (
            supabase
            .table("user_assistant_settings")
            .insert({
                "user_id": user_id,
                **({"current_persona_id": default_persona_id} if default_persona_id else {}),
            })
            .execute()
        )
        if created.data:
            return created.data[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to ensure assistant settings for %s: %s", user_id, exc)

    return None


async def set_user_persona(user_id: str, persona_id: str) -> bool:
    if not supabase_available():
        return False

    try:
        supabase = get_supabase_client()
        updated = (
            supabase
            .table("user_assistant_settings")
            .update({"current_persona_id": persona_id})
            .eq("user_id", user_id)
            .execute()
        )
        if updated.data:
            return True

        inserted = (
            supabase
            .table("user_assistant_settings")
            .insert({"user_id": user_id, "current_persona_id": persona_id})
            .execute()
        )
        return bool(inserted.data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to set persona for %s: %s", user_id, exc)
        return False


async def get_user_persona_context(user_id: str) -> tuple[Optional[str], Optional[str]]:
    if not supabase_available():
        return None, None

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("user_assistant_settings")
            .select("current_persona_id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None, None

        persona_id = response.data[0].get("current_persona_id")
        if not persona_id:
            return None, None

        persona = await get_persona_by_id(persona_id)
        if persona:
            return persona.get("system_prompt"), persona.get("display_name")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load persona context for %s: %s", user_id, exc)

    return None, None


def _build_persona_keyboard(personas: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    current_row: list[InlineKeyboardButton] = []

    for persona in personas:
        button = InlineKeyboardButton(
            persona.get("display_name", "Персона"),
            callback_data=f"{PERSONA_CALLBACK_PREFIX}{persona['id']}",
        )
        current_row.append(button)

        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    return InlineKeyboardMarkup(rows)


def _persona_options_text(personas: list[dict]) -> str:
    lines = []
    for persona in personas:
        description = persona.get("description") or ""
        lines.append(f"• {persona.get('display_name', 'Персона')} — {description}")
    return "\n".join(lines)


async def _send_persona_selection(chat, personas: list[dict], *, current_persona_name: str | None = None) -> None:
    message_lines = ["🎭 Давай выберем стиль общения MISIX."]

    if current_persona_name:
        message_lines.append(f"Сейчас активен стиль: {current_persona_name}.")

    message_lines.append("")
    message_lines.append(_persona_options_text(personas))
    message_lines.append("")
    message_lines.append(
        "Нажми на кнопку ниже, чтобы выбрать. Переключить стиль можно в любое время командой /set_persona."
    )

    await chat.send_message("\n".join(message_lines), reply_markup=_build_persona_keyboard(personas))


async def _update_sleep_totals(session: dict, *, ensure_for_status: Optional[str] = None) -> dict:
    now = _now_utc()
    status = ensure_for_status or session.get("status")

    total_sleep = int(session.get("total_sleep_seconds") or 0)
    total_pause = int(session.get("total_pause_seconds") or 0)

    last_change = _parse_datetime(session.get("last_state_change"))
    paused_at = _parse_datetime(session.get("paused_at"))

    if status == "sleeping" and last_change:
        total_sleep += _elapsed_seconds(last_change, now)
    elif status == "paused" and paused_at:
        total_pause += _elapsed_seconds(paused_at, now)

    return {
        **session,
        "total_sleep_seconds": total_sleep,
        "total_pause_seconds": total_pause,
        "last_state_change": _format_datetime(now),
    }


async def _get_sleep_session(user_id: str) -> Optional[dict]:
    if not supabase_available():
        return None

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("sleep_sessions")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", list(ANY_SLEEP_STATUSES))
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch sleep session: %s", exc)

    return None


async def _update_sleep_session(session_id: str, updates: dict) -> Optional[dict]:
    if not supabase_available():
        return None

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("sleep_sessions")
            .update(updates)
            .eq("id", session_id)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to update sleep session %s: %s", session_id, exc)

    return None


async def _create_sleep_session(user_id: str) -> Optional[dict]:
    if not supabase_available():
        return None

    now = _now_utc()
    payload = {
        "user_id": user_id,
        "status": "pending",
        "initiated_at": _format_datetime(now),
        "last_state_change": _format_datetime(now),
        "auto_stop_at": _format_datetime(now + timedelta(hours=24)),
    }

    try:
        supabase = get_supabase_client()
        response = supabase.table("sleep_sessions").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to create sleep session: %s", exc)

    return None


async def _sync_sleep_session_state(session: dict) -> tuple[Optional[dict], list[str]]:
    now = _now_utc()
    notifications: list[str] = []
    status = session.get("status")

    auto_stop_at = _parse_datetime(session.get("auto_stop_at"))
    if auto_stop_at and now >= auto_stop_at:
        session = await _update_sleep_totals(session, ensure_for_status=status)

        updates = {
            "status": "auto_stopped",
            "total_sleep_seconds": session["total_sleep_seconds"],
            "total_pause_seconds": session["total_pause_seconds"],
            "sleep_ended_at": _format_datetime(auto_stop_at),
            "paused_at": None,
            "last_state_change": _format_datetime(auto_stop_at),
        }

        updated = await _update_sleep_session(session["id"], updates)
        if updated:
            duration_text = _format_sleep_summary(updated.get("total_sleep_seconds", 0))
            notifications.append(
                f"⏰ Прошло сутки, так что я сам тормознул счётчик сна. В итоге ты отлежался {duration_text}."
            )
        return None, notifications

    if status == "pending":
        last_change = _parse_datetime(session.get("last_state_change"))
        if last_change and now >= last_change + timedelta(minutes=SLEEP_DELAY_MINUTES):
            updates = {
                "status": "sleeping",
                "last_state_change": _format_datetime(now),
            }
            if not session.get("sleep_started_at"):
                updates["sleep_started_at"] = _format_datetime(now)

            updated = await _update_sleep_session(session["id"], updates)
            if updated:
                session = updated
            else:
                session = {**session, **updates}

    return session, notifications


async def _start_sleep_session(user_id: str) -> Optional[dict]:
    session = await _get_sleep_session(user_id)
    if session:
        return session

    return await _create_sleep_session(user_id)


async def _pause_sleep_session(session: dict) -> Optional[dict]:
    session = await _update_sleep_totals(session, ensure_for_status="sleeping")

    updates = {
        "status": "paused",
        "paused_at": _format_datetime(_now_utc()),
        "total_sleep_seconds": session["total_sleep_seconds"],
        "total_pause_seconds": session["total_pause_seconds"],
        "last_state_change": _format_datetime(_now_utc()),
    }
    return await _update_sleep_session(session["id"], updates)


async def _resume_sleep_session(session: dict) -> Optional[dict]:
    session = await _update_sleep_totals(session, ensure_for_status="paused")

    updates = {
        "status": "pending",
        "paused_at": None,
        "total_sleep_seconds": session["total_sleep_seconds"],
        "total_pause_seconds": session["total_pause_seconds"],
        "last_state_change": _format_datetime(_now_utc()),
    }
    return await _update_sleep_session(session["id"], updates)


async def _stop_sleep_session(session: dict, *, auto=False) -> Optional[dict]:
    status = session.get("status")
    session = await _update_sleep_totals(session, ensure_for_status=status)

    final_status = "auto_stopped" if auto else "finished"

    updates = {
        "status": final_status,
        "total_sleep_seconds": session["total_sleep_seconds"],
        "total_pause_seconds": session["total_pause_seconds"],
        "sleep_ended_at": _format_datetime(_now_utc()),
        "paused_at": None,
        "last_state_change": _format_datetime(_now_utc()),
    }
    return await _update_sleep_session(session["id"], updates)


async def _process_user_text(message, user_id: str, text: str, *, telegram_id: int | None, bot, context: ContextTypes.DEFAULT_TYPE | None) -> None:
    text = text.strip()
    if not text:
        return

    text_lower = text.lower()

    session: Optional[dict] = None
    notifications: list[str] = []

    try:
        session, notifications = await ensure_sleep_session_state(user_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to sync sleep session: %s", exc)
        session = None
        notifications = []

    try:
        if context is not None:
            pending_state = context.chat_data.get('pending_confirmation')
            if pending_state:
                pending_intent = pending_state.get('pending_intent')
                payload = pending_state.get('payload', {})

                if text_lower in CONFIRMATION_ACCEPT_WORDS:
                    if pending_intent == 'finance_transaction':
                        saved = await _commit_pending_finance_transaction(payload)
                        emoji = "💰" if saved.get('type') == 'income' else "💸"
                        amount = saved.get('amount', 0)
                        category = payload.get('category_name', 'Без категории')
                        await message.reply_text(
                            f"{emoji} Транзакция сохранена!\n"
                            f"Сумма: {amount}\n"
                            f"Категория: {category}"
                        )
                        context.chat_data.pop('pending_confirmation', None)
                        return

                if text_lower in CONFIRMATION_CANCEL_WORDS:
                    await message.reply_text("❎ Отменено. Если передумаешь — расскажи детали ещё раз.")
                    context.chat_data.pop('pending_confirmation', None)
                    return

    except Exception as exc:
        logger.warning("Sleep session check failed: %s", exc)

    keyboard = _current_keyboard(session)
    for note in notifications:
        await message.reply_text(note, reply_markup=keyboard)

    # Help command / button
    if text_lower in {"/help", "help", "помощь", BUTTON_HELP.lower()}:
        await message.reply_text(HELP_MESSAGE, reply_markup=_current_keyboard(session))
        return

    # Sleep controls
    if text_lower in SLEEP_START_PHRASES:
        if session and session.get("status") in ANY_SLEEP_STATUSES:
            await message.reply_text(
                "Ты уже валяешься под одеялом. Или паузу жми, или просыпайся, соня.",
                reply_markup=_build_sleep_keyboard(session.get("status") == "paused")
            )
            return

        new_session = await _start_sleep_session(user_id)
        if not new_session:
            await message.reply_text(
                "Не смог засечь твой сон. Проверь связь, а потом попробуем снова.",
                reply_markup=_current_keyboard(session)
            )
            return

        await message.reply_text(
            "🛌 Договорились, даю тебе 15 минут на засыпание, а потом засеку сон."
            " Если передумаешь — жми ‘Пауза’ или ‘Я проснулся’.",
            reply_markup=_build_sleep_keyboard(False)
        )
        return

    if text_lower in SLEEP_PAUSE_PHRASES:
        if not session or session.get("status") not in ANY_SLEEP_STATUSES:
            await message.reply_text(
                "Ты ещё даже не спишь. Сначала скажи ‘Я спать’, а потом уже паузы выдумывай.",
                reply_markup=_current_keyboard(session)
            )
            return

        if session.get("status") == "paused":
            await message.reply_text(
                "Ты и так на паузе. Или жми ‘Пуск’, или вставай уже.",
                reply_markup=_build_sleep_keyboard(True)
            )
            return

        updated = await _pause_sleep_session(session)
        if not updated:
            await message.reply_text(
                "Что-то не вышло с паузой. Попробуй ещё разок, хитрец.",
                reply_markup=_build_sleep_keyboard(False)
            )
            return

        await message.reply_text(
            "⏸️ Фиксирую паузу. Как только допьёшь воду — жми ‘Пуск’.",
            reply_markup=_build_sleep_keyboard(True)
        )
        return

    if text_lower in SLEEP_RESUME_PHRASES:
        if not session or session.get("status") != "paused":
            await message.reply_text(
                "Паузы не было, расслабься. Если хочешь лечь, нажимай ‘Я спать’.",
                reply_markup=_current_keyboard(session)
            )
            return

        updated = await _resume_sleep_session(session)
        if not updated:
            await message.reply_text(
                "Не смог снять паузу. Попробуй ещё раз, пока не уснул стоя.",
                reply_markup=_build_sleep_keyboard(True)
            )
            return

        await message.reply_text(
            "▶️ Ладно, снова тайм-аут на 15 минут, засыпай. Потом снова считаю сон.",
            reply_markup=_build_sleep_keyboard(False)
        )
        return

    if text_lower in SLEEP_STOP_PHRASES:
        if not session or session.get("status") not in ANY_SLEEP_STATUSES:
            await message.reply_text(
                "Ты ещё даже не спал. Может, сначала ляжем?",
                reply_markup=_current_keyboard(session)
            )
            return

        updated = await _stop_sleep_session(session)
        if not updated:
            await message.reply_text(
                "Хм, не получилось закрыть сессию. Давай повторим ‘Я проснулся’.",
                reply_markup=_build_sleep_keyboard(session.get("status") == "paused")
            )
            return

        slept = _format_sleep_summary(updated.get("total_sleep_seconds", 0))
        pauses = updated.get("total_pause_seconds", 0)
        pause_text = f" (пауза: {_format_duration(pauses)})" if pauses else ""

        await message.reply_text(
            f"☀️ Подъём! Ты проспал {slept}{pause_text}. Возвращаю все функции ассистента.",
            reply_markup=_build_default_keyboard()
        )
        return

    # If user is in sleep mode, block casual chatting
    if session and session.get("status") in ANY_SLEEP_STATUSES:
        status = session.get("status")
        if status == "paused":
            prompt = "Ты на паузе. Или продолжай ‘Пуск’, или просыпайся. Болтать будем позже."
        elif status == "pending":
            prompt = "Ты ещё засыпаешь. Досыпай 15 минут или жми ‘Пауза’ / ‘Я проснулся’."
        else:
            prompt = "Ты спишь. Или ставь паузу, или просыпайся — болтовня потом."

        await message.reply_text(
            prompt,
            reply_markup=_build_sleep_keyboard(status == "paused")
        )
        return

    # Try to process structured data before free-form chat, so UI shows it even если AI недоступен
    structured_intent_handled = False
    try:
        structured_intent_handled = await process_and_save_structured_data(
            message,
            user_id,
            text,
            telegram_id=telegram_id,
        )
    except Exception as data_error:  # noqa: BLE001
        logger.error("Structured data pre-processing failed: %s", data_error)

    if structured_intent_handled:
        return

    if _should_skip_message(user_id, text):
        logger.info("Skipping duplicate message for user %s", user_id)
        return

    # Regular AI response flow
    try:
        if bot is not None:
            await bot.send_chat_action(chat_id=message.chat_id, action="typing")

        conversation_history = await get_conversation_history(user_id, limit=20)
        ai_response = await get_ai_response(text, conversation_history, user_id=user_id)

        await message.reply_text(ai_response, reply_markup=_current_keyboard(session))

    except Exception as exc:
        logger.error("AI processing failed: %s", exc)
        fallback = get_fallback_response(text)
        if fallback:
            await message.reply_text(fallback, reply_markup=_current_keyboard(session))

        try:
            await process_and_save_structured_data(message, user_id, text, telegram_id=telegram_id)
        except Exception as data_error:  # noqa: BLE001
            logger.error("Data saving also failed: %s", data_error)

        await _record_conversation_piece(
            user_id,
            "user",
            text,
            telegram_id=telegram_id,
        )
        if fallback:
            await _record_conversation_piece(
                user_id,
                "assistant",
                fallback,
                telegram_id=telegram_id,
                attempt_summary=True,
            )
        return

    try:
        await save_conversation_to_db(user_id, text, ai_response, telegram_id=telegram_id, session=session)
    except Exception as conv_error:  # noqa: BLE001
        logger.error("Failed to save conversation: %s", conv_error)

    await _record_conversation_piece(
        user_id,
        "user",
        text,
        telegram_id=telegram_id,
    )
    await _record_conversation_piece(
        user_id,
        "assistant",
        ai_response,
        telegram_id=telegram_id,
        attempt_summary=True,
    )


logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT: Final[str] = (
    """Ты - MISIX, персональный AI-ассистент. Ты можешь:

1. Отвечать на любые вопросы и вести разговоры
2. Помогать с задачами, заметками, финансами
3. Отвечать на вопросы о мире, науке, истории
4. Быть полезным и дружелюбным

Отвечай естественно, как человек. Если пользователь просит создать задачу или заметку, или сообщает о расходах - ты все равно должен ответить на его сообщение, а структурированные данные сохранятся автоматически.

ВАЖНО: Используй историю разговора для понимания контекста и поддержания непрерывного диалога."""
)

WELCOME_MESSAGE: Final[str] = (
    "🤖 Привет! Я MISIX — ваш персональный AI-ассистент!\n\n"
    "💬 Пишите или говорите мне на русском:\n"
    "• «Добавь задачу на завтра купить хлеб»\n"
    "• «Создай заметку о встрече с командой»\n"
    "• «Какие у меня задачи на сегодня?»\n"
    "• «Что ты умеешь?»\n\n"
    "🎤 Отправляйте голосовые сообщения — я их распознаю!\n\n"
    "Я пойму и выполню!"
)

HELP_MESSAGE: Final[str] = (
    "🤖 MISIX — ваш персональный AI-ассистент!\n\n"
    "💬 ОСНОВНЫЕ КОМАНДЫ:\n"
    "• «/start» — приветствие и регистрация\n"
    "• «/help» — эта справка\n"
    "• «/profile» — информация о профиле\n"
    "• «/set_persona» — выбрать характер ассистента\n\n"
    "🎤 ГОЛОСОВЫЕ СООБЩЕНИЯ:\n"
    "• Отправляйте голосовые сообщения — я их распознаю!\n"
    "• Говорите естественно, как с человеком\n\n"
    "💰 ФИНАНСЫ:\n"
    "• «Потратил 34 рубля на хлеб»\n"
    "• «Получил зарплату 50 000 рублей»\n"
    "• «Покажи баланс» / «Мои расходы»\n\n"
    "✅ ЗАДАЧИ:\n"
    "• «Добавь задачу купить продукты»\n"
    "• «Напомни завтра в 9:00 позавтракать»\n"
    "• «Покажи мои задачи»\n\n"
    "📝 ЗАМЕТКИ:\n"
    "• «Создай заметку о встрече»\n"
    "• «Запомни этот рецепт»\n"
    "• «Покажи мои заметки»\n\n"
    "🔐 ЛИЧНЫЕ ДАННЫЕ:\n"
    "• «Сохрани логин: user@gmail.com пароль: pass123»\n"
    "• «Сохрани контакт: Иван телефон: +7 999 123-45-67»\n\n"
    "😊 НАСТРОЕНИЕ И ДНЕВНИК:\n"
    "• «Настроение отличное, выучил 20 слов»\n"
    "• «Сегодня был тяжелый день»\n"
    "• «Запись благодарности: благодарен за поддержку»\n\n"
    "🎭 НАСТРОЙКИ:\n"
    "• «Профиль» / «Настройки» — управление профилем\n"
    "• «Смени персона» — выбрать характер ассистента\n\n"
    "🌐 ВЕБ-ИНТЕРФЕЙС:\n"
    "Все данные доступны в веб-приложении для подробного просмотра и редактирования!\n\n"
    "🚀 Просто пишите или говорите естественно — я пойму!"
)


def _elapsed_seconds(start: Optional[datetime], end: datetime) -> int:
    if not start:
        return 0
    delta = end - start
    return max(0, int(delta.total_seconds()))


def _total_sleep_with_elapsed(session: dict, end_time: datetime) -> int:
    total = int(session.get("total_sleep_seconds") or 0)
    if session.get("status") == "sleeping":
        last_change = _parse_datetime(session.get("last_state_change"))
        total += _elapsed_seconds(last_change, end_time)
    return total


def _total_pause_with_elapsed(session: dict, end_time: datetime) -> int:
    total = int(session.get("total_pause_seconds") or 0)
    if session.get("status") == "paused":
        paused_at = _parse_datetime(session.get("paused_at"))
        total += _elapsed_seconds(paused_at, end_time)
    return total


def _format_sleep_summary(total_seconds: int) -> str:
    return _format_duration(total_seconds)


async def get_active_sleep_session(user_id: str) -> Optional[dict]:
    if not supabase_available():
        return None

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("sleep_sessions")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", list(ANY_SLEEP_STATUSES))
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch active sleep session: %s", exc)

    return None


async def _update_sleep_session(session_id: str, updates: dict) -> Optional[dict]:
    if not supabase_available():
        return None

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table("sleep_sessions")
            .update(updates)
            .eq("id", session_id)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to update sleep session %s: %s", session_id, exc)

    return None


async def _create_sleep_session(user_id: str) -> Optional[dict]:
    if not supabase_available():
        return None

    now = _now_utc()
    payload = {
        "user_id": user_id,
        "status": "pending",
        "initiated_at": _format_datetime(now),
        "last_state_change": _format_datetime(now),
        "auto_stop_at": _format_datetime(now + timedelta(hours=24)),
    }

    try:
        supabase = get_supabase_client()
        response = supabase.table("sleep_sessions").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to create sleep session: %s", exc)

    return None


async def _sync_sleep_session_state(session: dict) -> tuple[Optional[dict], list[str]]:
    now = _now_utc()
    notifications: list[str] = []
    status = session.get("status")

    auto_stop_at = _parse_datetime(session.get("auto_stop_at"))
    if auto_stop_at and now >= auto_stop_at:
        total_sleep = _total_sleep_with_elapsed(session, auto_stop_at)
        total_pause = _total_pause_with_elapsed(session, auto_stop_at)

        updates = {
            "status": "auto_stopped",
            "total_sleep_seconds": total_sleep,
            "total_pause_seconds": total_pause,
            "sleep_ended_at": _format_datetime(auto_stop_at),
            "paused_at": None,
            "last_state_change": _format_datetime(auto_stop_at),
        }

        updated = await _update_sleep_session(session["id"], updates)
        if updated:
            duration_text = _format_sleep_summary(total_sleep)
            notifications.append(
                f"⏰ Прошло сутки, так что я сам тормознул счётчик сна. В итоге ты отлежался {duration_text}."
            )
        return None, notifications

    if status == "pending":
        last_change = _parse_datetime(session.get("last_state_change"))
        if last_change and now >= last_change + timedelta(minutes=SLEEP_DELAY_MINUTES):
            updates = {
                "status": "sleeping",
                "last_state_change": _format_datetime(now),
            }
            if not session.get("sleep_started_at"):
                updates["sleep_started_at"] = _format_datetime(now)

            updated = await _update_sleep_session(session["id"], updates)
            if updated:
                session = updated
            else:
                session = {**session, **updates}

    return session, notifications


async def ensure_sleep_session_state(user_id: str) -> tuple[Optional[dict], list[str]]:
    session = await get_active_sleep_session(user_id)
    if not session:
        return None, []

    updated_session, notifications = await _sync_sleep_session_state(session)
    return updated_session, notifications


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message and user registration."""
    user = update.effective_user
    if not user:
        return

    try:
        user_id = await get_or_create_user(user.id, user.username, user.full_name)
    except Exception as exc:
        logger.error("Failed to register user on /start: %s", exc)
        await update.effective_chat.send_message("❌ Не удалось зарегистрировать тебя. Попробуй позже.")
        return

    if supabase_available():
        try:
            supabase = get_supabase_client()
            supabase.table("users").update({
                "username": user.username,
                "full_name": user.full_name or f"{user.first_name or ''} {user.last_name or ''}".strip(),
                "language_code": user.language_code,
            }).eq("id", user_id).execute()
        except Exception as exc:
            logger.warning("Failed to update user profile info: %s", exc)

    settings = await ensure_user_assistant_settings(user_id)

    session, notifications = await ensure_sleep_session_state(user_id)
    keyboard = _current_keyboard(session)

    await update.effective_chat.send_message(WELCOME_MESSAGE, reply_markup=keyboard)
    for note in notifications:
        await update.effective_chat.send_message(note, reply_markup=keyboard)

    if settings and not settings.get("current_persona_id"):
        personas = await get_active_personas()
        if personas:
            await _send_persona_selection(update.effective_chat, personas)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information."""
    user = update.effective_user
    if not user:
        await update.effective_chat.send_message(HELP_MESSAGE, reply_markup=_build_default_keyboard())
        return

    try:
        user_id = await get_or_create_user(user.id, user.username, user.full_name)
    except Exception as exc:
        logger.error("Failed to ensure user for /help: %s", exc)
        await update.effective_chat.send_message(HELP_MESSAGE, reply_markup=_build_default_keyboard())
        return

    session, notifications = await ensure_sleep_session_state(user_id)
    keyboard = _current_keyboard(session)

    await update.effective_chat.send_message(HELP_MESSAGE, reply_markup=keyboard)
    for note in notifications:
        await update.effective_chat.send_message(note, reply_markup=keyboard)


async def set_persona_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allow user to select or change assistant persona."""
    chat = update.effective_chat
    user = update.effective_user

    if not user or not chat:
        return

    if not supabase_available():
        await chat.send_message("❌ Персонализация недоступна — база данных не настроена.")
        return

    try:
        user_id = await get_or_create_user(user.id, user.username, user.full_name)
    except Exception as exc:
        logger.error("Failed to prepare persona selection: %s", exc)
        await chat.send_message("❌ Не удалось подготовить список персонажей. Попробуй позже.")
        return

    settings = await ensure_user_assistant_settings(user_id)
    personas = await get_active_personas()

    if not personas:
        await chat.send_message("😴 Пока нет доступных персонажей. Загляни позже.")
        return

    current_name: str | None = None
    if settings and settings.get("current_persona_id"):
        persona = await get_persona_by_id(settings["current_persona_id"])
        if persona:
            current_name = persona.get("display_name")

    await _send_persona_selection(chat, personas, current_persona_name=current_name)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show stored profile data for the user."""
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    try:
        user_id = await get_or_create_user(user.id, user.username, user.full_name)
    except Exception as exc:
        logger.error("Failed to prepare profile: %s", exc)
        await message.reply_text("❌ Не смог напомнить, кто ты. Попробуй позже.")
        return

    if not supabase_available():
        await message.reply_text("📴 База данных недоступна — профиль пока не показать.")
        return

    try:
        supabase = get_supabase_client()
        user_response = (
            supabase
            .table("users")
            .select("full_name", "username", "email", "created_at")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        profile_response = (
            supabase
            .table("user_profile_data")
            .select("data_key", "data_value", "category")
            .eq("user_id", user_id)
            .order("category")
            .order("data_key")
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load profile data: %s", exc)
        await message.reply_text("❌ Что-то пошло не так, не смог собрать профиль.")
        return

    lines: list[str] = ["🧾 Вот что я о тебе помню:"]

    if user_response.data:
        base = user_response.data[0]
        full_name = base.get("full_name") or "—"
        username = base.get("username") or "—"
        email = base.get("email") or "—"
        created_at_text = "—"
        created_at = _parse_datetime(base.get("created_at"))
        if created_at:
            created_at_text = created_at.strftime("%d.%m.%Y")

        lines.extend(
            [
                f"Имя: {full_name}",
                f"Логин: @{username}" if username != "—" else "Логин: —",
                f"Почта: {email}",
                f"Со мной с: {created_at_text}",
            ]
        )
    else:
        lines.append("Основные данные ещё пустые.")

    profile_items = profile_response.data or []
    if profile_items:
        lines.append("")
        lines.append("Личные параметры:")
        for item in profile_items:
            key = item.get("data_key") or "ключ"
            value = item.get("data_value") or "—"
            category = item.get("category") or "general"
            pretty_key = key.replace("_", " ").title()
            lines.append(f"• [{category}] {pretty_key}: {value}")
    else:
        lines.append("")
        lines.append("Личные параметры пока не заполнены. Самое время поправить!")

    lines.append("")
    lines.append("Данные можно редактировать через веб-панель или прямо сообщениями.")

    await message.reply_text("\n".join(lines))


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show assistant settings info."""
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    try:
        user_id = await get_or_create_user(user.id, user.username, user.full_name)
    except Exception as exc:
        logger.error("Failed to prepare settings: %s", exc)
        await message.reply_text("❌ Не смог проверить настройки, попробуй позже.")
        return

    if not supabase_available():
        await message.reply_text("📴 База данных недоступна — настройки не достать.")
        return

    await handle_assistant_settings(message, user_id)


async def delete_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete all stored user data from Supabase."""
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not supabase_available():
        await message.reply_text("📴 База данных недоступна — ничего не удалил.")
        return

    try:
        user_id = await get_or_create_user(user.id, user.username, user.full_name)
    except Exception as exc:
        logger.error("Failed to resolve user before deletion: %s", exc)
        await message.reply_text("❌ Не опознал тебя, поэтому ничего не удалил.")
        return

    supabase = get_supabase_client()
    tables_to_wipe = [
        "assistant_messages",
        "assistant_sessions",
        "sleep_sessions",
        "tasks",
        "notes",
        "finance_transactions",
        "finance_categories",
        "mood_entries",
        "diary_entries",
        "personal_data_entries",
        "personal_data_categories",
        "user_event_history",
        "user_profile_data",
    ]

    failed_tables: list[str] = []

    for table in tables_to_wipe:
        try:
            supabase.table(table).delete().eq("user_id", user_id).execute()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to wipe %s for user %s: %s", table, user_id, exc)
            failed_tables.append(table)

    try:
        supabase.table("user_assistant_settings").delete().eq("user_id", user_id).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to wipe user_assistant_settings for %s: %s", user_id, exc)
        failed_tables.append("user_assistant_settings")

    try:
        supabase.table("users").delete().eq("id", user_id).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to delete user row %s: %s", user_id, exc)
        failed_tables.append("users")

    if failed_tables:
        readable = ", ".join(sorted(set(failed_tables)))
        await message.reply_text(
            "⚠️ Почистил не всё. Таблицы, которые заупрямились: " + readable + "."
        )
    else:
        await message.reply_text(
            "🧹 Всё стер подчистую. Если передумаешь — просто напиши, начнём историю заново."
        )


async def get_or_create_user(telegram_id: int, username: str = None, full_name: str = None) -> str:
    """Get or create user and return user_id."""
    try:
        supabase = get_supabase_client()
        logger.info(f"Checking user with telegram_id: {telegram_id} (type: {type(telegram_id)})")

        # telegram_id should remain as integer for Supabase bigint field
        response = supabase.table("users").select("id").eq("telegram_id", telegram_id).execute()
        logger.info(f"User lookup response: {response.data}")

        if response.data and len(response.data) > 0:
            user_id = response.data[0]["id"]
            logger.info(f"Found existing user: {user_id}")
            return user_id

        # User doesn't exist, create new one
        logger.info("Creating new user...")
        user_data = {
            "telegram_id": telegram_id,  # Keep as integer
            "username": username,
            "full_name": full_name or f"User {telegram_id}",
            "email": f"telegram_{telegram_id}@temp.local",  # Temporary email for telegram users
            "password_hash": "telegram_user",  # Placeholder, telegram users don't need passwords
        }

        logger.info(f"Creating user with data: {user_data}")
        response = supabase.table("users").insert(user_data).execute()
        logger.info(f"User creation response: {response.data}")

        if response.data and len(response.data) > 0:
            user_id = response.data[0]["id"]
            logger.info(f"Created new user: {user_id}")
            return user_id

        logger.error("Failed to create user - no data in response")
        raise Exception("Failed to create user - no response data")

    except Exception as e:
        logger.error(f"Database error in get_or_create_user: {e}", exc_info=True)
        raise Exception(f"Database error: {str(e)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main message handler with AI responses and data saving."""
    message = update.message
    user = update.effective_user

    if not message or not user or not message.text:
        return

    text = message.text or ""

    # Get or create user
    try:
        user_id = await get_or_create_user(user.id, user.username, user.full_name)
    except Exception as e:
        logger.error(f"Failed to get/create user: {e}")
        await message.reply_text("❌ Ошибка регистрации пользователя.")
        return

    await ensure_user_assistant_settings(user_id)

    logger.info(f"Processing message from user {user_id}: {text}")

    await _process_user_text(
        message,
        user_id,
        text,
        telegram_id=user.id,
        bot=context.bot,
        context=context,
    )


async def get_conversation_history(user_id: str, limit: int = 20) -> list[dict]:
    """Get recent conversation history for a user."""
    buffer = _get_conversation_buffer(user_id)

    if not buffer and supabase_available():
        try:
            supabase = get_supabase_client()
            response = (
                supabase
                .table("assistant_messages")
                .select("role", "content")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(CONVERSATION_BUFFER_LIMIT)
                .execute()
            )
            if response.data:
                for msg in reversed(response.data):
                    buffer.append({"role": msg["role"], "text": msg["content"]})
                _conversation_message_counts[user_id] = len(buffer)
        except Exception as exc:
            logger.warning("Failed to hydrate conversation buffer for %s: %s", user_id, exc)

    result: list[dict] = []
    summary_text = _conversation_summary_cache.get(user_id)
    if summary_text is None:
        summary_text = await _load_latest_summary(user_id)

    if summary_text:
        result.append({
            "role": "system",
            "text": f"Краткое резюме предыдущих разговоров: {summary_text}",
        })

    if buffer:
        history_slice = list(buffer)[-limit:]
        result.extend(history_slice)

    return result


async def process_transcribed_text(update: Update, context: ContextTypes.DEFAULT_TYPE, transcribed_text: str) -> None:
    """Process transcribed text from voice messages as regular text."""
    message = update.message
    user = update.effective_user

    if not message or not user or not transcribed_text.strip():
        return

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Get or create user
    try:
        user_id = await get_or_create_user(user.id, user.username, user.full_name)
    except Exception as e:
        logger.error(f"Failed to get/create user: {e}")
        await message.reply_text("❌ Ошибка регистрации пользователя.")
        return

    text = transcribed_text.strip()

    logger.info(f"Processing transcribed text from user {user_id}: {text}")

    await _process_user_text(
        message,
        user_id,
        text,
        telegram_id=user.id,
        bot=context.bot,
        context=context,
    )


async def save_conversation_to_db(user_id: str, user_message: str, ai_response: str, telegram_id: int | None = None) -> None:
    """Save conversation to database."""
    if not supabase_available():
        logger.warning("Supabase not available, skipping conversation save")
        return

    try:
        supabase = get_supabase_client()
        logger.info(f"Saving conversation for user_id: {user_id}, telegram_id: {telegram_id}")

        # Save user message
        user_payload = {
            "user_id": user_id,
            "role": "user",
            "content": user_message
        }
        if telegram_id is not None:
            user_payload["telegram_id"] = telegram_id
            
        user_result = supabase.table("assistant_messages").insert(user_payload).execute()
        logger.info(f"User message saved: {user_result.data}")

        # Save AI response
        ai_payload = {
            "user_id": user_id,
            "role": "assistant",
            "content": ai_response
        }
        if telegram_id is not None:
            ai_payload["telegram_id"] = telegram_id
            
        ai_result = supabase.table("assistant_messages").insert(ai_payload).execute()
        logger.info(f"AI response saved: {ai_result.data}")

        logger.info("Conversation saved to database successfully")

    except Exception as e:
        logger.error(f"Failed to save conversation: {e}", exc_info=True)


_recent_processed_messages: dict[str, tuple[str, float]] = {}
RECENT_MESSAGE_TTL_SECONDS = 10.0


def _should_skip_message(user_id: str, text: str) -> bool:
    """Detect duplicate messages coming from web UI double-submit."""
    key = user_id
    now = datetime.utcnow().timestamp()
    entry = _recent_processed_messages.get(key)
    if entry and entry[0] == text and (now - entry[1]) < RECENT_MESSAGE_TTL_SECONDS:
        return True
    _recent_processed_messages[key] = (text, now)
    return False


async def process_and_save_structured_data(message, user_id: str, text: str, telegram_id: int | None = None) -> bool:
    """Try to detect and save structured data (tasks, finances, etc.) without blocking AI response.

    Returns True if a structured intent was detected and handled (so regular chat response is not required).
    """
    try:
        # Try AI analysis for intent detection
        analysis = None
        try:
            analysis_prompt = f"""
            Проанализируй сообщение пользователя и определи, нужно ли сохранить структурированные данные.
            Верни JSON с полями:
            - intent: "create_task", "create_note", "finance_transaction", "mood_entry", "diary_entry", "health_entry", "list_health" или "none"
            - title: название задачи или заметки (если применимо)
            - description: описание (если применимо)
            - deadline: дата в формате YYYY-MM-DD (если упоминается "завтра", "послезавтра" и т.д.)
            - priority: "low", "medium", "high", "critical" (если можно определить)

            Сообщение пользователя: "{text}"

            Если это просто разговор или вопрос - верни intent: "none"
            """

            client = get_yandex_gpt_client()
            analysis_result = await client.chat([{ "role": "user", "text": analysis_prompt }])
            analysis = json.loads(analysis_result)
            intent = analysis.get('intent', 'none')

        except Exception as e:
            logger.warning(f"AI analysis failed, using fallback: {e}")
            intent = determine_intent_simple(text)
            analysis = None

        # Save structured data based on intent
        actionable_intents = {
            'create_task',
            'create_note',
            'finance_transaction',
            'create_debt',
            'create_reminder',
            'mood_entry',
            'diary_entry',
            'personal_data',
            'health_entry',
            'list_tasks',
            'list_notes',
            'list_finances',
            'list_health'
        }

        if intent in actionable_intents:
            title = analysis.get('title') if analysis else text
            description = analysis.get('description') if analysis else text
            deadline = analysis.get('deadline') if analysis else None
            priority = analysis.get('priority', 'medium') if analysis else 'medium'

            await execute_intent(
                message,
                user_id,
                intent,
                title,
                description,
                deadline,
                priority,
                raw_text=text,
                telegram_id=telegram_id,
            )
            return True

    except Exception as e:
        logger.warning(f"Structured data processing failed: {e}")
        # Don't show error to user, just log it

    return False


async def save_task_data(user_id: str, title: str, description: str, deadline: str = None, priority: str = 'medium') -> None:
    """Save task to database."""
    if not supabase_available():
        return

    try:
        supabase = get_supabase_client()
        task_data = {
            "user_id": user_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "new"
        }
        if deadline:
            task_data["deadline"] = deadline

        await supabase.table("tasks").insert(task_data).execute()
        logger.info(f"Task saved: {title}")

    except Exception as e:
        logger.warning(f"Failed to save note: {e}")


def _parse_amount(text: str) -> Optional[float]:
    match = re.search(r"(\d+(?:[\.,]\d{1,2})?)", text)
    if not match:
        return None
    return float(match.group(1).replace(',', '.'))


def _parse_counterparty(text: str) -> Optional[str]:
    match = re.search(r"(\b[А-ЯA-ZЁ][а-яa-zё]+(?:\s+[А-ЯA-ZЁ][а-яa-zё]+)*)", text)
    if match:
        return match.group(1)
    if 'я' in text.lower() or 'мне' in text.lower():
        return 'лично'
    return None


def _parse_direction(text: str) -> str:
    lowered = text.lower()
    if any(keyword in lowered for keyword in ['мне должны', 'мне вернут', 'вернут мне', 'должны вернуть', 'он должен', 'она должна', 'они должны']):
        return 'owed_to_me'
    if any(keyword in lowered for keyword in ['я должен', 'я верну', 'я вернул', 'я занял', 'я займ', 'я одолжил']):
        return 'owed_by_me'
    if 'мне' in lowered and 'должен' in lowered:
        return 'owed_to_me'
    if 'должен' in lowered:
        return 'owed_by_me'
    return 'owed_by_me'


def _parse_due_date(text: str) -> Optional[str]:
    lowered = text.lower()
    today = datetime.now().date()
    if 'сегодня' in lowered:
        return today.isoformat()
    if 'завтра' in lowered:
        return (today + timedelta(days=1)).isoformat()
    if 'послезавтра' in lowered:
        return (today + timedelta(days=2)).isoformat()
    match = re.search(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?", text)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else today.year
        try:
            return date(year, month, day).isoformat()
        except Exception as e:
            logger.warning(f"Failed to save finance data: {e}")
    return None


async def save_debt_entry(
    user_id: str,
    *,
    counterparty: str,
    amount: float,
    direction: str,
    due_date: str | None,
    notes: str | None = None,
    telegram_id: int | None = None,
) -> None:
    if not supabase_available():
        return

    payload = {
        "user_id": user_id,
        "counterparty": counterparty,
        "amount": amount,
        "currency": "RUB",
        "direction": direction,
        "status": "pending",
        "due_date": due_date,
        "notes": notes,
    }
    if telegram_id is not None:
        payload["telegram_id"] = telegram_id

    try:
        supabase = get_supabase_client()
        await supabase.table("finance_debts").insert(payload).execute()
        logger.info("Debt entry saved: %s", counterparty)
    except Exception as exc:
        logger.warning("Failed to save debt entry: %s", exc)


async def save_reminder_entry(
    user_id: str,
    *,
    title: str,
    reminder_time: datetime,
    timezone_name: str,
    recurrence_rule: str | None = None,
    payload_data: dict | None = None,
    telegram_id: int | None = None,
) -> None:
    if not supabase_available():
        return

    reminder_dt = reminder_time
    if reminder_dt.tzinfo is None:
        try:
            reminder_dt = reminder_dt.replace(tzinfo=ZoneInfo(timezone_name))
        except Exception:  # noqa: BLE001
            reminder_dt = reminder_dt.replace(tzinfo=ZoneInfo("Europe/Moscow"))
            timezone_name = "Europe/Moscow"

    data = {
        "user_id": user_id,
        "title": title,
        "reminder_time": reminder_dt.isoformat(),
        "timezone": timezone_name,
        "status": "scheduled",
        "recurrence_rule": recurrence_rule,
        "payload": payload_data,
    }
    if telegram_id is not None:
        data["telegram_id"] = telegram_id

    try:
        supabase = get_supabase_client()
        await supabase.table("reminders").insert(data).execute()
        logger.info("Reminder saved for %s at %s", user_id, reminder_dt.isoformat())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to save reminder: %s", exc)


def _parse_datetime_with_timezone(text: str) -> tuple[Optional[datetime], Optional[str]]:
    lowered = text.lower()
    now = datetime.now()
    timezone_name = None
    if 'мск' in lowered or 'москов' in lowered or 'msk' in lowered:
        timezone_name = 'Europe/Moscow'
    elif 'utc' in lowered:
        timezone_name = 'UTC'

    match = re.search(r"(\d{1,2}):(\d{2})", text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        base_date = now.date()
        if 'завтра' in lowered:
            base_date = base_date + timedelta(days=1)
        elif 'послезавтра' in lowered:
            base_date = base_date + timedelta(days=2)
        elif 'сегодня' not in lowered:
            match_date = re.search(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?", text)
            if match_date:
                day = int(match_date.group(1))
                month = int(match_date.group(2))
                year = int(match_date.group(3)) if match_date.group(3) else base_date.year
                try:
                    base_date = date(year, month, day)
                except ValueError:
                    base_date = now.date()
        try:
            reminder_dt = datetime.combine(base_date, datetime.min.time()).replace(hour=hours, minute=minutes)
            if timezone_name:
                tz = ZoneInfo(timezone_name)
                reminder_dt = reminder_dt.replace(tzinfo=tz)
            return reminder_dt, timezone_name or 'Europe/Moscow'
        except ValueError:
            return None, timezone_name or 'Europe/Moscow'
    return None, timezone_name or 'Europe/Moscow'


async def save_note_data(user_id: str, title: str, content: str) -> None:
    """Save note to database."""
    if not supabase_available():
        return

    try:
        supabase = get_supabase_client()
        note_data = {
            "user_id": user_id,
            "title": title,
            "content": content,
            "content_format": "markdown"
        }

        await supabase.table("notes").insert(note_data).execute()
        logger.info(f"Note saved: {title}")

    except Exception as e:
        logger.warning(f"Failed to save note: {e}")


FINANCE_CATEGORY_KEYWORDS: dict[str, str] = {
    'продукт': 'Продукты',
    'магазин': 'Продукты',
    'еда': 'Продукты',
    'обед': 'Продукты',
    'завтрак': 'Продукты',
    'ужин': 'Продукты',
    'кафе': 'Кафе и рестораны',
    'ресторан': 'Кафе и рестораны',
    'доставка': 'Кафе и рестораны',
    'такси': 'Транспорт',
    'метро': 'Транспорт',
    'автобус': 'Транспорт',
    'поезд': 'Транспорт',
    'кино': 'Развлечения',
    'кинотеатр': 'Развлечения',
    'развлеч': 'Развлечения',
    'игра': 'Развлечения',
    'подписка': 'Развлечения',
    'здоров': 'Здоровье',
    'аптека': 'Здоровье',
    'врач': 'Здоровье',
    'телефон': 'Связь',
    'интернет': 'Связь',
    'коммунал': 'Коммунальные услуги',
    'квартплата': 'Коммунальные услуги',
    'спорт': 'Спорт',
    'фитнес': 'Спорт',
    'спортзал': 'Спорт',
    'одежд': 'Одежда',
    'одежда': 'Одежда',
    'зарплат': 'Зарплата',
    'преми': 'Зарплата',
    'фриланс': 'Фриланс',
    'процент': 'Инвестиции',
    'инвест': 'Инвестиции',
}


def infer_finance_category(text_lower: str, transaction_type: str) -> Optional[str]:
    for keyword, category in FINANCE_CATEGORY_KEYWORDS.items():
        if keyword in text_lower:
            if transaction_type == 'income' and category in {'Зарплата', 'Фриланс', 'Инвестиции'}:
                return category
            if transaction_type == 'expense' and category not in {'Зарплата', 'Фриланс', 'Инвестиции'}:
                return category

    if transaction_type == 'income':
        return 'Зарплата'
    return 'Прочее'


async def ensure_finance_category(supabase, user_id: str, category_name: str, category_type: str) -> Optional[str]:
    try:
        lookup = supabase.table("finance_categories") \
            .select("id") \
            .eq("user_id", user_id) \
            .eq("name", category_name) \
            .eq("type", category_type) \
            .limit(1) \
            .execute()

        if lookup.data:
            return lookup.data[0]["id"]

        payload = {
            "user_id": user_id,
            "name": category_name,
            "type": category_type,
            "is_default": False,
        }

        created = supabase.table("finance_categories").insert(payload).execute()
        if created.data:
            return created.data[0]["id"]

    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to ensure finance category %s: %s", category_name, exc)

    return None


async def save_finance_data(user_id: str, raw_text: str, *, category_name: str | None = None) -> None:
    """Save finance transaction to database."""
    if not supabase_available():
        return

    try:
        supabase = get_supabase_client()

        amount_match = re.search(r'(\d+(?:[\.,]\d{1,2})?)', raw_text)
        if not amount_match:
            logger.info("No amount found in finance text: %s", raw_text)
            return

        amount = float(amount_match.group(1).replace(',', '.'))
        text_lower = raw_text.lower()

        if any(word in text_lower for word in ['получил', 'заработал', 'доход', 'зарплата', 'премия']):
            transaction_type = 'income'
            default_category = 'Зарплата'
        else:
            transaction_type = 'expense'
            default_category = 'Продукты'

        category_to_use = category_name or infer_finance_category(text_lower, transaction_type) or default_category

        category_id = None
        if category_to_use:
            category_id = await ensure_finance_category(supabase, user_id, category_to_use, transaction_type)

        cleaned_description = re.sub(r'(потратил|купил|заплатил|получил|заработал|стоимость|цена|оплатил)', '', raw_text, flags=re.IGNORECASE)
        cleaned_description = re.sub(r'(\d+(?:[\.,]\d{1,2})?)', '', cleaned_description).strip()

        transaction_data = {
            "user_id": user_id,
            "amount": amount,
            "type": transaction_type,
            "description": cleaned_description or raw_text[:200],
            "merchant": cleaned_description[:50] if cleaned_description else None,
            "transaction_date": datetime.utcnow().isoformat(),
            "notes": raw_text,
        }

        if category_id:
            transaction_data["category_id"] = category_id

        await supabase.table("finance_transactions").insert(transaction_data).execute()
        logger.info("Finance transaction saved: %s %s (%s)", transaction_type, amount, category_to_use)

    except Exception as e:
        logger.warning(f"Failed to save finance data: {e}")


HEALTH_TYPE_KEYWORDS: dict[str, list[str]] = {
    'weight': ['вес', 'вешу', 'килограм', 'kg', 'кг'],
    'pulse': ['пульс', 'ударов', 'сердцебиение'],
    'blood_pressure': ['давление', 'верхнее', 'нижнее'],
    'temperature': ['температур', 'градус', 'жар'],
    'sleep': ['спал', 'спала', 'сон', 'выспался', 'спал'],
    'steps': ['шаг', 'шагов', 'шаги', 'steps'],
    'glucose': ['сахар', 'глюкоз', 'глюкоза'],
    'water': ['выпил', 'выпила', 'воды', 'вода', 'литр', 'литра'],
}


def _parse_number(value: str) -> Optional[float]:
    cleaned = value.replace(' ', '').replace(',', '.').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _match_any(text_lower: str, keywords: list[str]) -> bool:
    return any(keyword in text_lower for keyword in keywords)


def parse_health_metrics(text: str) -> list[dict[str, str | float | None]]:
    text_lower = text.lower()
    metrics: list[dict[str, str | float | None]] = []
    consumed_spans: list[tuple[int, int]] = []

    def _span_consumed(start: int, end: int) -> bool:
        return any(start < existing_end and end > existing_start for existing_start, existing_end in consumed_spans)

    # Blood pressure (120/80) or "давление 120 на 80"
    for match in re.finditer(r'(\d{2,3})\s*(?:/|\\|на)\s*(\d{2,3})', text_lower):
        systolic = _parse_number(match.group(1))
        diastolic_value = _parse_number(match.group(2))
        if systolic is None:
            continue
        note = f"Диастолическое: {int(diastolic_value)}" if diastolic_value is not None else None
        metrics.append({
            'metric_type': 'blood_pressure',
            'metric_value': systolic,
            'unit': 'mmHg',
            'note': note,
        })
        consumed_spans.append(match.span())

    number_pattern = re.compile(r'\d+(?:[\s\.,]\d+)?')

    for match in number_pattern.finditer(text_lower):
        span = match.span()
        if _span_consumed(*span):
            continue

        value = _parse_number(match.group(0))
        if value is None:
            continue

        window_start = max(0, span[0] - 25)
        window_end = min(len(text_lower), span[1] + 25)
        window = text_lower[window_start:window_end]

        identified_type: Optional[str] = None
        for metric_type, keywords in HEALTH_TYPE_KEYWORDS.items():
            if any(keyword in window for keyword in keywords):
                identified_type = metric_type
                break

        if not identified_type:
            continue

        unit = None
        note = None
        metric_value = value

        if identified_type == 'weight':
            unit = 'kg'
        elif identified_type == 'pulse':
            unit = 'bpm'
        elif identified_type == 'temperature':
            unit = '°C'
        elif identified_type == 'steps':
            unit = 'steps'
            metric_value = float(int(metric_value))
        elif identified_type == 'glucose':
            unit = 'mmol/L'
        elif identified_type == 'water':
            unit = 'liters'
            if 'мл' in window:
                unit = 'ml'
                metric_value = round(metric_value, 2)
        elif identified_type == 'sleep':
            hours_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*час', window)
            minutes_match = re.search(r'(\d+)\s*мин', window)
            hours = metric_value
            if hours_match:
                hours = _parse_number(hours_match.group(1)) or hours
            if minutes_match:
                minutes = int(minutes_match.group(1))
                hours = (hours or 0) + minutes / 60
            elif 'мин' in window and 'час' not in window:
                hours = metric_value / 60
            metric_value = round(hours or metric_value, 2)
            unit = 'hours'

        metrics.append({
            'metric_type': identified_type,
            'metric_value': metric_value,
            'unit': unit,
            'note': note,
        })
        consumed_spans.append(span)

    return metrics


async def save_health_metric(user_id: str, data: dict[str, str | float | None]) -> None:
    if not supabase_available():
        return

    payload = {
        'user_id': user_id,
        'metric_type': data.get('metric_type'),
        'metric_value': data.get('metric_value'),
        'unit': data.get('unit'),
        'note': data.get('note'),
        'recorded_at': datetime.utcnow().isoformat(),
    }

    try:
        supabase = get_supabase_client()
        await supabase.table('health_metrics').insert(payload).execute()
        logger.info("Health metric saved: %s", payload['metric_type'])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to save health metric: %s", exc)


async def fetch_recent_health_metrics(user_id: str, limit: int = 5) -> list[dict]:
    if not supabase_available():
        return []

    try:
        supabase = get_supabase_client()
        response = (
            supabase
            .table('health_metrics')
            .select('*')
            .eq('user_id', user_id)
            .order('recorded_at', desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to fetch health metrics: %s", exc)
        return []


def _format_health_metric_line(metric: dict) -> str:
    value = metric.get('metric_value')
    unit = metric.get('unit')
    metric_type = metric.get('metric_type')
    note = metric.get('note')
    recorded_at = metric.get('recorded_at') or metric.get('created_at')
    timestamp = ''
    dt = _parse_datetime(recorded_at)
    if dt:
        timestamp = dt.strftime('%d.%m %H:%M')

    value_text = f"{value}" if value is not None else '?'
    if unit:
        value_text = f"{value_text} {unit}"

    note_part = f" — {note}" if note else ''
    time_part = f" ({timestamp})" if timestamp else ''

    readable_type = {
        'weight': 'Вес',
        'pulse': 'Пульс',
        'blood_pressure': 'Давление',
        'temperature': 'Температура',
        'sleep': 'Сон',
        'steps': 'Шаги',
        'glucose': 'Сахар',
        'water': 'Вода',
    }.get(metric_type, metric_type or 'Показатель')

    return f"• {readable_type}: {value_text}{note_part}{time_part}"


async def save_mood_data(user_id: str, text: str) -> None:
    """Save mood entry to database."""
    if not supabase_available():
        return

    try:
        supabase = get_supabase_client()
        from datetime import date

        # Simple mood detection
        text_lower = text.lower()
        mood_level = 5  # neutral default

        if any(word in text_lower for word in ['отлично', 'великолепно', 'супер']):
            mood_level = 9
        elif any(word in text_lower for word in ['хорошо', 'нормально']):
            mood_level = 7
        elif any(word in text_lower for word in ['плохо', 'ужасно', 'устал']):
            mood_level = 3

        mood_data = {
            "user_id": user_id,
            "mood_level": mood_level,
            "mood_description": text[:200],
            "entry_date": date.today()
        }

        await supabase.table("mood_entries").insert(mood_data).execute()
        logger.info(f"Mood entry saved: level {mood_level}")

    except Exception as e:
        logger.warning(f"Failed to save mood data: {e}")


async def save_diary_data(user_id: str, text: str) -> None:
    """Save diary entry to database."""
    if not supabase_available():
        return

    try:
        supabase = get_supabase_client()
        from datetime import date

        diary_data = {
            "user_id": user_id,
            "title": f"Запись {date.today().strftime('%d.%m.%Y')}",
            "content": text,
            "entry_type": "general",
            "entry_date": date.today()
        }

        await supabase.table("diary_entries").insert(diary_data).execute()
        logger.info("Diary entry saved")

    except Exception as e:
        logger.warning(f"Failed to save diary data: {e}")


def determine_intent_simple(text: str) -> str:
    """Simple intent detection based on keywords for MISIX."""
    text_lower = text.lower()

    # Finance transactions
    if any(word in text_lower for word in ['потратил', 'купил', 'заплатил', 'расход', 'цена', 'получил', 'заработал', 'доход', 'зарплата', 'оплата']):
        return 'finance_transaction'

    # Debts
    if any(word in text_lower for word in ['долг', 'должен', 'одолжил', 'вернуть', 'занял', 'занять']):
        return 'create_debt'

    # Reminders
    if any(word in text_lower for word in ['напомни', 'напоминание', 'напомни мне', 'напомин', 'не забудь']):
        return 'create_reminder'

    # Task creation (enhanced)
    if any(word in text_lower for word in ['добавь задачу', 'создай задачу', 'новая задача', 'задача', 'сделать', 'напомни']):
        return 'create_task'

    # Note creation (enhanced)
    if any(word in text_lower for word in ['создай заметку', 'запиши', 'запомни', 'заметка']):
        return 'create_note'

    # Personal data (logins, contacts)
    if any(word in text_lower for word in ['сохрани логин', 'сохрани пароль', 'логин', 'пароль', 'контакт', 'телефон']):
        return 'personal_data'

    # Mood tracking
    if any(word in text_lower for word in ['настроение', 'чувствую', 'эмоции', 'мood', 'настрой']):
        return 'mood_entry'

    # Diary entries
    if any(word in text_lower for word in ['дневник', 'запись дня', 'благодарность', 'размышление']):
        return 'diary_entry'

    # Health metrics
    if any(word in text_lower for word in ['вес', 'пульс', 'давлен', 'температур', 'шагов', 'сон', 'вода', 'глюкоз', 'сахар']):
        return 'health_entry'

    # List commands (enhanced)
    if any(word in text_lower for word in ['покажи задачи', 'мои задачи', 'список задач', 'какие задачи']):
        return 'list_tasks'

    if any(word in text_lower for word in ['покажи заметки', 'мои заметки', 'какие заметки', 'список заметок']):
        return 'list_notes'

    if any(word in text_lower for word in ['покажи расходы', 'мои расходы', 'финансы', 'баланс']):
        return 'list_finances'

    if any(word in text_lower for word in ['покажи здоровье', 'мои показатели', 'что по здоровью', 'статистика здоровья']):
        return 'list_health'

    # Assistant commands
    if any(word in text_lower for word in ['профиль', 'настройки', 'персона']):
        return 'assistant_settings'

    # Help and general chat
    if any(word in text_lower for word in ['помощь', 'help', 'что ты умеешь']):
        return 'help'

    # Factual questions (when, who, what, how, why questions)
    if any(word in text_lower for word in ['когда', 'кто', 'что', 'как', 'почему', 'сколько', 'где', 'какой', 'кем', 'чем']):
        return 'factual_question'

    return 'chat'


def extract_title_simple(text: str) -> str:
    """Simple title extraction."""
    # Remove command words and get the main content
    text = re.sub(r'(добавь|создай|задачу|заметку|на завтра|завтра|до послезавтра|послезавтра|сегодня)', '', text, flags=re.IGNORECASE).strip()
    return text[:100]  # Limit title length


def extract_deadline_simple(text: str) -> str | None:
    """Extract deadline from text."""
    text_lower = text.lower()

    if 'завтра' in text_lower:
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.strftime('%Y-%m-%d')
    elif 'послезавтра' in text_lower:
        day_after = datetime.now() + timedelta(days=2)
        return day_after.strftime('%Y-%m-%d')
    elif 'сегодня' in text_lower:
        today = datetime.now()
        return today.strftime('%Y-%m-%d')

    return None


async def handle_finance_transaction(message, user_id: str, text: str):
    """Handle finance transaction parsing and creation."""
    supabase = get_supabase_client()

    try:
        # Simple parsing for amount and description
        import re

        # Find amount (Russian rubles)
        amount_match = re.search(r'(\d+(?:\.\d{1,2})?)', text)
        if not amount_match:
            await message.reply_text("❌ Не удалось определить сумму. Укажите сумму в рублях.")
            return

        amount = float(amount_match.group(1))

        # Determine transaction type
        text_lower = text.lower()
        if any(word in text_lower for word in ['получил', 'заработал', 'доход', 'зарплата', 'премия']):
            transaction_type = 'income'
            default_category = 'Зарплата'
        else:
            transaction_type = 'expense'
            default_category = 'Продукты'

        # Extract description (remove amount and transaction words)
        description = re.sub(r'\d+(?:\.\d{1,2})?', '', text).strip()
        description = re.sub(r'(потратил|купил|заплатил|получил|заработал)', '', description, flags=re.IGNORECASE).strip()

        # Create transaction
        transaction_data = {
            "user_id": user_id,
            "amount": amount,
            "type": transaction_type,
            "description": description or f"{transaction_type.title()} {amount} ₽",
            "merchant": description[:50] if description else None
        }

        response = supabase.table("finance_transactions").insert(transaction_data).execute()

        if response.data:
            emoji = "💰" if transaction_type == 'income' else "💸"
            await message.reply_text(
                f"{emoji} {'Доход' if transaction_type == 'income' else 'Расход'} записан!\n"
                f"{'+' if transaction_type == 'income' else '-'}{amount} ₽ — {description or 'Без описания'}"
            )
        else:
            await message.reply_text("❌ Не удалось сохранить транзакцию.")

    except Exception as e:
        logger.error(f"Finance transaction error: {e}")
        await message.reply_text("❌ Ошибка при обработке финансовой операции.")


async def handle_personal_data(message, user_id: str, text: str):
    """Handle personal data (logins, contacts) creation."""
    supabase = get_supabase_client()

    try:
        text_lower = text.lower()

        if 'логин' in text_lower or 'пароль' in text_lower:
            # Login/password data
            data_type = 'login'

            # Simple parsing - user needs to provide structured data
            await message.reply_text(
                "🔐 Для сохранения логина/пароля используйте формат:\n"
                "«Сохрани логин: user@gmail.com пароль: mypass123»\n\n"
                "Или укажите тип данных через веб-интерфейс для большей безопасности."
            )

        elif 'телефон' in text_lower or 'контакт' in text_lower:
            # Contact data
            data_type = 'contact'

            await message.reply_text(
                "📞 Для сохранения контакта используйте:\n"
                "«Сохрани контакт: Иван Иванов телефон: +7 999 123-45-67»\n\n"
                "Или используйте веб-интерфейс для управления контактами."
            )
        else:
            await message.reply_text(
                "💾 Я могу сохранить:\n"
                "• Логины и пароли (конфиденциально)\n"
                "• Контактные данные\n"
                "• Документы и личную информацию\n\n"
                "Используйте веб-интерфейс для надежного хранения чувствительных данных."
            )

    except Exception as e:
        logger.error(f"Personal data error: {e}")
        await message.reply_text("❌ Ошибка при обработке личных данных.")


async def handle_mood_entry(message, user_id: str, text: str):
    """Handle mood tracking entry."""
    supabase = get_supabase_client()

    try:
        from datetime import date

        # Simple mood parsing
        text_lower = text.lower()
        mood_level = 5  # default neutral

        # Try to determine mood level from keywords
        if any(word in text_lower for word in ['отлично', 'великолепно', 'супер', 'замечательно']):
            mood_level = 9
        elif any(word in text_lower for word in ['хорошо', 'нормально', 'ок']):
            mood_level = 7
        elif any(word in text_lower for word in ['плохо', 'ужасно', 'кошмар']):
            mood_level = 2
        elif any(word in text_lower for word in ['устал', 'грустно', 'расстроен']):
            mood_level = 3

        mood_data = {
            "user_id": user_id,
            "mood_level": mood_level,
            "mood_description": text[:200],  # Store original text as description
            "entry_date": date.today()
        }

        response = supabase.table("mood_entries").insert(mood_data).execute()

        if response.data:
            mood_emojis = ["😢", "😞", "😐", "😕", "😐", "🙂", "😊", "😄", "😍"]
            emoji = mood_emojis[min(mood_level - 1, len(mood_emojis) - 1)]

            await message.reply_text(
                f"{emoji} Настроение записано!\n"
                f"Уровень: {mood_level}/10\n"
                f"Запись сохранена в дневник настроения."
            )
        else:
            await message.reply_text("❌ Не удалось сохранить настроение.")

    except Exception as e:
        logger.error(f"Mood entry error: {e}")
        await message.reply_text("❌ Ошибка при сохранении настроения.")


async def handle_diary_entry(message, user_id: str, text: str):
    """Handle diary entry creation."""
    supabase = get_supabase_client()

    try:
        from datetime import date

        # Determine entry type
        text_lower = text.lower()
        entry_type = 'general'

        if 'благодарность' in text_lower or 'благодарен' in text_lower:
            entry_type = 'gratitude'
        elif 'размышлени' in text_lower or 'думаю' in text_lower:
            entry_type = 'reflection'
        elif 'мечта' in text_lower or 'сон' in text_lower:
            entry_type = 'dream'
        elif 'цель' in text_lower or 'достижени' in text_lower:
            entry_type = 'achievement'

        diary_data = {
            "user_id": user_id,
            "title": f"Запись {date.today().strftime('%d.%m.%Y')}",
            "content": text,
            "entry_type": entry_type,
            "entry_date": date.today()
        }

        response = supabase.table("diary_entries").insert(diary_data).execute()

        if response.data:
            await message.reply_text(
                f"📖 Запись в дневник сохранена!\n"
                f"Тип: {entry_type.title()}\n"
                f"Дата: {date.today().strftime('%d.%m.%Y')}"
            )
        else:
            await message.reply_text("❌ Не удалось сохранить запись в дневник.")

    except Exception as e:
        logger.error(f"Diary entry error: {e}")
        await message.reply_text("❌ Ошибка при сохранении записи в дневник.")


async def handle_finance_summary(message, user_id: str):
    """Show finance summary."""
    supabase = get_supabase_client()

    try:
        from datetime import datetime, timedelta

        # Get current month data
        start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.utcnow()

        response = supabase.table("finance_transactions").select("*").eq("user_id", user_id)\
            .gte("transaction_date", start_date.isoformat())\
            .lte("transaction_date", end_date.isoformat()).execute()

        transactions = response.data or []

        total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
        total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
        balance = total_income - total_expenses

        await message.reply_text(
            f"💰 Финансовый отчет ({start_date.strftime('%B %Y')}):\n\n"
            f"📈 Доходы: +{total_income:.2f} ₽\n"
            f"📉 Расходы: -{total_expenses:.2f} ₽\n"
            f"⚖️ Баланс: {balance:.2f} ₽\n\n"
            f"📊 Всего операций: {len(transactions)}\n\n"
            f"Подробную статистику смотрите в веб-интерфейсе!"
        )

    except Exception as e:
        logger.error(f"Finance summary error: {e}")
        await message.reply_text("❌ Ошибка при получении финансовой статистики.")


async def handle_factual_question(message, text: str, send_message: bool = True):
    """Handle factual questions with knowledge base."""
    try:
        text_lower = text.lower()

        # Knowledge base for common questions
        knowledge_base = {
            # Historical facts
            'сталин': 'Иосиф Виссарионович Сталин родился 18 декабря 1878 года (по старому стилю 6 декабря) в городе Гори, Грузия.',
            'сталина': 'Иосиф Виссарионович Сталин родился 18 декабря 1878 года (по старому стилю 6 декабря) в городе Гори, Грузия.',
            'родился сталин': 'Иосиф Виссарионович Сталин родился 18 декабря 1878 года в городе Гори, Грузия.',
            'когда родился сталин': 'Иосиф Виссарионович Сталин родился 18 декабря 1878 года (по старому стилю 6 декабря) в городе Гори, Грузия.',
            'сталин родился': 'Иосиф Виссарионович Сталин родился 18 декабря 1878 года в городе Гори, Грузия.',

            # Holidays and celebrations
            'день россии': 'День России отмечается 12 июня. Это государственный праздник, посвященный принятию Декларации о государственном суверенитете РСФСР в 1990 году.',
            'когда день россии': 'День России отмечается 12 июня ежегодно.',
            'праздник день россии': 'День России отмечается 12 июня. Это главный государственный праздник Российской Федерации.',

            # Famous people
            'путин': 'Владимир Владимирович Путин - Президент Российской Федерации, родился 7 октября 1952 года.',
            'путину': 'Владимир Владимирович Путин - Президент Российской Федерации, родился 7 октября 1952 года.',
            'сколько лет путину': 'Владимиру Путину 71 год (родился 7 октября 1952 года).',
            'когда родился путин': 'Владимир Путин родился 7 октября 1952 года.',
            'путин родился': 'Владимир Путин родился 7 октября 1952 года в Ленинграде (ныне Санкт-Петербург).',

            # Mathematical facts
            'пи': 'Число π (пи) ≈ 3.14159, это отношение длины окружности к её диаметру.',
            'число пи': 'Число π (пи) ≈ 3.14159, это отношение длины окружности к её диаметру.',

            # Scientific facts
            'скорость света': 'Скорость света в вакууме составляет примерно 299 792 458 метров в секунду.',
            'земля': 'Земля - третья планета от Солнца, её возраст около 4.54 миллиарда лет.',

            # General knowledge
            'москва': 'Москва - столица Российской Федерации, крупнейший город страны с населением около 12 миллионов человек.',
            'россия': 'Россия - крупнейшая страна мира по площади, расположена в Восточной Европе и Северной Азии.',
        }

        # Check for matches in knowledge base
        for key, answer in knowledge_base.items():
            if key in text_lower:
                if send_message:
                    await message.reply_text(f"📚 {answer}")
                logger.info(f"Found knowledge base answer for '{key}': {answer}")
                return

        # Fallback for unrecognized factual questions
        if send_message:
            await message.reply_text(
                "🤔 Это интересный вопрос! К сожалению, я не нашел готового ответа в моей базе знаний.\n\n"
                "Попробуйте перефразировать вопрос или спросите о:\n"
                "• Исторических фактах (Сталин, войны, события)\n"
                "• Математических константах (число π, скорость света)\n"
                "• Географии (страны, города)\n"
                "• Науке (планеты, элементы)\n\n"
                "Или используйте мои основные функции: задачи, заметки, финансы, настроение!"
            )

    except Exception as e:
        logger.error(f"Factual question error: {e}")
        if send_message:
            await message.reply_text("❌ Ошибка при обработке вопроса. Попробуйте позже.")


async def handle_assistant_settings(message, user_id: str):
    """Show assistant settings info."""
    supabase = get_supabase_client()

    try:
        # Get current settings
        response = supabase.table("user_assistant_settings").select("*").eq("user_id", user_id).execute()

        if response.data:
            settings = response.data[0]
            persona_name = "Не выбран"

            if settings.get("current_persona_id"):
                persona_response = supabase.table("assistant_personas").select("display_name").eq("id", settings["current_persona_id"]).execute()
                if persona_response.data:
                    persona_name = persona_response.data[0]["display_name"]

            await message.reply_text(
                f"⚙️ Ваши настройки ассистента:\n\n"
                f"🎭 Характер: {persona_name}\n"
                f"🗣️ Голос: {'Включен' if settings.get('voice_enabled') else 'Отключен'}\n"
                f"🔔 Уведомления: {'Включены' if settings.get('notifications_enabled') else 'Отключены'}\n"
                f"🌍 Язык: {settings.get('language', 'ru').upper()}\n"
                f"🕐 Часовой пояс: {settings.get('timezone', 'Europe/Moscow')}\n\n"
                f"Настройки можно изменить в веб-интерфейсе!"
            )
        else:
            await message.reply_text(
                "⚙️ Настройки ассистента не найдены.\n"
                "Используйте веб-интерфейс для настройки характера и предпочтений!"
            )

    except Exception as e:
        logger.error(f"Assistant settings error: {e}")
        await message.reply_text("❌ Ошибка при получении настроек ассистента.")


async def execute_intent(
    message,
    user_id: str,
    intent: str,
    title: str,
    description: str,
    deadline: str | None = None,
    priority: str = 'medium',
    *,
    raw_text: str | None = None,
    telegram_id: int | None = None,
    context: ContextTypes.DEFAULT_TYPE | None = None,
):
    """Execute the determined intent for MISIX."""
    supabase = get_supabase_client()

    try:
        if intent == 'finance_transaction':
            text_for_processing = raw_text or description
            amount_value, direction_value, category_name = _parse_transaction_details(text_for_processing or "")

            if amount_value is None:
                await message.reply_text("❓ Не слышу сумму. Уточни, сколько именно?")
                return

            if direction_value is None:
                await message.reply_text("💬 Это доход или расход? Напиши 'доход' или 'расход'.")
                return

            human_category = category_name or "Без категории"
            summary_lines = [
                "📋 Проверь, всё ли верно:",
                f"Сумма: {amount_value}",
                f"Тип: {'Доход' if direction_value == 'income' else 'Расход'}",
                f"Категория: {human_category}",
            ]
            await message.reply_text("\n".join(summary_lines))
            await message.reply_text("Если всё верно, напиши 'подтверждаю'. Иначе укажи нужные правки целиком.")

            state = {
                "pending_intent": "finance_transaction",
                "payload": {
                    "user_id": user_id,
                    "amount": amount_value,
                    "type": direction_value,
                    "notes": text_for_processing,
                    "category_name": human_category,
                },
            }
            if context is not None:
                context.chat_data['pending_confirmation'] = state
            else:
                logger.warning("Bot context not available to store confirmation state")

            return

        elif intent == 'create_task':
            await message.chat.send_action(action="typing")

            task_title = title or description or raw_text or ""
            normalized_title = task_title.strip()

            task_deadline = deadline
            if not task_deadline and raw_text:
                task_deadline = await parse_deadline_phrase(raw_text)

            if not normalized_title:
                await message.reply_text("❓ Я не понял название задачи. Напиши, что нужно сделать.")
                return

            if not task_deadline:
                await message.reply_text("📅 На когда поставить задачу? Напиши дату или хотя бы 'завтра', 'послезавтра'.")
                return

            task_data = {
                "user_id": user_id,
                "title": normalized_title,
                "description": description,
                "priority": priority,
                "status": "new",
                "deadline": task_deadline,
            }

            supabase.table("tasks").insert(task_data).execute()

            priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(priority, "🟡")

            await message.reply_text(
                f"✅ Задача создана!\n"
                f"{priority_emoji} «{normalized_title}»\n"
                f"📅 {task_deadline}"
            )

        elif intent == 'create_note':
            # Show typing for database operation
            await message.chat.send_action(action=ChatAction.TYPING)
            
            # Create note
            note_data = {
                "user_id": user_id,
                "title": title,
                "content": description,
                "content_format": "markdown"
            }

            response = supabase.table("notes").insert(note_data).execute()

            await message.reply_text(
                f"📝 Заметка создана!\n"
                f"«{title or 'Без названия'}»"
            )

        elif intent == 'personal_data':
            # Handle personal data (logins, contacts)
            await handle_personal_data(message, user_id, description)

        elif intent == 'create_debt':
            text_for_processing = raw_text or description
            amount = _parse_amount(text_for_processing)
            if amount is None:
                await message.reply_text(
                    "❌ Не понял сумму долга. Напиши, например: 'Долг 2000 рублей Сергею'."
                )
                return

            counterparty = _parse_counterparty(text_for_processing) or "лично"
            direction = _parse_direction(text_for_processing)
            due_date = _parse_due_date(text_for_processing)

            await save_debt_entry(
                user_id,
                counterparty=counterparty,
                amount=amount,
                direction=direction,
                due_date=due_date,
                notes=text_for_processing,
                telegram_id=telegram_id,
            )

            due_part = f" до {due_date}" if due_date else ""
            direction_text = "ты должен" if direction == 'owed_by_me' else "тебе должны"
            await message.reply_text(
                f"📒 Зафиксировал долг {amount:.2f} ₽ — {counterparty} ({direction_text}){due_part}."
            )

        elif intent == 'create_reminder':
            text_for_processing = raw_text or description
            reminder_dt, tz_name = _parse_datetime_with_timezone(text_for_processing)
            if reminder_dt is None:
                await message.reply_text(
                    "❌ Не понял время напоминания. Напиши, например: 'Напомни завтра в 08:00 позвонить маме'."
                )
                return

            timezone_name = tz_name or 'Europe/Moscow'
            title = re.sub(r"(?i)напомни( мне|,| пожалуйста)?", "", text_for_processing).strip()
            if not title:
                title = "Напоминание"

            await save_reminder_entry(
                user_id,
                title=title,
                reminder_time=reminder_dt,
                timezone_name=timezone_name,
                payload_data={"source": "telegram", "raw": text_for_processing},
                telegram_id=telegram_id,
            )

            local_time = reminder_dt
            if local_time.tzinfo is not None:
                local_time = local_time.astimezone(ZoneInfo(timezone_name))
            await message.reply_text(
                f"⏰ Напоминание запланировано на {local_time.strftime('%d.%m %H:%M')} ({timezone_name})."
            )

        elif intent == 'health_entry':
            text_for_processing = raw_text or description
            parsed_metrics = parse_health_metrics(text_for_processing)
            if not parsed_metrics:
                await message.reply_text(
                    "❌ Не понял показатель. Напиши, например: 'Вес 72.4 кг' или 'Пульс 68'."
                )
                return

            previews: list[str] = []
            timestamp = datetime.utcnow().isoformat()
            for metric_data in parsed_metrics:
                await save_health_metric(user_id, metric_data)
                previews.append(_format_health_metric_line({**metric_data, 'recorded_at': timestamp}))

            await message.reply_text(
                "🩺 Записал показател" + ("и" if len(previews) > 1 else "ь") + " здоровья:\n" + "\n".join(previews)
            )

        elif intent == 'list_health':
            metrics = await fetch_recent_health_metrics(user_id, limit=5)
            if not metrics:
                await message.reply_text("🩺 Пока нет сохранённых показателей. Сообщи, например, 'Вес 72 кг'.")
                return

            lines = [_format_health_metric_line(metric) for metric in metrics]
            await message.reply_text(
                "🩺 Последние показатели здоровья:\n" + "\n".join(lines)
            )

        elif intent == 'mood_entry':
            # Show typing for database operation
            await message.chat.bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing"
            )
            
            # Handle mood tracking
            await handle_mood_entry(message, user_id, description)

        elif intent == 'diary_entry':
            # Show typing for database operation
            await message.chat.bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing"
            )
            
            # Handle diary entry
            await handle_diary_entry(message, user_id, description)

        elif intent == 'assistant_settings':
            await handle_assistant_settings(message, user_id)

        elif intent == 'list_tasks':
            # Show typing for database query
            await message.chat.bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing"
            )
            
            # List recent tasks
            response = supabase.table("tasks").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(5).execute()

            if not response.data:
                await message.reply_text("📋 У вас пока нет задач.")
                return

            tasks_text = "📋 Ваши последние задачи:\n\n"
            for task in response.data:
                status_emoji = {
                    "new": "🔵",
                    "in_progress": "🟡",
                    "waiting": "🟠",
                    "completed": "🟢",
                    "cancelled": "❌"
                }.get(task.get('status', 'new'), "🔵")

                priority_emoji = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🟠",
                    "critical": "🔴"
                }.get(task.get('priority', 'medium'), "🟡")

                tasks_text += f"{status_emoji}{priority_emoji} {task['title']}\n"

            await message.reply_text(tasks_text)

        elif intent == 'list_notes':
            # Show typing for database query
            await message.chat.bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing"
            )
            
            # List recent notes
            response = supabase.table("notes").select("*").eq("user_id", user_id).eq("is_archived", False).order("created_at", desc=True).limit(5).execute()

            if not response.data:
                await message.reply_text("📝 У вас пока нет заметок.")
                return

            notes_text = "📝 Ваши последние заметки:\n\n"
            for note in response.data:
                title = note.get('title') or 'Без названия'
                notes_text += f"📄 {title}\n"

            await message.reply_text(notes_text)

        elif intent == 'list_finances':
            # Show typing for database query
            await message.chat.bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing"
            )
            
            # Show finance summary
            await handle_finance_summary(message, user_id)

        elif intent == 'factual_question':
            # Handle factual questions with knowledge base (don't send message if AI already responded)
            await handle_factual_question(message, description, send_message=False)

        elif intent == 'help':
            # Show help
            await message.reply_text(HELP_MESSAGE)

        else:
            # Default to AI chat
            await chat_with_ai(message, user_id, description, telegram_id=telegram_id)

    except Exception as e:
        logger.error(f"Failed to execute intent {intent}: {e}")
        await message.reply_text("❌ Произошла ошибка при выполнении действия.")


async def chat_with_ai(message, user_id: str, user_text: str, telegram_id: int | None = None) -> None:
    """Regular AI chat when no specific intent is detected."""
    try:
        # Log user message
        if supabase_available():
            try:
                supabase = get_supabase_client()
                payload = {
                    "user_id": user_id,
                    "role": "user",
                    "content": user_text
                }
                if telegram_id is not None:
                    payload["telegram_id"] = telegram_id
                await supabase.table("assistant_messages").insert(payload).execute()
            except Exception as log_error:
                logger.warning("Failed to log user message in assistant_messages: %s", log_error)

        # Try to get AI response with fallback
        response = await get_ai_response(user_text, user_id=user_id)

        # Log assistant response
        if supabase_available():
            try:
                payload = {
                    "user_id": user_id,
                    "role": "assistant",
                    "content": response
                }
                if telegram_id is not None:
                    payload["telegram_id"] = telegram_id
                await supabase.table("assistant_messages").insert(payload).execute()
            except Exception as log_error:
                logger.warning("Failed to log assistant response in assistant_messages: %s", log_error)

        await message.reply_text(response)

    except Exception as e:
        logger.error(f"AI chat failed: {e}", exc_info=True)
        # Fallback response
        fallback_response = get_fallback_response(user_text)
        await message.reply_text(fallback_response)


async def get_ai_response(
    user_text: str,
    conversation_history: list[dict] = None,
    *,
    user_id: str | None = None,
) -> str:
    """Get AI response for any user message with conversation history."""
    try:
        # Primary: Yandex GPT for general conversation
        client = get_yandex_gpt_client()

        # Build conversation context
        messages = []

        persona_prompt: str | None = None
        persona_name: str | None = None
        if user_id:
            persona_prompt, persona_name = await get_user_persona_context(user_id)

        system_parts = [DEFAULT_SYSTEM_PROMPT]

        if persona_prompt:
            system_parts.append(persona_prompt)
        elif persona_name:
            system_parts.append(f"Поддерживай стиль: {persona_name}.")

        messages.append({"role": "system", "text": "\n\n".join(system_parts)})

        # Add conversation history (limit to last 10 messages to avoid token limits)
        if conversation_history:
            # Take last 10 messages to keep context manageable
            recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
            messages.extend(recent_history)
            logger.info(f"Using {len(recent_history)} messages from conversation history")

        # Add current user message
        messages.append({"role": "user", "text": user_text})
        
        response = await client.chat(messages)
        return response

    except YandexGPTConfigurationError as e:
        logger.warning(f"Yandex GPT configuration error: {e}")
        raise

    except Exception as e:
        logger.error(f"Yandex GPT failed: {e}")
        raise


def get_fallback_response(user_text: str) -> str:
    """Generate fallback response when AI is unavailable."""
    text_lower = user_text.lower()

    # Greeting responses
    if any(word in text_lower for word in ['привет', 'здравствуй', 'hello', 'hi']):
        return "👋 Привет! Я ваш персональный ассистент MISIX. Чем могу помочь?"

    # Help responses
    if any(word in text_lower for word in ['помощь', 'help', 'что ты умеешь']):
        return "🤖 Я могу:\n• Создавать задачи и заметки\n• Отслеживать финансы\n• Вести дневник настроения\n• Хранить личные данные\n\nНапишите 'Добавь задачу купить продукты' или используйте голосовые сообщения!"

    # Task-related
    if any(word in text_lower for word in ['задач', 'task']):
        return 'list_tasks'
    if any(word in text_lower for word in ['напомни', 'reminder']):
        return 'reminder'
    if any(word in text_lower for word in ['долг', 'debt']):
        return 'debt'

    # Note-related
    if any(word in text_lower for word in ['заметк', 'note']):
        return "📝 Для создания заметки напишите: 'Создай заметку о [тема]'\n\nНапример: 'Создай заметку о встрече с командой'"

    # Finance-related
    if any(word in text_lower for word in ['деньг', 'финанс', 'расход', 'доход']):
        return "💰 Для учета финансов напишите: 'Потратил [сумма] на [что]'\n\nНапример: 'Потратил 500 рублей на обед'"

    # Mood-related
    if any(word in text_lower for word in ['настроени', 'mood', 'эмоц']):
        return "😊 Для записи настроения напишите: 'Настроение [описание]'\n\nНапример: 'Настроение отличное, выучил 20 слов'"

    # Default response
    return "🤖 Извините, AI временно недоступен. Попробуйте позже.\n\nЯ могу работать с:\n• Задачами: 'Добавь задачу купить хлеб'\n• Заметками: 'Создай заметку о встрече'\n• Финансами: 'Потратил 100 рублей на еду'\n• Настроением: 'Настроение хорошее'"


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle voice messages - convert to text and process as regular message."""
    message = update.message
    user = update.effective_user

    logger.info("🎤 ===== VOICE MESSAGE RECEIVED =====")
    logger.info(f"   User: {user.id} ({user.username})")
    logger.info(f"   Chat: {update.effective_chat.id}")
    logger.info(f"   Message ID: {message.message_id}")

    if not message or not user or not message.voice:
        logger.warning("❌ Invalid voice message received - missing required fields")
        return

    logger.info(f"🎤 Voice file info: duration={message.voice.duration}s, size={message.voice.file_size} bytes")
    logger.info(f"   Mime type: {message.voice.mime_type}")
    logger.info(f"   File ID: {message.voice.file_id}")

    try:
        # Show that we're processing voice
        logger.info("📤 Sending processing message to user...")
        processing_msg = await message.reply_text("🎤 Распознаю голосовое сообщение...")
        logger.info("✅ Processing message sent")

        # Show typing indicator while processing
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        # Download voice file
        logger.info("📥 Starting voice file download...")
        voice_file = await message.voice.get_file()
        logger.info(f"✅ Voice file object obtained: {voice_file.file_id}")
        logger.info(f"   File size: {voice_file.file_size} bytes")

        # Use Yandex SpeechKit for transcription
        logger.info("🎯 Starting transcription with Yandex SpeechKit...")
        speech_kit = get_yandex_speech_kit()
        transcribed_text = await speech_kit.transcribe_telegram_voice(voice_file)

        if transcribed_text and transcribed_text.strip():
            logger.info(f"✅ Transcription successful: '{transcribed_text}'")
            await message.reply_text(f"🎙️ Распознано: «{transcribed_text}»")

            # Process the transcribed text using dedicated function
            await process_transcribed_text(update, context, transcribed_text)
        else:
            logger.warning("❌ Transcription failed - no result")
            await message.reply_text(
                "❌ Не удалось распознать голосовое сообщение.\n\n"
                "Возможные причины:\n"
                "• Слишком тихая запись\n"
                "• Шумы в фоне\n"
                "• Короткое сообщение\n\n"
                "Попробуйте записать сообщение четче или напишите текстом! 📝"
            )

        # Delete processing message
        try:
            await processing_msg.delete()
            logger.info("🗑️ Processing message deleted")
        except Exception as delete_error:
            logger.warning(f"Could not delete processing message: {delete_error}")

    except Exception as e:
        logger.error(f"❌ Voice processing error: {e}", exc_info=True)
        try:
            await message.reply_text("❌ Ошибка обработки голосового сообщения. Попробуйте написать текстом.")
        except Exception as send_error:
            logger.error(f"Could not send error message to user: {send_error}")


async def simulate_voice_transcription(voice_file) -> str:
    """Simulate voice-to-text conversion. In production, integrate with Yandex SpeechKit."""
    # For now, return a mock transcription
    # In real implementation, this would:
    # 1. Download the voice file
    # 2. Send to Yandex SpeechKit API
    # 3. Get transcription back

    import asyncio
    await asyncio.sleep(1)  # Simulate processing time

    # Mock responses for testing
    return "Привет, добавь задачу купить продукты на завтра"


def register_handlers(application: Application) -> None:
    """Register all bot handlers."""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_persona", set_persona_command))
    application.add_handler(CallbackQueryHandler(handle_persona_callback))

    # Handle text messages with natural language processing
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Handle voice messages
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))


async def handle_persona_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle persona selection via inline keyboard."""
    query = update.callback_query
    if not query or not query.data or not query.data.startswith(PERSONA_CALLBACK_PREFIX):
        return

    await query.answer()

    persona_id = query.data[len(PERSONA_CALLBACK_PREFIX):]
    user = query.from_user

    if not user:
        return

    if not supabase_available():
        await query.edit_message_text("❌ Персонализация сейчас недоступна. Попробуй позже.")
        return

    try:
        user_id = await get_or_create_user(user.id, user.username, user.full_name)
    except Exception as exc:
        logger.error("Failed to register user for persona callback: %s", exc)
        await query.edit_message_text("❌ Не удалось сохранить выбор. Попробуй ещё раз позже.")
        return

    await ensure_user_assistant_settings(user_id)

    persona = await get_persona_by_id(persona_id)
    if not persona:
        await query.edit_message_text("❌ Такой характер не найден. Выбери другой вариант.")
        return

    updated = await set_user_persona(user_id, persona_id)
    if not updated:
        await query.edit_message_text("❌ Не удалось сохранить выбор. Попробуй позже.")
        return

    confirmation = (
        f"🎭 Готово! Теперь я «{persona.get('display_name', 'MISIX')}»\n\n"
        f"{persona.get('description', 'Всегда можно сменить стиль командой /set_persona.') }"
    )

    try:
        await query.edit_message_text(confirmation)
    except Exception as edit_error:  # noqa: BLE001
        logger.info("Could not edit persona selection message: %s", edit_error)
        await query.message.reply_text(confirmation)
