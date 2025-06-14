import os
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import Application, AIORateLimiter

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://yourdomain.com/webhook
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # Example: '@YourChannelUsername'
CHANNEL_USERNAME1 = os.getenv("CHANNEL_USERNAME1")
MESSAGE_TEXT = "Girls and boys chat zone \nClick the link below to join the chat. 💬👇\nhttps://t.me/MakefriendsglobalBot/Letschat"

PROMO_MESSAGE = "😍Download and install this 🎥Random video chat app📱 to enjoy free video call with 100k+ Girls and boys.🫦\n⬇️Download link: https://1024terabox.com/s/1E5_FWd2ihEzDPkNBEtF_QQ"

app = FastAPI()
bot = Bot(token=TOKEN)
last_bot_message_id = None
last_promo_message_id = None

# In-memory message log (for user messages)
user_messages = []

@app.on_event("startup")
async def startup():
    await bot.set_webhook(url=WEBHOOK_URL + "/webhook")
    asyncio.create_task(bot_loop())
    asyncio.create_task(delete_old_user_messages())
    asyncio.create_task(promo_message_loop())  # New task added here

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
                if msg.text and any(link in msg.text.lower() for link in ["http://", "https://", "t.me/", "telegram.me/"]):
                    try:
                        chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=msg.from_user.id)
                        if chat_member.status not in ["administrator", "creator"]:
                            await bot.delete_message(chat_id=CHANNEL_ID, message_id=msg.message_id)
                            print(f"Link message deleted from user: {msg.message_id}")
                            return {"ok": True}
                    except TelegramError as e:
                        print(f"Error checking admin status or deleting: {e}")
                        return {"ok": True}

                try:
                    member1 = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=msg.from_user.id)
                    member2 = await bot.get_chat_member(chat_id=CHANNEL_USERNAME1, user_id=msg.from_user.id)

                    if (
                        member1.status in ["member", "administrator", "creator"] and
                        member2.status in ["member", "administrator", "creator"]
                    ):
                        user_messages.append({
                            "message_id": msg.message_id,
                            "timestamp": datetime.now(timezone.utc),
                        })
                    else:
                        raise Exception("User not joined both channels")
                except Exception as e:
                    try:
                        username = msg.from_user.username
                        if username:
                            mention = f"[@{username}](tg://user?id={msg.from_user.id})"
                        else:
                            mention = f"[User](tg://user?id={msg.from_user.id})"

                        warning_text = (
                            f"🛑 {mention}, Join our channels to chat in this group :\n"
                            f" Channel 1👉 {CHANNEL_USERNAME} \n"
                            f" Channel 2👉 {CHANNEL_USERNAME1}"
                        )

                        sent_msg = await bot.send_message(
                            chat_id=msg.chat.id,
                            reply_to_message_id=msg.message_id,
                            text=warning_text,
                            parse_mode=ParseMode.MARKDOWN_V2,
                        )
                        asyncio.create_task(delete_prompt_after_delay(sent_msg.chat_id, sent_msg.message_id))
                    except TelegramError as te:
                        print(f"Failed to send join warning: {te}")

    return {"ok": True}

async def bot_loop():
    global last_bot_message_id
    while True:
        try:
            if last_bot_message_id:
                try:
                    await bot.delete_message(chat_id=CHANNEL_ID, message_id=last_bot_message_id)
                except Exception as e:
                    print(f"Bot delete failed: {e}")

            sent = await bot.send_message(chat_id=CHANNEL_ID, text=MESSAGE_TEXT, parse_mode=ParseMode.HTML)
            last_bot_message_id = sent.message_id
            print(f"Sent bot message {last_bot_message_id}")

        except Exception as e:
            print(f"Bot loop error: {e}")

        await asyncio.sleep(300)  # 5 minutes

async def delete_old_user_messages():
    while True:
        now = datetime.now(timezone.utc)
        to_delete = [m for m in user_messages if now - m["timestamp"] > timedelta(minutes=10)]

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

# ✅ New function to send and delete promo messages every 3 minutes
async def promo_message_loop():
    global last_promo_message_id
    while True:
        try:
            if last_promo_message_id:
                try:
                    await bot.delete_message(chat_id=CHANNEL_ID, message_id=last_promo_message_id)
                except TelegramError as e:
                    print(f"Failed to delete previous promo: {e}")

            sent = await bot.send_message(chat_id=CHANNEL_ID, text=PROMO_MESSAGE)
            last_promo_message_id = sent.message_id
            print(f"Promo message sent: {last_promo_message_id}")

        except Exception as e:
            print(f"Promo loop error: {e}")

        await asyncio.sleep(180)  # 3 minutes
