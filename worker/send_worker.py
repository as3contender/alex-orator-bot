import asyncio
import os
from aiogram import Bot
from db import get_db_pool
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
bot = Bot(token=BOT_TOKEN)

CHECK_INTERVAL = 5  # секунд


async def process_queue():
    db = await get_db_pool()
    async with db.acquire() as conn:
        messages = await conn.fetch(
            """
            SELECT id, user_id, message
            FROM message_queue
            WHERE sent = FALSE
            ORDER BY created_at
            LIMIT 10
        """
        )

        for msg in messages:
            try:
                await bot.send_message(chat_id=msg["user_id"], text=msg["message"])
                await conn.execute(
                    """
                    UPDATE message_queue
                    SET sent = TRUE, sent_at = $2
                    WHERE id = $1
                """,
                    msg["id"],
                    datetime.now(timezone.utc),
                )
                print(f"✅ Sent message {msg['id']} to {msg['user_id']}")
            except Exception as e:
                print(f"❌ Failed to send message {msg['id']} to {msg['user_id']}: {e}")


async def run_worker():
    while True:
        try:
            await process_queue()
        except Exception as e:
            print(f"🚨 Error in worker loop: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run_worker())
