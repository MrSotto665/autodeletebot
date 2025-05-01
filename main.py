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
# Function to delete messages after 10 minutes (600 seconds)
# Function to delete messages after 10 minutes
async def delete_after_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat.id
        message_id = update.message.message_id

        # Skip join/leave system messages
        if update.message.new_chat_members or update.message.left_chat_member:
            print("ℹ️ Skipping system message.")
            return

        await asyncio.sleep(10)  # wait 10 minutes

        try:
            me = await context.bot.get_chat_member(chat_id, context.bot.id)

            # Check permission safely
            can_delete = getattr(me, "can_delete_messages", False)
            if me.status == "administrator" and not can_delete:
                print("❌ Bot is admin but lacks delete permission.")
                return
            elif me.status not in ["administrator", "creator"]:
                print("❌ Bot is not admin/creator.")
                return

            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"✅ Deleted message {message_id} from chat {chat_id}")

        except Exception as e:
            error_text = str(e).lower()
            if "message to delete not found" in error_text or "message can't be deleted" in error_text:
                print(f"⚠️ Message {message_id} was already deleted or cannot be deleted.")
            else:
                print(f"❌ Unexpected error while deleting message {message_id}: {e}")



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
