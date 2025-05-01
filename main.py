from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-service-name.onrender.com/webhook

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

# Delete message after 2 minutes
async def delete_after_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat.id
        message_id = update.message.message_id

        await asyncio.sleep(120)  # 2 minutes
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        except Exception as e:
            print(f"Delete failed: {e}")

# Register handler
bot_app.add_handler(MessageHandler(filters.ALL, delete_after_delay))

# Webhook endpoint for Telegram
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

# Startup: initialize app and set webhook
@app.on_event("startup")
async def setup_webhook():
    print(f"Setting webhook: {WEBHOOK_URL}")
    await bot_app.initialize()
    await bot_app.bot.set_webhook(WEBHOOK_URL)
    await bot_app.start()

# Shutdown: clean exit
@app.on_event("shutdown")
async def shutdown():
    await bot_app.stop()
    await bot_app.shutdown()
