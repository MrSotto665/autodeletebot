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
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # Example: '@YourChannelUsername'

MESSAGE_TEXT = "Daily new members added in this chat zone👉🏻 https://t.me/MakefriendsglobalBot/Letschat"

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
                try:
                    member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=msg.from_user.id)
                    if member.status in ["member", "administrator", "creator"]:
                        user_messages.append({
                            "message_id": msg.message_id,
                            "timestamp": datetime.now(timezone.utc),
                        })
                    else:
                        raise Exception("Not a member")
                except Exception as e:
                    try:
                        await bot.delete_message(chat_id=CHANNEL_ID, message_id=msg.message_id)
                    except TelegramError as te:
                        print(f"Failed to delete message: {te}")
                    try:
                        sent_msg = await bot.send_message(
                            chat_id=msg.chat.id,
                            text=f"🛑 To chat here Please join our channel first :\n👉 {CHANNEL_USERNAME}",
                        )
                        asyncio.create_task(delete_prompt_after_delay(sent_msg.chat_id, sent_msg.message_id))
                    except TelegramError as te:
                        print(f"Failed to send join message: {te}")

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
        to_delete = [m for m in user_messages if now - m["timestamp"] > timedelta(minutes=60)]

        for m in to_delete:
            try:
                await bot.delete_message(chat_id=CHANNEL_ID, message_id=m["message_id"])
                print(f"Deleted user message {m['message_id']}")
                user_messages.remove(m)
            except TelegramError as e:
                print(f"User delete failed: {e}")

        await asyncio.sleep(30)

async def delete_prompt_after_delay(chat_id, message_id):
    await asyncio.sleep(30)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramError as e:
        print(f"Failed to delete prompt message: {e}")

