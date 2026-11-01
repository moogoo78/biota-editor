from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

WEAK_SECRETS = {"", "dev-secret-change-me", "change-me", "changeme", "secret"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "production" (set by the prod image) refuses a missing or weak SECRET_KEY
    app_env: str = "development"
    secret_key: str = "dev-secret-change-me"
    database_url: str = "sqlite:////data/biotaeditor.sqlite"
    cors_origins: str = "http://localhost:5180,http://127.0.0.1:5180"
    token_ttl_hours: int = 24 * 7
    allow_signup: bool = True

    # TaiCOL nametool
    taicol_api: str = "https://nametool.taicol.tw/api"
    taicol_token: str = ""
    taicol_public_api: str = "https://api.taicol.tw/v2"
    # skip the /user/namespace ownership check (local dev without TaiCOL access)
    taicol_skip_ownership: bool = False
    # optional shared secret for POST /api/hooks (header X-Webhook-Token or ?token=)
    webhook_secret: str = ""

    # tbia-specimen-annotation (ISLAND)
    tbia_api: str = "http://host.docker.internal:8000"
    tbia_web: str = "http://localhost:5173"

    # images
    taieol_api: str = "https://data.taieol.tw/api/v2"
    taieol_token: str = ""
    inat_api: str = "https://api.inaturalist.org/v1"

    http_timeout: float = 20.0
    cache_ttl: int = 600

    @model_validator(mode="after")
    def _check_secret(self):
        if self.app_env == "production" and (self.secret_key in WEAK_SECRETS or len(self.secret_key) < 32):
            raise ValueError(
                "SECRET_KEY must be set to a random value of 32+ characters in production, "
                "e.g. python -c 'import secrets; print(secrets.token_urlsafe(48))'")
        return self

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# hosts the exporter may download figures from (selected images only)
IMAGE_HOSTS = (
    "inaturalist-open-data.s3.amazonaws.com",
    "static.inaturalist.org",
    "data.taieol.tw",
)
