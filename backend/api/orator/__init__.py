from fastapi import APIRouter

from . import profiles, weeks, topics, matching, pairs, feedback, content, settings

# Создаем главный роутер
router = APIRouter()

# Подключаем все подроутеры с соответствующими префиксами
router.include_router(profiles.router, tags=["Profiles"])
router.include_router(weeks.router, prefix="/weeks", tags=["Weeks"])
router.include_router(topics.router, prefix="/topics", tags=["Topics"])
router.include_router(matching.router, prefix="/matching", tags=["Matching"])
router.include_router(pairs.router, prefix="/pairs", tags=["Pairs"])
router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
router.include_router(content.router, tags=["Content"])

router.include_router(settings.router, prefix="/settings", tags=["Settings"])
