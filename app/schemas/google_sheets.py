from pydantic import BaseModel, Field


class GoogleSheetsTaskRequest(BaseModel):
    task_id: str


class GoogleSheetsReadRequest(BaseModel):
    task_id: str
    limit: int = Field(default=1000, ge=1, le=1000)
