"""Yandex SpeechKit integration for voice-to-text conversion."""

import aiohttp
import logging
from typing import Optional
import os
import json
from datetime import datetime, timedelta
import io
import wave
import struct

logger = logging.getLogger(__name__)

class YandexSpeechKit:
    """Yandex SpeechKit client for speech recognition."""

    def __init__(self):
        # Use SpeechKit-specific key if available, otherwise fallback to GPT key
        self.api_key = os.getenv('YANDEX_SPEECHKIT_API_KEY') or os.getenv('YANDEX_GPT_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        # Updated endpoint for Yandex SpeechKit
        self.stt_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        self.iam_url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"

        # Cache for IAM token
        self._iam_token = None
        self._token_expires = None

    def convert_ogg_to_wav(self, ogg_data: bytes) -> Optional[bytes]:
        """
        Convert OGG audio data to WAV format using pydub.
        """
        try:
            logger.info("Converting OGG to WAV using pydub")

            # Try to use pydub for proper conversion
            try:
                from pydub import AudioSegment

                # Load OGG data into AudioSegment and ensure mono 16kHz PCM
                ogg_io = io.BytesIO(ogg_data)
                audio = AudioSegment.from_ogg(ogg_io)
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

                wav_io = io.BytesIO()
                audio.export(wav_io, format='wav')
                wav_data = wav_io.getvalue()

                logger.info(f"Successfully converted OGG to WAV: {len(wav_data)} bytes")
                return wav_data

            except ImportError:
                logger.warning("pydub not available; skipping OGG -> WAV conversion")
                return None
            except Exception as e:
                logger.warning(f"pydub conversion failed: {e}")
                return None

        except Exception as e:
            logger.warning(f"OGG to WAV conversion failed: {e}")
            return None
    
    def _simple_ogg_to_wav_conversion(self, ogg_data: bytes) -> Optional[bytes]:
        """
        Simple fallback OGG to WAV conversion.
        This is a basic implementation and may not work for all OGG files.
        """
        try:
            # Basic WAV header for 16-bit mono PCM at 16kHz (common for speech)
            wav_header = struct.pack('<4sL4s4sLHHLLHH4sL',
                b'RIFF',  # ChunkID
                len(ogg_data) + 36,  # ChunkSize
                b'WAVE',  # Format
                b'fmt ',  # Subchunk1ID
                16,  # Subchunk1Size
                1,  # AudioFormat (PCM)
                1,  # NumChannels (mono)
                16000,  # SampleRate
                32000,  # ByteRate
                2,  # BlockAlign
                16,  # BitsPerSample
                b'data',  # Subchunk2ID
                len(ogg_data)  # Subchunk2Size
            )
            
            wav_data = wav_header + ogg_data
            logger.info(f"Fallback WAV conversion: {len(wav_data)} bytes")
            return wav_data
            
        except Exception as e:
            logger.warning(f"Fallback WAV conversion failed: {e}")
            return None

    def convert_ogg_to_lpcm(self, ogg_data: bytes) -> Optional[bytes]:
        """
        Convert OGG audio data to LPCM format.
        This extracts raw PCM data from OGG (simplified conversion).
        """
        try:
            logger.info("Attempting to convert OGG to LPCM format")

            try:
                from pydub import AudioSegment

                ogg_io = io.BytesIO(ogg_data)
                audio = AudioSegment.from_ogg(ogg_io)
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                raw_audio = audio.raw_data

                logger.info(f"Extracted LPCM audio: {len(raw_audio)} bytes")
                return raw_audio

            except ImportError:
                logger.warning("pydub not available; skipping OGG -> LPCM conversion")
                return None
            except Exception as e:
                logger.warning(f"pydub LPCM conversion failed: {e}")
                return None

        except Exception as e:
            logger.warning(f"OGG to LPCM conversion failed: {e}")
            return None

    async def _get_iam_token(self) -> Optional[str]:
        """Get IAM token using API key."""
        try:
            # Check if we have a valid cached token
            if self._iam_token and self._token_expires and datetime.now() < self._token_expires:
                return self._iam_token

            if not self.api_key:
                logger.error("No API key available for IAM token")
                return None

            # Request new IAM token
            payload = {"yandexPassportOauthToken": self.api_key}
            headers = {"Content-Type": "application/json"}

            logger.info("Requesting new IAM token from Yandex")

            connector = aiohttp.TCPConnector(verify_ssl=False)  # Disable SSL verification
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(self.iam_url, json=payload, headers=headers) as response:
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

    async def transcribe_audio(self, audio_data: bytes, language: str = "ru-RU") -> Optional[str]:
        """
        Transcribe audio data to text using Yandex SpeechKit.
        Tries gRPC v3 API first, then falls back to REST v1 API.

        Args:
            audio_data: Raw audio bytes (OGG format from Telegram)
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

            # Try gRPC v3 API first
            logger.info("Trying SpeechKit gRPC v3 API...")
            try:
                from .yandex_speech_grpc import get_yandex_speech_kit_grpc
                grpc_client = get_yandex_speech_kit_grpc()
                grpc_result = await grpc_client.transcribe_audio_grpc(audio_data, language)
                if grpc_result and grpc_result.strip():
                    logger.info(f"gRPC v3 transcription successful: '{grpc_result}'")
                    return grpc_result.strip()
                else:
                    logger.info("gRPC v3 returned empty result, trying REST v1")
            except Exception as grpc_error:
                logger.warning(f"gRPC v3 failed: {grpc_error}, falling back to REST v1")

            # Fallback to REST v1 API
            logger.info("Using SpeechKit REST v1 API as fallback")
            return await self._transcribe_audio_rest_v1(audio_data, language)

        except Exception as e:
            logger.error(f"SpeechKit transcription failed: {e}", exc_info=True)
            return None

    async def _transcribe_audio_rest_v1(self, audio_data: bytes, language: str = "ru-RU") -> Optional[str]:
        """
        Transcribe audio using REST v1 API (fallback implementation).
        """
        # Try to convert OGG to different formats
        lpcm_audio = self.convert_ogg_to_lpcm(audio_data)
        wav_audio = self.convert_ogg_to_wav(audio_data)

        # Try different audio format options in order of preference
        format_options = []
        if lpcm_audio:
            format_options.append(("lpcm", "audio/lpcm", lpcm_audio))
        if wav_audio:
            format_options.append(("wav", "audio/wav", wav_audio))
        format_options.append(("oggopus", "audio/ogg", audio_data))

        # Try different authentication methods
        auth_methods = [
            ("API Key", f"Api-Key {self.api_key}"),
            ("Bearer API Key", f"Bearer {self.api_key}"),
        ]

        for auth_name, auth_header in auth_methods:
            for format_name, content_type_format, audio_payload in format_options:
                if not audio_payload:
                    continue
                    
                logger.info(f"Trying SpeechKit REST v1 with {auth_name} + {format_name} format")
                
                params = {
                    "folderId": self.folder_id,
                    "lang": language,
                    "format": format_name
                }
                headers = {
                    "Authorization": auth_header,
                    "Content-Type": content_type_format
                }

                logger.info(f"Sending {format_name} audio ({len(audio_payload)} bytes)")

                timeout = aiohttp.ClientTimeout(total=30, connect=10)
                connector = aiohttp.TCPConnector(verify_ssl=False)  # Disable SSL verification
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.post(self.stt_url, headers=headers, params=params, data=audio_payload) as response:
                        logger.info(f"SpeechKit {auth_name} {format_name} response: {response.status}")

                        if response.status == 200:
                            try:
                                result_json = await response.json()
                                logger.debug(f"SpeechKit response: {result_json}")

                                if "result" in result_json and result_json["result"].strip():
                                    transcript = result_json["result"].strip()
                                    logger.info(f" SpeechKit success: '{transcript}'")
                                    return transcript
                                else:
                                    logger.warning(f"Empty result from {format_name}")
                                    continue

                            except Exception as e:
                                logger.error(f"Failed to parse {format_name} response: {e}")
                                continue

                        elif response.status in [400, 415]:
                            logger.warning(f"Format {format_name} not supported (status {response.status})")
                            continue
                            
                        elif response.status in [401, 403]:
                            logger.warning(f"{auth_name} auth failed (status {response.status})")
                            break  # Try next auth method

                        else:
                            error_text = await response.text()
                            logger.warning(f"SpeechKit error {response.status}: {error_text[:100]}...")
                            continue  # Try next auth method

        # If all auth methods failed, try IAM token as last resort
        logger.info("All direct auth methods failed, trying IAM token...")
        iam_token = await self._get_iam_token()
        if iam_token:
            # Try IAM with different formats
            for format_name, content_type_format, audio_payload in format_options:
                if not audio_payload:
                    continue
                    
                headers = {
                    "Authorization": f"Bearer {iam_token}",
                    "Content-Type": content_type_format
                }
                params = {
                    "folderId": self.folder_id,
                    "lang": language,
                    "format": format_name
                }

                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.post(self.stt_url, headers=headers, params=params, data=audio_payload) as response:
                        logger.info(f"SpeechKit IAM {format_name} response status: {response.status}")

                        if response.status == 200:
                            try:
                                result_json = await response.json()
                                if "result" in result_json:
                                    transcript = result_json["result"].strip()
                                    if transcript:
                                        logger.info(f"SpeechKit IAM {format_name} transcription successful: '{transcript}'")
                                        return transcript
                            except Exception as e:
                                logger.error(f"Failed to parse IAM {format_name} SpeechKit response: {e}")

                        elif response.status not in [400, 415]:  # Don't log format errors for IAM
                            error_text = await response.text()
                            logger.warning(f"SpeechKit IAM {format_name} error {response.status}: {error_text}")
                            break  # If IAM auth fails, don't try other formats

        logger.error("All authentication methods failed for SpeechKit REST v1")
        return None

    async def transcribe_telegram_voice(self, voice_file) -> Optional[str]:
        """
        Transcribe Telegram voice message.

        Args:
            voice_file: Telegram Voice file object

        Returns:
            Transcribed text or None if failed
        """
        try:
            logger.info(f"Starting transcription for voice file: {voice_file.file_id}")

            # Download voice file from Telegram with timeout
            try:
                logger.info("Downloading voice file from Telegram...")
                audio_bytearray = await voice_file.download_as_bytearray()
                audio_data = bytes(audio_bytearray)  # Convert bytearray to bytes
                logger.info(f"Downloaded and converted audio data: {len(audio_data)} bytes")
            except Exception as e:
                logger.error(f"Failed to download voice file: {e}")
                return None

            if not audio_data or len(audio_data) == 0:
                logger.error("Downloaded empty audio data")
                return None

            logger.info(f"Audio data size: {len(audio_data)} bytes")

            # Try SpeechKit first
            logger.info("Attempting SpeechKit transcription...")
            result = await self.transcribe_audio(audio_data)

            if result and result.strip():
                logger.info(f"SpeechKit transcription successful: '{result}'")
                return result.strip()
            else:
                logger.warning("SpeechKit transcription failed or empty")
                return None  # Don't use fallback mock responses

        except Exception as e:
            logger.error(f"Telegram voice transcription failed: {e}", exc_info=True)
            return None  # Don't use fallback mock responses

# Global instance
_speech_kit_instance = None

def get_yandex_speech_kit() -> YandexSpeechKit:
    """Get global Yandex SpeechKit instance."""
    global _speech_kit_instance
    if _speech_kit_instance is None:
        _speech_kit_instance = YandexSpeechKit()
    return _speech_kit_instance
