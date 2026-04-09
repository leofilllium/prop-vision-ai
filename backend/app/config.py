"""
PropVision.AI Backend Application Configuration.

Loads all settings from environment variables using Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://propvision:propvision_secret@localhost:5432/propvision",
        description="PostgreSQL connection string with asyncpg driver",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # OpenAI
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for GPT-4o-mini query parsing",
    )

    # Meshy AI (Image-to-3D)
    meshy_api_key: str = Field(
        default="",
        description="Meshy AI API key for image-to-3D generation (get from meshy.ai)",
    )

    # Pollinations (Video Walkthrough) — https://gen.pollinations.ai
    pollinations_api_key: str = Field(
        default="",
        description="Pollinations API key for img2video generation (get from enter.pollinations.ai)",
    )

    # Mapbox
    mapbox_access_token: str = Field(
        default="",
        description="Mapbox access token for map tile generation",
    )

    # Google Places
    google_places_api_key: str = Field(
        default="",
        description="Google Places API key for POI data",
    )

    # AWS S3
    aws_access_key_id: str = Field(default="")
    aws_secret_access_key: str = Field(default="")
    aws_region: str = Field(default="us-east-1")
    s3_bucket_name: str = Field(default="propvision-models")
    s3_endpoint_url: str = Field(
        default="https://s3.us-east-1.amazonaws.com",
        description="S3-compatible endpoint URL",
    )

    # Uybor.uz Marketplace Integration
    uybor_api_base_url: str = Field(
        default="https://api.uybor.uz/api/v1/listings",
        description="Uybor.uz API endpoint for listings",
    )
    uybor_sync_enabled: bool = Field(
        default=True,
        description="Whether to run the daily Uybor sync job",
    )

    # API Security
    api_secret_key: str = Field(
        default="change-me-in-production-minimum-32-characters-long",
        description="Secret key for hashing and signing",
    )

    # JWT
    jwt_secret_key: str = Field(
        default="change-me-in-production-minimum-32-characters-long",
        description="Secret key for signing JWT tokens (use a strong random value)",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=60 * 24, description="JWT expiry in minutes (default 24 h)")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins",
    )

    # Application
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=100,
        description="Maximum API requests per minute per API key",
    )

    # Comfort Score Weights (configurable per deployment)
    comfort_weight_transport: float = Field(default=0.20)
    comfort_weight_shopping: float = Field(default=0.15)
    comfort_weight_education: float = Field(default=0.15)
    comfort_weight_green_space: float = Field(default=0.10)
    comfort_weight_safety: float = Field(default=0.15)
    comfort_weight_healthcare: float = Field(default=0.15)
    comfort_weight_entertainment: float = Field(default=0.10)

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def comfort_weights(self) -> dict[str, float]:
        """Return comfort score weights as a dictionary."""
        return {
            "transport": self.comfort_weight_transport,
            "shopping": self.comfort_weight_shopping,
            "education": self.comfort_weight_education,
            "green_space": self.comfort_weight_green_space,
            "safety": self.comfort_weight_safety,
            "healthcare": self.comfort_weight_healthcare,
            "entertainment": self.comfort_weight_entertainment,
        }

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Create cached Settings instance. Call this function to access settings."""
    return Settings()


# Global settings instance for easy importing
settings = get_settings()
