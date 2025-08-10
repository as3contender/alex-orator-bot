# send_worker.py (переписанный, с корректным graceful shutdown)
# ------------------------------------------------------------
import os
import signal
import asyncio
import contextlib
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

from db import get_db_pool, close_db_pool  # используем твои функции из db.py

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHECK_INTERVAL = int(os.getenv("WORKER_CHECK_INTERVAL", "2"))  # сек
BATCH_SIZE = int(os.getenv("WORKER_BATCH_SIZE", "50"))
CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "10"))
DRAIN_TIMEOUT = int(os.getenv("WORKER_DRAIN_TIMEOUT", "30"))


async def fetch_batch(conn):
    """Забираем пачку сообщений, блокируя их от конкурентных воркеров."""
    rows = await conn.fetch(
        """
        WITH cte AS (
            SELECT id
            FROM message_queue
            WHERE sent = FALSE
            ORDER BY created_at
            FOR UPDATE SKIP LOCKED
            LIMIT $1
        )
        SELECT mq.id, mq.user_id, mq.message, mq.keyboard
        FROM message_queue mq
        JOIN cte ON mq.id = cte.id;
        """,
        BATCH_SIZE,
    )
    return rows


async def mark_sent(conn, msg_id):
    await conn.execute(
        """
        UPDATE message_queue
        SET sent = TRUE, sent_at = NOW()
        WHERE id = $1
        """,
        msg_id,
    )


async def send_one(bot: Bot, pool, row, sem: asyncio.Semaphore):
    """Отправляем одно сообщение с ограничением по параллелизму."""
    import json

    async with sem:
        try:
            keyboard = row["keyboard"]
            if keyboard:
                # Десериализуем JSON строку обратно в словарь
                keyboard_dict = json.loads(keyboard) if isinstance(keyboard, str) else keyboard

                # Создаем клавиатуру правильно для aiogram
                keyboard_buttons = []
                for row_buttons in keyboard_dict.get("inline_keyboard", []):
                    button_row = []
                    for button_data in row_buttons:
                        # Поддерживаем как callback_data, так и url
                        if "callback_data" in button_data:
                            button = InlineKeyboardButton(
                                text=button_data["text"], callback_data=button_data["callback_data"]
                            )
                        elif "url" in button_data:
                            button = InlineKeyboardButton(text=button_data["text"], url=button_data["url"])
                        else:
                            # Пропускаем кнопки без callback_data или url
                            continue
                        button_row.append(button)
                    keyboard_buttons.append(button_row)

                reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
                await bot.send_message(
                    chat_id=row["user_id"], text=row["message"], reply_markup=reply_markup, parse_mode="HTML"
                )
            else:
                await bot.send_message(chat_id=row["user_id"], text=row["message"], parse_mode="HTML")
            async with pool.acquire() as conn:
                await mark_sent(conn, row["id"])  # фиксируем доставку
            print(f"✅ sent id={row['id']} user={row['user_id']}")
        except Exception as e:  # noqa: BLE001 — логируем и живём дальше
            # TODO: можно добавить retry/backoff + таблицу для ошибок
            print(f"❌ send failed id={row['id']} user={row['user_id']}: {e}")


async def run_worker(stop_event: asyncio.Event):
    pool = await get_db_pool()  # твой пул из db.py
    bot = Bot(token=BOT_TOKEN)
    sem = asyncio.Semaphore(CONCURRENCY)

    try:
        while not stop_event.is_set():
            async with pool.acquire() as conn:
                rows = await fetch_batch(conn)

            if not rows:
                # ждём либо сигнал, либо таймаут
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=CHECK_INTERVAL)
                except asyncio.TimeoutError:
                    pass
                continue

            # Отправляем текущую пачку параллельно и дожидаемся завершения
            async with asyncio.TaskGroup() as tg:
                for row in rows:
                    tg.create_task(send_one(bot, pool, row, sem))

        # пришёл стоп-сигнал — дренаж не обязателен, TaskGroup дожидается

    finally:
        # Дадим время корректно доработать оставшиеся задачи (страховка)
        pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if pending:
            print(f"⏳ draining {len(pending)} tasks up to {DRAIN_TIMEOUT}s...")
            with contextlib.suppress(Exception):
                await asyncio.wait(pending, timeout=DRAIN_TIMEOUT)

        # Закрываем ресурсы
        with contextlib.suppress(Exception):
            await bot.session.close()
        with contextlib.suppress(Exception):
            await close_db_pool()
        print("✅ graceful shutdown complete")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN должен быть задан в переменных окружения")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    await run_worker(stop_event)


if __name__ == "__main__":
    asyncio.run(main())
