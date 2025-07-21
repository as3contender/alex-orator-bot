from fastapi import APIRouter
from api import auth, database, health, user_settings

router = APIRouter()

# Подключение всех роутеров
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(database.router, prefix="/database", tags=["Database"])
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(user_settings.router, prefix="/settings", tags=["User Settings"])
