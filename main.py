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
async def delete_after_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat.id
        message_id = update.message.message_id

        # Skip system messages
        if update.message.new_chat_members or update.message.left_chat_member:
            print("ℹ️ Skipping system message.")
            return

        await asyncio.sleep(600)  # wait 10 minutes

        try:
            me = await context.bot.get_chat_member(chat_id, context.bot.id)

            if me.status == "administrator":
                if not me.can_delete_messages:
                    print("❌ Bot is admin but can't delete messages.")
                    return
            elif me.status != "creator":
                print("❌ Bot is not admin or creator, can't delete messages.")
                return

            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"✅ Deleted message {message_id} from chat {chat_id}")

        except Exception as e:
            if "message to delete not found" in str(e).lower():
                print(f"⚠️ Message {message_id} was already deleted manually.")
            else:
                print(f"❌ Unexpected error deleting message {message_id}: {e}")



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
