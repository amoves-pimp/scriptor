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
    yandex_search_api_key: str = 'change-me'
    yandex_search_folder_id: str = 'change-me'
    yandex_search_base_url: str = 'https://searchapi.api.cloud.yandex.net'
    yandex_search_timeout_seconds: float = 30.0
    google_client_id: str = 'change-me'
    google_client_secret: str = 'change-me'
    google_refresh_token: str = 'change-me'
    google_sheets_spreadsheet_id: str = 'change-me'
    google_oauth_token_url: str = 'https://oauth2.googleapis.com/token'
    google_sheets_base_url: str = 'https://sheets.googleapis.com/v4/spreadsheets'
    google_sheets_max_rows_per_request: int = 1000
    log_level: str = 'INFO'
    data_dir: str = 'data'
    request_delay_ms: int = 1000
    max_concurrency: int = 1

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir)


settings = Settings()
