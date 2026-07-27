from fastapi import APIRouter
from app.shared.responses import APIResponse
from app.core.config import settings
from app.core.constants import STATUS_OK

router = APIRouter()

@router.get("/", response_model=APIResponse[dict])
def read_root():
    return APIResponse(
        success=True,
        message="Welcome to the AIVOA CCMS API",
        data={
            "project_name": settings.PROJECT_NAME,
            "version": settings.API_VERSION
        }
    )

@router.get("/health", response_model=APIResponse[dict])
def check_health():
    return APIResponse(
        success=True,
        message="Health check passed",
        data={"status": STATUS_OK}
    )

@router.get("/ready", response_model=APIResponse[dict])
def check_ready():
    # In a real app, check DB connection here
    return APIResponse(
        success=True,
        message="Service is ready",
        data={"status": STATUS_OK}
    )
