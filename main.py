import os
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from telegram.error import TelegramError
from telegram.ext import Application, AIORateLimiter

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://yourdomain.com/webhook

MESSAGE_TEXT = "Use this dirty chats👉🏻 https://t.me/BabyMonika_Bot/RandomVideochat"

app = FastAPI()
bot = Bot(token=TOKEN)
last_bot_message_id = None

# In-memory message log (for user messages)
user_messages = []

@app.on_event("startup")
async def startup():
    await bot.set_webhook(url=WEBHOOK_URL + "/webhook")
    asyncio.create_task(bot_loop())
    asyncio.create_task(delete_old_user_messages())

@app.get("/")
async def root():
    return {"status": "Bot running."}

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)

    if update.message:
        msg = update.message
        if msg.chat.id == CHANNEL_ID:
            if not msg.from_user.is_bot:
                # Save user message for later deletion
                user_messages.append({
                    "message_id": msg.message_id,
                    "timestamp": datetime.now(timezone.utc),
                })

    return {"ok": True}

async def bot_loop():
    global last_bot_message_id
    while True:
        try:
            # Delete old bot message
            if last_bot_message_id:
                try:
                    await bot.delete_message(chat_id=CHANNEL_ID, message_id=last_bot_message_id)
                except Exception as e:
                    print(f"Bot delete failed: {e}")

            # Send new message
            sent = await bot.send_message(chat_id=CHANNEL_ID, text=MESSAGE_TEXT, parse_mode=ParseMode.HTML)
            last_bot_message_id = sent.message_id
            print(f"Sent bot message {last_bot_message_id}")

        except Exception as e:
            print(f"Bot loop error: {e}")

        await asyncio.sleep(300)  # 5 minutes

async def delete_old_user_messages():
    while True:
        now = datetime.now(timezone.utc)
        to_delete = [m for m in user_messages if now - m["timestamp"] > timedelta(minutes=3)]

        for m in to_delete:
            try:
                await bot.delete_message(chat_id=CHANNEL_ID, message_id=m["message_id"])
                print(f"Deleted user message {m['message_id']}")
                user_messages.remove(m)
            except TelegramError as e:
                print(f"User delete failed: {e}")

        await asyncio.sleep(30)  # Check every 30 seconds

