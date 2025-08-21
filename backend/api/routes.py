from fastapi import APIRouter
from api import auth, health, user_settings
from api.orator import router as orator_router

router = APIRouter()

# Подключение всех роутеров
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(user_settings.router, prefix="/settings", tags=["User Settings"])

router.include_router(orator_router, prefix="/orator", tags=["Alex Orator Bot"])
