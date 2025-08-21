#!/bin/bash

# Тестовый скрипт для проверки логики .deployignore
# Запускается из директории deployment

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🧪 Тестирование логики деплоя..."
echo ""

# Проверка существования .deployignore
echo "1. Проверка .deployignore файла:"
if [ -f "../.deployignore" ]; then
    echo -e "${GREEN}✅ .deployignore найден${NC}"
    echo "📊 Количество строк исключений: $(wc -l < ../.deployignore)"
else
    echo -e "${RED}❌ .deployignore не найден${NC}"
fi
echo ""

# Тест rsync локально
echo "2. Тест rsync с .deployignore (локально):"
if rsync --dry-run -av --exclude-from=../.deployignore ../ /tmp/test-deploy-logic/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ rsync с .deployignore работает${NC}"
    FILES_TO_COPY=$(rsync --dry-run -av --exclude-from=../.deployignore ../ /tmp/test-deploy-logic/ | grep -v '^Transfer starting\|^$' | wc -l)
    echo "📁 Файлов для копирования: $FILES_TO_COPY"
else
    echo -e "${RED}❌ rsync с .deployignore не работает${NC}"
fi
echo ""

# Проверка исключений
echo "3. Проверка что исключаются нужные файлы:"
rsync --dry-run -av --exclude-from=../.deployignore ../ /tmp/test-deploy-logic/ > /tmp/rsync_output.txt 2>&1

EXCLUDED_ITEMS=(
    ".git"
    "__pycache__"
    "venv"
    ".pytest_cache"
    "node_modules"
    "*.pyc"
)

for item in "${EXCLUDED_ITEMS[@]}"; do
    if ! grep -q "$item" /tmp/rsync_output.txt; then
        echo -e "${GREEN}✅ $item исключен${NC}"
    else
        echo -e "${YELLOW}⚠️  $item может быть включен${NC}"
    fi
done
echo ""

# Проверка что включаются нужные файлы
echo "4. Проверка что включаются важные файлы:"
REQUIRED_FILES=(
    "docker-compose.yml"
    ".env"
    "backend/"
    "telegram-bot/"
    "deployment/"
)

for file in "${REQUIRED_FILES[@]}"; do
    if grep -q "$file" /tmp/rsync_output.txt; then
        echo -e "${GREEN}✅ $file включен${NC}"
    else
        echo -e "${RED}❌ $file не найден${NC}"
    fi
done
echo ""

echo "✅ Тест завершен"
echo ""
echo "💡 Полный вывод rsync сохранен в /tmp/rsync_output.txt"

# Cleanup
rm -f /tmp/rsync_output.txt >/dev/null 2>&1