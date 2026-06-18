from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.health import HealthResponse
from app.models.diagnosis import Diagnosis, DiagnosisResponse
from app.services.investigation import run_investigation
from app.ai.agent import analyze_cluster

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", service="ai-kubernetes-agent")


@router.post("/investigate", response_model=DiagnosisResponse)
async def investigate() -> DiagnosisResponse:
    try:
        logger.info("POST /investigate — starting pipeline")

        evidence = run_investigation()
        diagnosis_data = analyze_cluster(evidence)

        return DiagnosisResponse(
            status="success",
            diagnosis=Diagnosis(**diagnosis_data),
        )

    except ValueError as e:
        # Configuration errors (e.g. missing API key) — 400 so the caller knows to fix config
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Investigation pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
