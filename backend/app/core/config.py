import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FoodLoop AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development") # development | staging | production
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-insecure-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Supabase & Database Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://your-project-ref.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "your-supabase-anon-key")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./foodloop.db")
    FALLBACK_SQLITE_URL: str = "sqlite:///./foodloop.db"

    # Storage Buckets
    SUPABASE_STORAGE_BUCKET_DOCUMENTS: str = os.getenv("SUPABASE_STORAGE_BUCKET_DOCUMENTS", "foodloop-documents")
    SUPABASE_STORAGE_BUCKET_AVATARS: str = os.getenv("SUPABASE_STORAGE_BUCKET_AVATARS", "foodloop-avatars")
    SUPABASE_STORAGE_BUCKET_IMAGES: str = os.getenv("SUPABASE_STORAGE_BUCKET_IMAGES", "foodloop-images")

    # LLM Settings (Provider Agnostic)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")  # "gemini", "openai", "anthropic", "mock"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Mapbox & Routing
    MAPBOX_ACCESS_TOKEN: str = os.getenv("MAPBOX_ACCESS_TOKEN", "pk.demo_mapbox_token")

    # Monitoring & Observability
    PROMETHEUS_METRICS_ENABLED: bool = os.getenv("PROMETHEUS_METRICS_ENABLED", "true").lower() in ("true", "1", "yes")
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://foodloop-ai.vercel.app"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i) for i in v]
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://foodloop-ai.vercel.app"
        ]

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        extra="ignore"
    )


settings = Settings()

