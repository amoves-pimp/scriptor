import httpx
from urllib.parse import quote

from app.config import settings


class GoogleSheetsClient:
    def _access_token(self) -> str:
        payload = {
            'client_id': settings.google_client_id,
            'client_secret': settings.google_client_secret,
            'refresh_token': settings.google_refresh_token,
            'grant_type': 'refresh_token',
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(settings.google_oauth_token_url, data=payload)
            response.raise_for_status()
            data = response.json()
            token = data.get('access_token')
            if not token:
                raise ValueError('missing access_token in Google OAuth token response')
            return token

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self._access_token()}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def get_spreadsheet(self, spreadsheet_id: str) -> dict:
        url = f"{settings.google_sheets_base_url}/{spreadsheet_id}"
        params = {'fields': 'spreadsheetId,properties.title,sheets.properties'}
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=self._headers(), params=params)
            response.raise_for_status()
            return response.json()

    def add_sheet(self, spreadsheet_id: str, tab_name: str) -> dict:
        url = f"{settings.google_sheets_base_url}/{spreadsheet_id}:batchUpdate"
        body = {'requests': [{'addSheet': {'properties': {'title': tab_name}}}]}
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=self._headers(), json=body)
            response.raise_for_status()
            return response.json()

    def clear_values(self, spreadsheet_id: str, tab_name: str) -> dict:
        encoded_range = quote(f"'{tab_name}'!A:ZZ", safe='')
        url = f"{settings.google_sheets_base_url}/{spreadsheet_id}/values/{encoded_range}:clear"
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=self._headers(), json={})
            response.raise_for_status()
            return response.json()

    def update_values(self, spreadsheet_id: str, tab_name: str, values: list[list[str]]) -> dict:
        encoded_range = quote(f"'{tab_name}'!A1", safe='')
        url = f"{settings.google_sheets_base_url}/{spreadsheet_id}/values/{encoded_range}"
        params = {'valueInputOption': 'RAW'}
        body = {'range': f"'{tab_name}'!A1", 'majorDimension': 'ROWS', 'values': values}
        with httpx.Client(timeout=30.0) as client:
            response = client.put(url, headers=self._headers(), params=params, json=body)
            response.raise_for_status()
            return response.json()

    def read_values(self, spreadsheet_id: str, tab_name: str, limit: int) -> dict:
        encoded_range = quote(f"'{tab_name}'!A1:ZZ{limit}", safe='')
        url = f"{settings.google_sheets_base_url}/{spreadsheet_id}/values/{encoded_range}"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()


google_sheets_client = GoogleSheetsClient()
