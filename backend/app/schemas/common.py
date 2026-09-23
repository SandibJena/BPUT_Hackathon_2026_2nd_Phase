from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    detail: str
    code: str

class HealthResponse(BaseModel):
    status: str
    version: str
    disclaimer: str
