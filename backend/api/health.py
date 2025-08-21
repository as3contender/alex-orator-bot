from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import Dict, Any

from services.app_database import app_database_service

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Базовый health check"""
    return {"status": "healthy", "service": "cloverdashbot-backend"}


@router.get("/info")
async def detailed_health_check() -> Dict[str, Any]:
    """Детальная информация о состоянии всех компонентов"""
    health_info = {"status": "healthy", "service": "cloverdashbot-backend", "components": {}}

    # Проверка Application Database
    try:
        await app_database_service.check_connection()
        health_info["components"]["app_database"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"App database health check failed: {e}")
        health_info["components"]["app_database"] = {"status": "unhealthy", "error": str(e)}
        health_info["status"] = "degraded"

    return health_info


@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """Readiness check для Kubernetes"""
    try:
        # Проверяем все критические компоненты
        await app_database_service.check_connection()

        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """Liveness check для Kubernetes"""
    return {"status": "alive"}
