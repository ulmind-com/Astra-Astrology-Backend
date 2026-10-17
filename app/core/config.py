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

    # CORS — comma separated list in .env, or `*` for every origin (NoDecode:
    # parsed by the validator below, not as JSON).
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])

    # ------------------------------------------------------------- mongodb
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "astra_astrology"
    MONGODB_MAX_POOL_SIZE: int = 100
    MONGODB_MIN_POOL_SIZE: int = 0
    MONGODB_CONNECT_TIMEOUT_MS: int = 10_000

    # ------------------------------------------------------------- health
    # Keep the health check fast so uptime monitors never time out on it.
    HEALTH_DB_TIMEOUT_SECONDS: float = 3.0

    # ----------------------------------------------------------------- jwt
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ----------------------------------------------------------------- otp
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    # When true the OTP comes back in the API response. Local development only.
    OTP_DEV_MODE: bool = False
    # How long a half-finished signup (awaiting its OTP) is kept.
    PENDING_REGISTRATION_EXPIRE_MINUTES: int = 30

    # ------------------------------------------------------------ firebase
    # Service account credentials. Use the PATH locally and the inline JSON on
    # hosts where you cannot upload a file (Render, Railway, ...).
    FIREBASE_CREDENTIALS_PATH: str = ""
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_PROJECT_ID: str = ""
    # Refuse to register anyone while Firebase is unreachable, rather than
    # creating a MongoDB user that has no Firebase twin.
    FIREBASE_REQUIRED: bool = True

    # -------------------------------------------------------- first admin
    # Used by: uv run python -m scripts.create_admin
    FIRST_ADMIN_NAME: str = "Super Admin"
    FIRST_ADMIN_EMAIL: str = ""
    FIRST_ADMIN_PASSWORD: str = ""

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

    # Avatars are compressed by Cloudinary before being stored, not on delivery,
    # so the stored asset itself is the small one.
    AVATAR_MAX_DIMENSION: int = 512
    AVATAR_QUALITY: str = "auto:good"
    AVATAR_FORMAT: str = "webp"

    # ------------------------------------------------------------ razorpay
    # Money is held in integer paise everywhere; rupees appear only in the UI.
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    # Set in the Razorpay dashboard under Settings -> Webhooks. Without it the
    # webhook cannot be trusted, so it is refused rather than processed.
    RAZORPAY_WEBHOOK_SECRET: str = ""

    WALLET_CURRENCY: str = "INR"
    WALLET_MIN_RECHARGE_PAISE: int = 1_000  # Rs 10
    WALLET_MAX_RECHARGE_PAISE: int = 5_000_000  # Rs 50,000
    # Preset amounts offered on the recharge screen, in paise.
    RECHARGE_PACKS_PAISE: Annotated[list[int], NoDecode] = Field(
        default_factory=lambda: [10_000, 25_000, 50_000, 100_000, 200_000, 500_000]
    )
    # How many orders one user may open per hour, so the endpoint cannot be
    # used to hammer Razorpay.
    RECHARGE_ORDERS_PER_HOUR: int = 20

    @field_validator("RECHARGE_PACKS_PAISE", mode="before")
    @classmethod
    def _split_packs(cls, v: object) -> object:
        if isinstance(v, str):
            return [int(p.strip()) for p in v.split(",") if p.strip()]
        return v

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

    @property
    def razorpay_configured(self) -> bool:
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)

    @property
    def razorpay_webhook_configured(self) -> bool:
        return bool(self.RAZORPAY_WEBHOOK_SECRET)

    @property
    def razorpay_is_test_key(self) -> bool:
        return self.RAZORPAY_KEY_ID.startswith("rzp_test_")

    @property
    def firebase_configured(self) -> bool:
        return bool(self.FIREBASE_CREDENTIALS_PATH or self.FIREBASE_CREDENTIALS_JSON)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
