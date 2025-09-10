from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from loguru import logger

from config.settings import settings
from api.routes import router as api_router
from services.app_database import app_database_service
from services.orator_database import orator_db


# Настройка логирования
logger.add("logs/backend.log", rotation="1 day", retention="7 days", level="INFO")

app = FastAPI(
    title="CloverdashBot Backend",
    description="Backend API для интеллектуальной системы анализа данных",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(api_router, prefix="/api/v1")

# Подключение статических файлов (если директория существует)
import os

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
async def startup_event():
    logger.info("Starting CloverdashBot Backend...")

    # Инициализация подключений к базам данных
    try:
        await app_database_service.connect()
        await orator_db.connect()

        logger.info("Database connections established")
    except Exception as e:
        logger.error(f"Failed to connect to databases: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down CloverdashBot Backend...")

    # Закрытие подключений к базам данных
    try:
        await app_database_service.disconnect()
        await orator_db.disconnect()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Failed to close database connections: {e}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug, log_level="info")
