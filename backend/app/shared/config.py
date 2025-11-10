from pathlib import Path
from dotenv import load_dotenv
import logging
import os
import yaml

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env.local")

config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
config = {}

logger = logging.getLogger(__name__)

logger.info(f"Loading configuration from: {config_path}")
try:
    if config_path.exists() and config_path.stat().st_size > 0:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        logger.info(f"Successfully loaded configuration")
    else:
        logger.warning(f"Configuration file not found or empty")
        config = {
            "telegram": {
                "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN"),
                "webhook_url": os.environ.get("TELEGRAM_WEBHOOK_URL")
            },
            "yandex": {
                "gpt_api_key": os.environ.get("YANDEX_GPT_API_KEY", "test_key"),
                "folder_id": os.environ.get("YANDEX_FOLDER_ID", "test_folder"),
                "gpt_base_url": "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                "gpt_model": "small",
                "gpt_temperature": 0.7,
                "gpt_top_p": 0.9,
                "gpt_top_k": 40,
                "gpt_frequency_penalty": 0.0,
                "gpt_presence_penalty": 0.0,
                "gpt_min_length": 1,
                "gpt_max_length": 2048
            },
            "jwt": {
                "secret_key": os.environ.get("JWT_SECRET_KEY"),
                "algorithm": os.environ.get("JWT_ALGORITHM")
            },
            "backend": {
                "base_url": os.environ.get("BACKEND_BASE_URL")
            },
            "frontend": {
                "allowed_origins": os.environ.get("FRONTEND_ALLOWED_ORIGINS")
            },
            "supabase": {
                "url": os.environ.get("SUPABASE_URL"),
                "anon_key": os.environ.get("SUPABASE_ANON_KEY"),
                "service_key": os.environ.get("SUPABASE_SERVICE_KEY")
            },
            "security": {
                "encryption_key": os.environ.get("MISIX_ENCRYPTION_KEY")
            }
        }
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    config = {}

class Settings:
    """Application configuration loaded from YAML file or environment variables."""

    def __init__(self):
        self.telegram_bot_token = self._safe_get("telegram", "bot_token")
        self.telegram_webhook_url = self._safe_get("telegram", "webhook_url")
        self.yandex_gpt_api_key = self._safe_get("yandex", "gpt_api_key")
        self.yandex_folder_id = self._safe_get("yandex", "folder_id")
        self.yandex_gpt_base_url = self._safe_get("yandex", "gpt_base_url")
        self.yandex_gpt_model = self._safe_get("yandex", "gpt_model")
        self.yandex_gpt_temperature = self._safe_get("yandex", "gpt_temperature")
        self.yandex_gpt_top_p = self._safe_get("yandex", "gpt_top_p")
        self.yandex_gpt_top_k = self._safe_get("yandex", "gpt_top_k")
        self.yandex_gpt_frequency_penalty = self._safe_get("yandex", "gpt_frequency_penalty")
        self.yandex_gpt_presence_penalty = self._safe_get("yandex", "gpt_presence_penalty")
        self.yandex_gpt_min_length = self._safe_get("yandex", "gpt_min_length")
        self.yandex_gpt_max_length = self._safe_get("yandex", "gpt_max_length")
        self.jwt_secret_key = self._safe_get("jwt", "secret_key")
        self.jwt_algorithm = self._safe_get("jwt", "algorithm")
        self.backend_base_url = self._safe_get("backend", "base_url")
        self.supabase_url = self._safe_get("supabase", "url")
        self.supabase_anon_key = self._safe_get("supabase", "anon_key")
        self.supabase_service_key = self._safe_get("supabase", "service_key")
        self.encryption_key = self._safe_get("security", "encryption_key")
        self.frontend_allowed_origins = self._get_frontend_allowed_origins()

    def _safe_get(self, section, key):
        try:
            return config.get(section, {}).get(key)
        except Exception as e:
            logger.error(f"Error getting config {section}.{key}: {e}")
            return None

    def _get_frontend_allowed_origins(self):
        value = self._safe_get("frontend", "allowed_origins")
        if not value:
            value = os.environ.get("FRONTEND_ALLOWED_ORIGINS")

        if not value:
            return []

        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",")]
            return [part for part in parts if part]

        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]

        logger.warning("Unsupported FRONTEND_ALLOWED_ORIGINS type: %s", type(value))
        return []

settings = Settings()
