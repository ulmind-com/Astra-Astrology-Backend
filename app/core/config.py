"""Application settings, loaded from environment / .env file."""

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------------------------------------------------------- app
    APP_NAME: str = "Astra Astrology"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-me"

    # CORS — comma separated list in .env (NoDecode: parsed by the validator
    # below, not as JSON).
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"]
    )

    # ------------------------------------------------------------- mongodb
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "astra_astrology"
    MONGODB_MAX_POOL_SIZE: int = 100
    MONGODB_MIN_POOL_SIZE: int = 0

    # -------------------------------------------------------------- resend
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "no-reply@example.com"
    RESEND_FROM_NAME: str = "Astra Astrology"
    SUPPORT_EMAIL: str = "support@example.com"

    # ---------------------------------------------------------- cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_UPLOAD_FOLDER: str = "astra-astrology"
    CLOUDINARY_SECURE: bool = True
    MAX_UPLOAD_SIZE_MB: int = 10

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def cloudinary_configured(self) -> bool:
        return bool(
            self.CLOUDINARY_CLOUD_NAME and self.CLOUDINARY_API_KEY and self.CLOUDINARY_API_SECRET
        )

    @property
    def resend_configured(self) -> bool:
        return bool(self.RESEND_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
