import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Основные настройки бота
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Настройки API
API_TIMEOUT = 30
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 1

# Настройки сообщений
MAX_MESSAGE_LENGTH = 4096
MAX_RESULTS_DISPLAY = 50

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "logs/telegram-bot.log"

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable is required")

if not BACKEND_URL:
    raise ValueError("BACKEND_URL environment variable is required")

# Создание директории для логов
os.makedirs("logs", exist_ok=True)
