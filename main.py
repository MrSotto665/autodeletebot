from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import asyncio
import os

# Load bot token and webhook URL from environment variables
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-service-name.onrender.com/webhook

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

# Function to delete messages after 2 minutes
async def delete_after_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat.id
        message_id = update.message.message_id

        await asyncio.sleep(120)  # 2 minutes

        try:
            # Check if bot has permission to delete messages
            me = await context.bot.get_chat_member(chat_id, context.bot.id)
            print(f"🤖 Bot status in chat {chat_id}: {me.status}, can_delete_messages={me.can_delete_messages}")

            if not (me.can_delete_messages or me.status == "creator"):
                print("❌ Bot lacks permission to delete messages.")
                return

            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"✅ Message {message_id} deleted.")
        except Exception as e:
            print(f"❌ Delete failed for message {message_id}: {e}")

# Register handler for all messages
bot_app.add_handler(MessageHandler(filters.ALL, delete_after_delay))

# Webhook endpoint
@app.post("/webhook")
async def telegram_webhook(req: Request):
    update = Update.de_json(await req.json(), bot_app.bot)
    if not bot_app.running:
        await bot_app.initialize()
        await bot_app.start()
    await bot_app.process_update(update)
    return {"ok": True}

# Set webhook on startup
@app.on_event("startup")
async def startup():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to: {WEBHOOK_URL}")

# Stop bot on shutdown
@app.on_event("shutdown")
async def shutdown():
    await bot_app.stop()
    await bot_app.shutdown()
