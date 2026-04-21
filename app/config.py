from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    scriptor_auth_token: str = 'change-me'
    octoclick_api_key: str = 'change-me'
    octoclick_base_url: str = 'https://api.octoclick.com/api/v4'
    octoclick_role: str = 'hunter'
    octoclick_lang: str = 'en'
    octoclick_timeout_seconds: float = 30.0
    log_level: str = 'INFO'
    data_dir: str = 'data'
    request_delay_ms: int = 1000
    max_concurrency: int = 1

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)


settings = Settings()
