#!/usr/bin/env python3
"""
Парсер для извлечения текстов из файлов бота
"""

import re
from typing import Dict, List, Any
from loguru import logger


class ContentParser:
    def __init__(self):
        self.bot_messages = {}
        self.exercises = {}
        self.topics = {}

    def parse_bot_messages(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """Парсинг сообщений бота из файла"""
        logger.info(f"Parsing bot messages from {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {}
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {}

        # Разделяем на секции по разделителю ==========
        sections = content.split("==========")

        messages = {}
        current_key = None
        current_text = ""

        for section in sections:
            section = section.strip()
            if not section:
                continue

            lines = section.split("\n")
            if not lines:
                continue

            # Ищем заголовок (начинается с #)
            header_line = None
            for line in lines:
                if line.strip().startswith("#"):
                    header_line = line.strip()
                    break

            if header_line:
                # Если у нас есть предыдущий текст, сохраняем его
                if current_key and current_text.strip():
                    messages[current_key] = {"ru": current_text.strip()}

                # Извлекаем ключ из заголовка
                current_key = self._extract_message_key(header_line)
                current_text = ""

                # Добавляем остальные строки к тексту
                for line in lines:
                    if not line.strip().startswith("#"):
                        current_text += line + "\n"
            else:
                # Если нет заголовка, добавляем к текущему тексту
                current_text += section + "\n"

        # Сохраняем последний текст
        if current_key and current_text.strip():
            messages[current_key] = {"ru": current_text.strip()}

        logger.info(f"Parsed {len(messages)} bot messages")
        return messages

    def parse_exercises(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """Парсинг упражнений из файла"""
        logger.info(f"Parsing exercises from {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {}
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {}

        # Разделяем на секции по разделителю ==========
        sections = content.split("==========")

        exercises = {}
        topics_set = set()

        for section in sections:
            section = section.strip()
            if not section:
                continue

            lines = section.split("\n")
            if not lines:
                continue

            # Ищем заголовок (начинается с ##)
            header_line = None
            for line in lines:
                if line.strip().startswith("##"):
                    header_line = line.strip()
                    break

            if header_line:
                # Парсим заголовок: ## Речевая импровизация / Уровень 1 / Задание 1
                parts = header_line.replace("## ", "").split(" / ")
                if len(parts) >= 3:
                    topic_name = parts[0].strip()
                    level = parts[1].strip()
                    sublevel = parts[2].strip()

                    # Создаем ключ для упражнения
                    exercise_key = f"{topic_name.lower().replace(' ', '_')}_{level.lower().replace(' ', '_')}_{sublevel.lower().replace(' ', '_')}"

                    # Извлекаем текст упражнения (все после заголовка)
                    exercise_text = ""
                    header_found = False
                    for line in lines:
                        if line.strip().startswith("##"):
                            header_found = True
                            continue
                        if header_found:
                            exercise_text += line + "\n"

                    if exercise_text.strip():
                        exercises[exercise_key] = {"ru": exercise_text.strip()}

                        # Добавляем тему в список тем
                        topics_set.add(topic_name)

        # Создаем структуру тем
        self._create_topics_structure(topics_set)

        logger.info(f"Parsed {len(exercises)} exercises")
        return exercises

    def _extract_message_key(self, header_line: str) -> str:
        """Извлекает ключ сообщения из заголовка"""
        # Убираем # и номер, если есть
        header = header_line.strip()

        # Убираем номер в начале (например, "# 1. Приветственное сообщение")
        if re.match(r"^#\s*\d+\.", header):
            header = re.sub(r"^#\s*\d+\.\s*", "", header)
        else:
            # Убираем просто #
            header = header.replace("#", "").strip()

        # Преобразуем в ключ
        key = header.lower().replace(" ", "_").replace("-", "_")
        key = re.sub(r"[^\w_]", "", key)

        return key

    def _create_topics_structure(self, topics_set: set):
        """Создает структуру тем на основе найденных упражнений"""
        topics_data = []

        # Создаем группы тем
        topic_groups = {
            "Речевая импровизация": 1,
            "Четкость и плавность речи": 2,
            "Контакт с аудиторией": 3,
            "Эмоции": 4,
            "Сторителлинг": 5,
            "Структура": 6,
        }

        # Добавляем родительские темы
        for topic_name, sort_order in topic_groups.items():
            topics_data.append(
                {
                    "topic_id": topic_name.lower().replace(" ", "_"),
                    "name": topic_name,
                    "level": 1,
                    "sort_order": sort_order,
                }
            )

        # Добавляем дочерние темы (уровни)
        for topic_name in topics_set:
            parent_id = topic_name.lower().replace(" ", "_")

            # Создаем уровни для каждой темы
            for level in range(1, 4):  # Уровни 1, 2, 3
                topics_data.append(
                    {
                        "topic_id": f"{parent_id}_level{level}",
                        "name": f"{topic_name} - Уровень {level}",
                        "parent_id": parent_id,
                        "level": 2,
                        "sort_order": level,
                    }
                )

        self.topics = topics_data

    def get_bot_messages(self) -> Dict[str, Dict[str, str]]:
        """Получить сообщения бота"""
        return self.bot_messages

    def get_exercises(self) -> Dict[str, Dict[str, str]]:
        """Получить упражнения"""
        return self.exercises

    def get_topics(self) -> List[Dict[str, Any]]:
        """Получить структуру тем"""
        return self.topics

    def parse_all_content(self, bot_messages_path: str, exercises_path: str):
        """Парсинг всего контента"""
        logger.info("Starting content parsing...")

        # Парсим сообщения бота
        self.bot_messages = self.parse_bot_messages(bot_messages_path)

        # Парсим упражнения
        self.exercises = self.parse_exercises(exercises_path)

        logger.info(
            f"Parsing completed: {len(self.bot_messages)} messages, {len(self.exercises)} exercises, {len(self.topics)} topics"
        )

        return {"messages": self.bot_messages, "exercises": self.exercises, "topics": self.topics}


def main():
    """Тестирование парсера"""
    parser = ContentParser()

    # Пути к файлам
    bot_messages_path = "backend/texts/bot_messages.txt"
    exercises_path = "backend/texts/exercises.txt"

    # Парсим контент
    content = parser.parse_all_content(bot_messages_path, exercises_path)

    # Выводим результаты
    print("=== BOT MESSAGES ===")
    for key, value in content["messages"].items():
        print(f"{key}: {value['ru'][:100]}...")

    print("\n=== EXERCISES ===")
    for key, value in content["exercises"].items():
        print(f"{key}: {value['ru'][:100]}...")

    print("\n=== TOPICS ===")
    for topic in content["topics"]:
        print(f"{topic['name']} (level {topic['level']})")


if __name__ == "__main__":
    main()
