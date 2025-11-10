"""Yandex GPT client wrapper with retry logic."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import certifi
import httpx
import ssl
from tenacity import AsyncRetrying, RetryError, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.shared.config import settings
import logging

logger = logging.getLogger(__name__)


class YandexGPTConfigurationError(RuntimeError):
    """Raised when required Yandex GPT configuration is missing."""


class YandexGPTClient:
    def __init__(self, api_key: str, base_url: str, folder_id: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.folder_id = folder_id

    async def chat(
        self,
        messages: Iterable[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 512,
        model: str = "yandexgpt-lite",
    ) -> str:
        """Send chat messages to Yandex GPT and return the model response."""

        payload = {
            "modelUri": f"gpt://{self.folder_id}/{model}",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": max_tokens,
            },
            "messages": list(messages),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(httpx.HTTPError) | retry_if_exception_type(RuntimeError),
            reraise=True,
        ):
            with attempt:
                response = None
                try:
                    ssl_context = ssl.create_default_context(cafile=certifi.where())
                    async with httpx.AsyncClient(timeout=30, verify=ssl_context) as client:
                        logger.debug(f"Sending request to Yandex GPT: URL={self.base_url}, Headers={headers}")
                        response = await client.post(self.base_url, json=payload, headers=headers)
                        logger.debug(f"Received response: Status={response.status_code}, Body={response.text}")
                        response.raise_for_status()
                        data = response.json()
                except Exception as e:
                    logger.error(f"HTTP request failed: {e}")
                    logger.error(f"Request payload: {payload}")
                    logger.error(f"Request headers: {headers}")
                    if response:
                        logger.error(f"Response status code: {response.status_code}")
                        logger.error(f"Response text: {response.text}")
                    if attempt.retry_state.attempt_number >= 3:
                        raise
                    else:
                        raise e

        result = data.get("result", {})
        alternatives = result.get("alternatives", [])
        if not alternatives:
            logger.error(f"Yandex GPT response missing alternatives: {data}")
            raise RuntimeError("Yandex GPT response missing alternatives")

        message = alternatives[0].get("message", {})
        text = message.get("text")
        if not text:
            logger.error(f"Yandex GPT response missing text: {message}")
            raise RuntimeError("Yandex GPT response missing text")

        return text


@lru_cache(maxsize=1)
def get_yandex_gpt_client() -> YandexGPTClient:
    api_key = settings.yandex_gpt_api_key
    folder_id = settings.yandex_folder_id
    base_url = settings.yandex_gpt_base_url

    logger.debug(f"Yandex GPT settings: api_key={api_key}, folder_id={folder_id}")

    if not api_key:
        raise YandexGPTConfigurationError("YANDEX_GPT_API_KEY is not configured")
    if not folder_id:
        raise YandexGPTConfigurationError("YANDEX_FOLDER_ID is not configured")

    return YandexGPTClient(api_key=api_key, base_url=base_url, folder_id=folder_id)
