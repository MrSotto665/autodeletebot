from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
group_id_env = os.getenv("GROUP_ID")
if not group_id_env:
    raise ValueError("GROUP_ID environment variable is not set.")
GROUP_ID = int(group_id_env)

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()
last_scheduled_message_id = None  # To track last periodic message

# Auto-delete user messages after ~8 minutes
async def delete_after_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat.id
        message_id = update.message.message_id
        if update.message.new_chat_members or update.message.left_chat_member:
            return
        await asyncio.sleep(500)
        try:
            me = await context.bot.get_chat_member(chat_id, context.bot.id)
            if not (me.can_delete_messages or me.status == "creator"):
                return
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(f"❌ Delete failed for message {message_id}: {e}")

bot_app.add_handler(MessageHandler(filters.ALL, delete_after_delay))

@app.post("/webhook")
async def telegram_webhook(req: Request):
    update = Update.de_json(await req.json(), bot_app.bot)
    if not bot_app.running:
        await bot_app.initialize()
        await bot_app.start()
    await bot_app.process_update(update)
    return {"ok": True}

# Send and delete group message every 5 minutes
async def periodic_message_sender():
    global last_scheduled_message_id
    await asyncio.sleep(10)
    while True:
        try:
            if last_scheduled_message_id:
                try:
                    await bot_app.bot.delete_message(chat_id=GROUP_ID, message_id=last_scheduled_message_id)
                except Exception as e:
                    print(f"⚠️ Couldn't delete last message: {e}")

            sent = await bot_app.bot.send_message(
                chat_id=GROUP_ID,
                text="Join here for dirty chats👉🏻 https://t.me/BabyMonika_Bot/RandomVideochat"
            )
            last_scheduled_message_id = sent.message_id
            print(f"📢 Sent message {sent.message_id}")
        except Exception as e:
            print(f"❌ Error sending periodic message: {e}")
        await asyncio.sleep(300)

# Proper async startup
@app.on_event("startup")
async def on_startup():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to: {WEBHOOK_URL}")
    asyncio.create_task(periodic_message_sender())

@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.stop()
    await bot_app.shutdown()
