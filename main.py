from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-service-name.onrender.com/webhook

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

# Function to delete messages after 2 minutes
async def delete_after_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat.id
        message_id = update.message.message_id

        # Skip join/leave system messages
        if update.message.new_chat_members or update.message.left_chat_member:
            print("ℹ️ Skipping system message.")
            return

        await asyncio.sleep(500)  # wait 2 minutes

        try:
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

# Telegram webhook endpoint
@app.post("/webhook")
async def telegram_webhook(req: Request):
    update = Update.de_json(await req.json(), bot_app.bot)

    if not bot_app.running:
        await bot_app.initialize()
        await bot_app.start()

    await bot_app.process_update(update)
    return {"ok": True}

# On startup: set webhook
@app.on_event("startup")
async def on_startup():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to: {WEBHOOK_URL}")

# On shutdown: clean exit
@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.stop()
    await bot_app.shutdown()
