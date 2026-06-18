from pydantic import BaseModel, Field


class Diagnosis(BaseModel):
    root_cause: str
    explanation: str
    fix: str
    kubectl_commands: list[str]
    prevention: str
    confidence: int = Field(ge=0, le=100)


class DiagnosisResponse(BaseModel):
    status: str
    diagnosis: Diagnosis
