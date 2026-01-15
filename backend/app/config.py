"""
Application configuration management using Pydantic Settings.
Loads configuration from environment variables and .env file.
"""

from functools import lru_cache
from typing import Any

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and type safety."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_parse_none_str="null",
    )

    # Application
    app_name: str = Field(default="Event Management SaaS")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/event_management"
    )
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=0)

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")
    redis_cache_db: int = Field(default=1)

    # Celery
    celery_broker_url: RedisDsn = Field(default="redis://localhost:6379/2")
    celery_result_backend: RedisDsn = Field(default="redis://localhost:6379/3")

    # Security
    secret_key: str = Field(default="development_secret_key_change_in_production_min_32_chars", min_length=32)
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    refresh_token_expire_days: int = Field(default=7)

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:19006"
    )
    cors_allow_credentials: bool = Field(default=True)

    @field_validator("cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # File Upload
    max_upload_size: int = Field(default=10485760)  # 10MB
    upload_dir: str = Field(default="/tmp/uploads")
    allowed_extensions: str = Field(default="xlsx,xls,csv")

    @field_validator("allowed_extensions", mode="after")
    @classmethod
    def parse_allowed_extensions(cls, v: str) -> list[str]:
        """Parse allowed extensions from comma-separated string."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    # Cloud Storage (GCP)
    gcp_project_id: str | None = Field(default=None)
    gcp_bucket_name: str | None = Field(default=None)
    gcp_credentials_path: str | None = Field(default=None)

    # Vector Database (Qdrant)
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str | None = Field(default=None)
    qdrant_collection_name: str = Field(default="event_management_embeddings")

    # OpenAI
    openai_api_key: str = Field(default="sk-dummy-key-replace-with-real-one")
    openai_model: str = Field(default="gpt-4-turbo-preview")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    openai_max_tokens: int = Field(default=4000)
    openai_temperature: float = Field(default=0.1)

    # Google Gemini (Alternative to OpenAI)
    gemini_api_key: str | None = Field(default=None)
    gemini_model: str = Field(default="gemini-1.5-flash")  # Free and fast model
    use_gemini: bool = Field(default=False)  # Set to True to use Gemini instead of OpenAI

    # Email (Resend - preferred) and SendGrid (fallback)
    resend_api_key: str | None = Field(default=None)
    sendgrid_api_key: str | None = Field(default=None)
    from_email: str = Field(default="noreply@example.com")
    from_name: str = Field(default="Event Management System")
    frontend_url: str = Field(default="http://localhost:5173")

    # SMS (Twilio)
    twilio_account_sid: str | None = Field(default=None)
    twilio_auth_token: str | None = Field(default=None)
    twilio_phone_number: str | None = Field(default=None)

    # Calendar Integration
    google_calendar_credentials: str | None = Field(default=None)
    microsoft_calendar_client_id: str | None = Field(default=None)
    microsoft_calendar_client_secret: str | None = Field(default=None)

    # Monitoring
    sentry_dsn: str | None = Field(default=None)
    sentry_environment: str = Field(default="development")
    sentry_traces_sample_rate: float = Field(default=0.1)

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_per_hour: int = Field(default=1000)

    # Indian Financial Year
    financial_year_start_month: int = Field(default=4)
    financial_year_start_day: int = Field(default=1)

    # Timezone
    default_timezone: str = Field(default="Asia/Kolkata")

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic migrations."""
        return str(self.database_url).replace("+asyncpg", "")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
