# 🐍 Настройка Python окружения

## Обзор

Alex Orator Bot использует Python 3.12.0 для генерации ключей и утилит. Проект настроен для работы с pyenv и виртуальными окружениями.

## 🚀 Быстрая настройка

### 1. Проверка Python версии

```bash
# Проверка текущей версии
python --version

# Должно быть: Python 3.12.0
```

### 2. Настройка pyenv (если не настроен)

```bash
# Добавить в ~/.zshrc
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - zsh)"

# Перезагрузить shell
source ~/.zshrc
```

### 3. Установка Python 3.12.0

```bash
# Установка версии (если не установлена)
pyenv install 3.12.0

# Установка локальной версии для проекта
pyenv local 3.12.0
```

### 4. Создание виртуального окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация
source venv/bin/activate

# Обновление pip
pip install --upgrade pip
```

### 5. Установка зависимостей

```bash
# Установка всех зависимостей
pip install -r requirements.txt

# Или только основных
pip install cryptography python-dotenv
```

## 🔧 Использование

### Генерация ключей

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Генерация ключей
python generate_keys.py
```

### Проверка окружения

```bash
# Проверка Python версии
python --version

# Проверка установленных пакетов
pip list

# Проверка pyenv
pyenv versions
```

## 📁 Структура файлов

```
alex-orator-bot/
├── .python-version          # Версия Python для pyenv
├── requirements.txt         # Python зависимости
├── venv/                   # Виртуальное окружение
├── generate_keys.py        # Скрипт генерации ключей
└── PYTHON_SETUP.md         # Эта документация
```

## 🛠️ Управление зависимостями

### Добавление новой зависимости

```bash
# Установка пакета
pip install package_name

# Добавление в requirements.txt
pip freeze > requirements.txt
```

### Обновление зависимостей

```bash
# Обновление всех пакетов
pip install --upgrade -r requirements.txt

# Обновление конкретного пакета
pip install --upgrade package_name
```

## 🔒 Безопасность

### Виртуальное окружение

- ✅ Изолирует зависимости проекта
- ✅ Предотвращает конфликты версий
- ✅ Упрощает развертывание

### Версионирование

- ✅ Фиксированная версия Python (3.12.0)
- ✅ Контролируемые версии зависимостей
- ✅ Воспроизводимая среда

## 🚨 Устранение неполадок

### Ошибка "pyenv: command not found"

```bash
# Установка pyenv
brew install pyenv

# Настройка в ~/.zshrc
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - zsh)"
```

### Ошибка "Python version not found"

```bash
# Установка нужной версии
pyenv install 3.12.0

# Установка локальной версии
pyenv local 3.12.0
```

### Проблемы с виртуальным окружением

```bash
# Удаление и пересоздание
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📝 Полезные команды

```bash
# Активация окружения
source venv/bin/activate

# Деактивация
deactivate

# Проверка активного окружения
which python

# Просмотр установленных пакетов
pip list

# Экспорт зависимостей
pip freeze > requirements.txt
```

## 🔗 Связанные файлы

- **requirements.txt** - список зависимостей
- **generate_keys.py** - скрипт генерации ключей
- **.python-version** - версия Python для pyenv
- **KEYS_SETUP.md** - настройка ключей
- **SECURITY.md** - инструкции по безопасности 