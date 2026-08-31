"""Runtime configuration, loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    vault_key: str = ""
    database_url: str = "sqlite:///./data/trading.db"
    broker: str = "paper"
    admin_token: str = "change-me"
    dry_run: bool = True

    paytm_api_key: str = ""
    paytm_api_secret: str = ""
    paytm_login_id: str = ""
    paytm_password: str = ""
    paytm_totp_secret: str = ""

    universe: str = "RELIANCE,TCS,HDFCBANK,INFY,ICICIBANK"
    capital: float = 100_000.0
    max_position_pct: float = 0.15
    max_daily_loss_pct: float = 0.03
    max_open_positions: int = 5

    @property
    def symbols(self) -> list[str]:
        return [s.strip().upper() for s in self.universe.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
