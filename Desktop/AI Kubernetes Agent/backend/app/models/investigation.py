from pydantic import BaseModel


class InvestigationResponse(BaseModel):
    status: str
    investigation: dict
