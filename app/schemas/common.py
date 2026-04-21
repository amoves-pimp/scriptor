from pydantic import BaseModel


class ApiResponse(BaseModel):
    status: str
