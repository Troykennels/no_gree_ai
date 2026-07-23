"""Application configuration, loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_JWT_DEFAULT = "dev-insecure-change-me"
DEV_DB_PASSWORD = "securenaija_dev_password"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name: str = "No_Gree AI API"
    api_env: str = Field(default="development", alias="API_ENV")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://securenaija:securenaija_dev_password@localhost:5432/securenaija",
        alias="DATABASE_URL",
    )

    # Security
    jwt_secret_key: str = Field(default=INSECURE_JWT_DEFAULT, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # CORS (comma-separated)
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # ML
    model_registry_dir: str | None = Field(default=None, alias="MODEL_REGISTRY_DIR")

    # RBAC: comma-separated emails that are granted the admin role automatically
    # (on registration and at startup). Everyone else is a normal user.
    admin_emails: str = Field(default="", alias="ADMIN_EMAILS")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

    @property
    def is_production(self) -> bool:
        return self.api_env.lower() in {"production", "prod"}

    @model_validator(mode="after")
    def _forbid_insecure_defaults_in_production(self) -> "Settings":
        """Fail fast rather than silently ship a public signing key or password.

        In development the defaults keep the app runnable out of the box; in
        production an unset JWT_SECRET_KEY would let anyone forge tokens, and the
        default DB password is public in source — so we refuse to start.
        """
        if self.is_production:
            problems = []
            if self.jwt_secret_key == INSECURE_JWT_DEFAULT:
                problems.append("JWT_SECRET_KEY must be set to a strong secret")
            if DEV_DB_PASSWORD in self.database_url:
                problems.append("DATABASE_URL must not use the default dev password")
            if problems:
                raise ValueError(
                    "Insecure configuration for API_ENV=production: "
                    + "; ".join(problems)
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
