"""Secure application configuration with validation."""

from typing import Optional
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with strict validation.
    
    All sensitive configuration must be provided via environment variables.
    No default values are provided for secrets to prevent accidental exposure.
    """
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ============================================================================
    # Required Settings (No Defaults - Will Fail if Missing)
    # ============================================================================
    
    # Supabase Configuration
    supabase_url: str = Field(
        ...,
        description="Supabase project URL",
        min_length=1,
    )
    supabase_service_key: str = Field(
        ...,
        description="Supabase service role key (admin access)",
        min_length=1,
    )
    supabase_anon_key: str = Field(
        ...,
        description="Supabase anonymous key (public access)",
        min_length=1,
    )
    
    # JWT Configuration
    jwt_secret_key: str = Field(
        ...,
        description="Secret key for JWT token signing",
        min_length=32,
    )
    
    # Yandex API Configuration
    yandex_gpt_api_key: str = Field(
        ...,
        description="Yandex GPT API key",
        min_length=1,
    )
    yandex_folder_id: str = Field(
        ...,
        description="Yandex Cloud folder ID",
        min_length=1,
    )
    
    # ============================================================================
    # Optional Settings (Safe Defaults Provided)
    # ============================================================================
    
    # Application Settings
    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    
    # JWT Settings
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    jwt_access_token_expire_minutes: int = Field(
        default=15,
        description="Access token expiration time in minutes",
        gt=0,
        le=60,
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days",
        gt=0,
        le=30,
    )
    
    # Yandex GPT Settings
    yandex_gpt_base_url: str = Field(
        default="https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        description="Yandex GPT API base URL",
    )
    yandex_gpt_model: str = Field(
        default="yandexgpt-lite",
        description="Yandex GPT model to use",
    )
    yandex_gpt_temperature: float = Field(
        default=0.7,
        description="GPT temperature parameter",
        ge=0.0,
        le=1.0,
    )
    yandex_gpt_max_tokens: int = Field(
        default=2048,
        description="Maximum tokens in GPT response",
        gt=0,
        le=8000,
    )
    
    # Telegram Bot Settings
    telegram_bot_token: Optional[str] = Field(
        default=None,
        description="Telegram bot token (optional)",
    )
    telegram_webhook_url: Optional[str] = Field(
        default=None,
        description="Telegram webhook URL (optional)",
    )
    
    # Backend Settings
    backend_base_url: str = Field(
        default="http://localhost:8000",
        description="Backend base URL",
    )
    
    # Frontend Settings
    frontend_allowed_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:3000",
        ],
        description="Allowed CORS origins for frontend",
    )
    
    # Redis Settings (for caching and rate limiting)
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (optional, for caching)",
    )
    
    # Security Settings
    encryption_key: Optional[str] = Field(
        default=None,
        description="Encryption key for sensitive data (optional)",
        min_length=32,
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per IP",
        gt=0,
    )
    rate_limit_auth_per_minute: int = Field(
        default=5,
        description="Maximum auth requests per minute per IP",
        gt=0,
    )
    
    # File Upload Settings
    max_upload_size_mb: int = Field(
        default=10,
        description="Maximum file upload size in MB",
        gt=0,
        le=100,
    )
    allowed_upload_extensions: list[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".pdf", ".txt", ".doc", ".docx"],
        description="Allowed file extensions for uploads",
    )
    
    # Logging Settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)",
    )
    
    # ============================================================================
    # Validators
    # ============================================================================
    
    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is strong enough."""
        if len(v) < 32:
            raise ValueError(
                "JWT secret key must be at least 32 characters long for security. "
                "Generate a strong secret using: openssl rand -hex 32"
            )
        return v
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v_upper
    
    @field_validator("frontend_allowed_origins", mode="before")
    @classmethod
    def parse_frontend_origins(cls, v):
        """Parse frontend origins from string or list."""
        if v is None:
            # Return default if not set
            return ["http://localhost:5173", "http://localhost:3000"]
        if isinstance(v, str):
            # Handle empty string
            if not v.strip():
                return ["http://localhost:5173", "http://localhost:3000"]
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        # If it's some other type, try to convert to string first
        try:
            return [origin.strip() for origin in str(v).split(",") if origin.strip()]
        except Exception:
            raise ValueError(f"Cannot parse frontend_allowed_origins from value: {v}")
    
    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate encryption key if provided."""
        if v is not None and len(v) < 32:
            raise ValueError(
                "Encryption key must be at least 32 characters long. "
                "Generate using: openssl rand -hex 32"
            )
        return v
    
    # ============================================================================
    # Helper Properties
    # ============================================================================
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024
    
    def get_cors_origins(self) -> list[str]:
        """Get list of allowed CORS origins."""
        # In production, never allow wildcard
        if self.is_production and "*" in self.frontend_allowed_origins:
            raise ValueError("Wildcard CORS origin not allowed in production")
        return self.frontend_allowed_origins


# ============================================================================
# Global Settings Instance
# ============================================================================

def get_settings() -> Settings:
    """Get application settings instance.
    
    This function creates and validates settings on first call.
    Subsequent calls return the cached instance.
    
    Raises:
        ValidationError: If required environment variables are missing or invalid.
    """
    return Settings()


# Create settings instance at module import
# This will fail fast if configuration is invalid
try:
    settings = get_settings()
except Exception as e:
    import sys
    print(f"❌ Configuration Error: {e}", file=sys.stderr)
    print("\n📋 Required environment variables:", file=sys.stderr)
    print("  - SUPABASE_URL", file=sys.stderr)
    print("  - SUPABASE_SERVICE_KEY", file=sys.stderr)
    print("  - SUPABASE_ANON_KEY", file=sys.stderr)
    print("  - JWT_SECRET_KEY (min 32 chars)", file=sys.stderr)
    print("  - YANDEX_GPT_API_KEY", file=sys.stderr)
    print("  - YANDEX_FOLDER_ID", file=sys.stderr)
    print("\n💡 Generate secrets using: openssl rand -hex 32", file=sys.stderr)
    sys.exit(1)
