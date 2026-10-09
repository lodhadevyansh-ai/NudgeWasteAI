"""
Health Check Router.
Provides service health and database connectivity diagnostics status endpoint.
"""

from fastapi import APIRouter
from app.core.config import settings  # pyrefly: ignore [missing-import]
from app.core.constants import STATUS_HEALTHY, STATUS_UNHEALTHY  # pyrefly: ignore [missing-import]
from database.connection import check_database_health  # pyrefly: ignore [missing-import]

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health Check")
async def health_check():
    """
    Health check endpoint returning application status, service name, environment, version, and database status.
    """
    db_health = check_database_health()
    return {
        "status": STATUS_HEALTHY if db_health.get("is_connected", True) else STATUS_UNHEALTHY,
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "database": {
            "status": db_health.get("status"),
            "connected": db_health.get("is_connected"),
            "database_name": db_health.get("database_name"),
            "latency_ms": db_health.get("latency_ms"),
        },
    }


@router.get("/health/ml", summary="ML Model Health Check")
async def ml_health_check():
    """
    ML model health check endpoint returning model loading status, version, device, and classes.
    """
    from app.services.classification_service import classification_service
    return classification_service.get_health()