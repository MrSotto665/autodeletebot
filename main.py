from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-service-name.onrender.com/webhook
GROUP_ID = int(os.getenv("GROUP_ID"))   # Telegram group ID (e.g. -1001234567890)

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

last_scheduled_message_id = None  # Will store the ID of the last scheduled message

# Function to auto-delete user messages after 8 minutes
async def delete_after_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat.id
        message_id = update.message.message_id

        # Skip system messages
        if update.message.new_chat_members or update.message.left_chat_member:
            print("ℹ️ Skipping system message.")
            return

        await asyncio.sleep(500)  # ~8 min delay

        try:
            me = await context.bot.get_chat_member(chat_id, context.bot.id)
            if not (me.can_delete_messages or me.status == "creator"):
                print("❌ Bot can't delete messages.")
                return
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"✅ Message {message_id} deleted.")
        except Exception as e:
            print(f"❌ Delete failed for message {message_id}: {e}")

# Register handler for all messages
bot_app.add_handler(MessageHandler(filters.ALL, delete_after_delay))

# Webhook for Telegram
@app.post("/webhook")
async def telegram_webhook(req: Request):
    update = Update.de_json(await req.json(), bot_app.bot)
    if not bot_app.running:
        await bot_app.initialize()
        await bot_app.start()
    await bot_app.process_update(update)
    return {"ok": True}

# Background task to send and manage periodic group messages
async def periodic_message_sender():
    global last_scheduled_message_id
    await asyncio.sleep(10)  # Small delay to ensure everything is ready

    while True:
        try:
            # Delete previous message
            if last_scheduled_message_id:
                try:
                    await bot_app.bot.delete_message(chat_id=GROUP_ID, message_id=last_scheduled_message_id)
                    print(f"🗑️ Deleted previous periodic message {last_scheduled_message_id}")
                except Exception as e:
                    print(f"⚠️ Failed to delete previous periodic message: {e}")

            # Send new message
            sent = await bot_app.bot.send_message(chat_id=GROUP_ID, text="Join here for dirty chats👉🏻 https://t.me/BabyMonika_Bot/RandomVideochat ")
            last_scheduled_message_id = sent.message_id
            print(f"📢 Sent periodic message: {sent.message_id}")

        except Exception as e:
            print(f"❌ Failed in periodic sender: {e}")

        await asyncio.sleep(300)  # Wait 5 minutes

# Startup and shutdown handlers
@app.on_event("startup")
async def on_startup():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to: {WEBHOOK_URL}")
    asyncio.create_task(periodic_message_sender())  # Start periodic message task

@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.stop()
    await bot_app.shutdown()
