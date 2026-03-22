from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="backend/.env", extra="ignore")

    APP_ENV: str = "development"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DART_API_KEY: str = ""
    KRX_AUTH_KEY: str = ""
    KRX_KOSPI_DAILY_API_URL: str = "https://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd"
    KRX_KOSDAQ_DAILY_API_URL: str = "https://data-dbg.krx.co.kr/svc/apis/sto/ksq_bydd_trd"
    KRX_KONEX_DAILY_API_URL: str = ""
    KRX_REQUEST_TIMEOUT_SECONDS: int = 30
    MARKET_CACHE_DIR: str = "data/cache/runtime"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5500,http://127.0.0.1:5500"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [item.strip() for item in self.ALLOWED_ORIGINS.split(",") if item.strip()]


settings = Settings()
