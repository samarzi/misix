from fastapi import APIRouter, Body, HTTPException
from telegram import Update
import logging

from app.services.telegram import get_telegram_application

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def telegram_webhook(payload: dict = Body(...)) -> dict[str, str]:
    logger.info(f"Received Telegram update: {payload}")
    application = get_telegram_application()

    if application.bot is None:
        raise HTTPException(status_code=503, detail="Telegram bot not initialized")

    update = Update.de_json(payload, application.bot)
    await application.process_update(update)
    return {"status": "processed"}
