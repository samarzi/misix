"""Yandex SpeechKit gRPC client for v3 API."""

import grpc
import logging
from typing import Optional, AsyncGenerator
import os
from datetime import datetime, timedelta

# Импортируем сгенерированные protobuf классы (если они будут созданы)
try:
    from yandex.cloud.ai.stt.v3 import stt_service_pb2, stt_service_pb2_grpc
except ImportError:
    # Fallback для случаев, когда protobuf не сгенерирован
    stt_service_pb2 = None
    stt_service_pb2_grpc = None
    logging.warning("Protobuf classes not available, using fallback implementation")

logger = logging.getLogger(__name__)

class YandexSpeechKitGRPC:
    """Yandex SpeechKit gRPC client for v3 API."""

    def __init__(self):
        self.api_key = os.getenv('YANDEX_SPEECHKIT_API_KEY') or os.getenv('YANDEX_GPT_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.endpoint = "stt.api.cloud.yandex.net:443"

        # Cache for IAM token
        self._iam_token = None
        self._token_expires = None

    async def _get_iam_token(self) -> Optional[str]:
        """Get IAM token using API key."""
        try:
            # Check if we have a valid cached token
            if self._iam_token and self._token_expires and datetime.now() < self._token_expires:
                return self._iam_token

            if not self.api_key:
                logger.error("No API key available for IAM token")
                return None

            # Request new IAM token via REST (пока что используем REST для IAM)
            import aiohttp
            iam_url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
            payload = {"yandexPassportOauthToken": self.api_key}
            headers = {"Content-Type": "application/json"}

            logger.info("Requesting new IAM token from Yandex")

            async with aiohttp.ClientSession() as session:
                async with session.post(iam_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._iam_token = data.get("iamToken")
                        # Token expires in 12 hours, but we'll refresh after 10 hours
                        self._token_expires = datetime.now() + timedelta(hours=10)

                        logger.info("Successfully obtained IAM token")
                        return self._iam_token
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get IAM token: {response.status} - {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Error getting IAM token: {e}")
            return None

    async def transcribe_audio_grpc(self, audio_data: bytes, language: str = "ru-RU") -> Optional[str]:
        """
        Transcribe audio using gRPC v3 API.

        Args:
            audio_data: Raw audio bytes
            language: Language code (default: ru-RU)

        Returns:
            Transcribed text or None if failed
        """
        try:
            if not self.api_key or not self.folder_id:
                logger.warning("Yandex SpeechKit: API key or folder ID not configured")
                return None

            if not audio_data:
                logger.warning("Empty audio data provided")
                return None

            # Get IAM token
            iam_token = await self._get_iam_token()
            if not iam_token:
                logger.error("Failed to get IAM token for gRPC")
                return None

            # Create gRPC channel
            credentials = grpc.ssl_channel_credentials()
            channel = grpc.secure_channel(self.endpoint, credentials)

            # Create stub
            if stt_service_pb2_grpc:
                stub = stt_service_pb2_grpc.RecognizerStub(channel)

                # Prepare recognition request
                # Note: This is a simplified implementation
                # In real implementation, you would need proper protobuf messages

                logger.info("gRPC SpeechKit v3 transcription not fully implemented yet")
                logger.info("Falling back to REST API v1")

                # For now, fall back to REST implementation
                from .yandex_speech import get_yandex_speech_kit
                rest_client = get_yandex_speech_kit()
                return await rest_client.transcribe_audio(audio_data, language)
            else:
                logger.warning("gRPC protobuf classes not available, using REST fallback")
                from .yandex_speech import get_yandex_speech_kit
                rest_client = get_yandex_speech_kit()
                return await rest_client.transcribe_audio(audio_data, language)

        except Exception as e:
            logger.error(f"gRPC SpeechKit error: {e}", exc_info=True)
            return None

        finally:
            if 'channel' in locals():
                channel.close()

# Global instance
_grpc_instance = None

def get_yandex_speech_kit_grpc() -> YandexSpeechKitGRPC:
    """Get global Yandex SpeechKit gRPC instance."""
    global _grpc_instance
    if _grpc_instance is None:
        _grpc_instance = YandexSpeechKitGRPC()
    return _grpc_instance
