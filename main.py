import asyncio
import os
from fastapi import FastAPI
from telegram import Bot
from telegram.constants import ParseMode
import uvicorn

# Get credentials from environment variables
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
MESSAGE_TEXT = "👆"

# Type check for CHANNEL_ID (as env var comes as string)
try:
    CHANNEL_ID = int(CHANNEL_ID)
except Exception as e:
    print(f"Invalid CHANNEL_ID: {CHANNEL_ID}. Make sure it's a valid Telegram channel ID (e.g. -1001234567890)")

app = FastAPI()
bot = Bot(token=TOKEN)
last_message_id = None

@app.get("/")
async def root():
    return {"status": "Bot is running."}


async def bot_loop():
    global last_message_id
    while True:
        try:
            # Delete old message if exists
            if last_message_id:
                try:
                    await bot.delete_message(chat_id=CHANNEL_ID, message_id=last_message_id)
                except Exception as delete_err:
                    print(f"Delete failed: {delete_err}")

            # Send new message
            sent = await bot.send_message(chat_id=CHANNEL_ID, text=MESSAGE_TEXT, parse_mode=ParseMode.HTML)
            last_message_id = sent.message_id
            print(f"Sent message ID: {last_message_id}")

        except Exception as e:
            print(f"Bot error: {e}")

        await asyncio.sleep(1800)  # 30 minutes


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(bot_loop())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
