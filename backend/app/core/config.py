from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================================================
    # Application
    # =========================================================

    APP_NAME: str = "AI Root Cause Investigator"
    APP_VERSION: str = "1.0.0"

    # development | testing | production
    ENVIRONMENT: Literal[
        "development",
        "testing",
        "production",
    ] = "development"

    DEBUG: bool = True
    TESTING: bool = False

    # =========================================================
    # Security
    # =========================================================

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15

    # =========================================================
    # Database
    # =========================================================

    DATABASE_URL: str

    # =========================================================
    # Groq
    # =========================================================

    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MAX_RETRIES: int = 3
    GROQ_RETRY_DELAY: int = 2

    # =========================================================
    # Email / SMTP
    # =========================================================

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "AI Root Cause Investigator"
    SMTP_USE_TLS: bool = True

    # =========================================================
    # Slack
    # =========================================================

    SLACK_WEBHOOK_URL: str = ""
    SLACK_TIMEOUT: int = 10

    # =========================================================
    # Microsoft Teams
    # =========================================================

    TEAMS_WEBHOOK_URL: str = ""
    TEAMS_TIMEOUT: int = 10

    # =========================================================
    # Upload
    # =========================================================

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    # =========================================================
    # API request body protection
    # =========================================================

    MAX_REQUEST_BODY_SIZE: int = 12 * 1024 * 1024

    # =========================================================
    # Logging
    # =========================================================

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    # =========================================================
    # Vector Database
    # =========================================================

    # =========================================================
    # Vector Database
    # =========================================================

    CHROMA_DB_PATH: str = "./chroma_db"

    QDRANT_URL: str = "memory://"
    QDRANT_COLLECTION: str = "investigation_memory"
    QDRANT_API_KEY: str = ""
    QDRANT_TIMEOUT: float = 10.0
    # =========================================================
    # Embeddings
    # =========================================================

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # =========================================================
    # Agent Execution Timeout
    # =========================================================

    AGENT_TIMEOUT_SECONDS: float = 60.0
    INVESTIGATION_TIMEOUT_SECONDS: float = 300.0
    RECOVERY_TIMEOUT_SECONDS: float = 30.0

    # =========================================================
# Production security validation
# =========================================================

    @model_validator(mode="after")
    def validate_production_security(self):
        """
        Prevent insecure configuration from being used
        in production.
        """

        if self.TESTING:
            return self

        if self.ENVIRONMENT == "production":

            if self.DEBUG:
                raise ValueError(
                    "DEBUG must be False in production."
                )

            if not self.SECRET_KEY:
                raise ValueError(
                    "SECRET_KEY must be configured in production."
                )

            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must contain at least "
                    "32 characters in production."
                )

            insecure_secrets = {
                "change_this_to_a_long_random_secret_key",
                "change_me",
                "secret",
                "changeme",
                "your_secret_key",
            }

            if self.SECRET_KEY.lower() in insecure_secrets:
                raise ValueError(
                    "SECRET_KEY contains an insecure "
                    "placeholder value."
                )

            if not self.DATABASE_URL:
                raise ValueError(
                    "DATABASE_URL must be configured in production."
                )

            if not self.GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY must be configured in production."
                )

        return self

    def validate_production(self) -> None:
        """Explicitly validate configuration required outside testing."""

        if self.TESTING:
            return

        if self.DEBUG and self.ENVIRONMENT == "production":
            raise ValueError(
            "DEBUG must be False in production."
        )

        if not self.SECRET_KEY:
            raise ValueError(
            "SECRET_KEY must be configured when TESTING=False."
        )

        if len(self.SECRET_KEY) < 32:
            raise ValueError(
            "SECRET_KEY must be at least 32 characters long."
        )

        if not self.DATABASE_URL:
            raise ValueError(
            "DATABASE_URL must be configured when TESTING=False."
        )

        if not self.GROQ_API_KEY:
            raise ValueError(
            "GROQ_API_KEY must be configured when TESTING=False."
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
