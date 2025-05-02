import os
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.helpers import escape\_markdown
from telegram.error import TelegramError
from telegram.ext import Application, AIORateLimiter

TOKEN = os.getenv("BOT\_TOKEN")
CHANNEL\_ID = int(os.getenv("CHANNEL\_ID"))
WEBHOOK\_URL = os.getenv("WEBHOOK\_URL")  # Example: [https://yourdomain.com/webhook](https://yourdomain.com/webhook)

MESSAGE\_TEXT = "Use this dirty chats👉🏻 [https://t.me/BabyMonika\_Bot/RandomVideochat](https://t.me/BabyMonika_Bot/RandomVideochat)"

app = FastAPI()
bot = Bot(token=TOKEN)
last\_bot\_message\_id = None

# In-memory message log (for user messages)

user\_messages = \[]

@app.on\_event("startup")
async def startup():
await bot.set\_webhook(url=WEBHOOK\_URL + "/webhook")
asyncio.create\_task(bot\_loop())
asyncio.create\_task(delete\_old\_user\_messages())

@app.get("/")
async def root():
return {"status": "Bot running."}

@app.post("/webhook")
async def webhook\_handler(request: Request):
data = await request.json()
update = Update.de\_json(data, bot)

```
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
```

async def bot\_loop():
global last\_bot\_message\_id
while True:
try:
\# Delete old bot message
if last\_bot\_message\_id:
try:
await bot.delete\_message(chat\_id=CHANNEL\_ID, message\_id=last\_bot\_message\_id)
except Exception as e:
print(f"Bot delete failed: {e}")

```
        # Send new message
        sent = await bot.send_message(chat_id=CHANNEL_ID, text=MESSAGE_TEXT, parse_mode=ParseMode.HTML)
        last_bot_message_id = sent.message_id
        print(f"Sent bot message {last_bot_message_id}")

    except Exception as e:
        print(f"Bot loop error: {e}")

    await asyncio.sleep(300)  # 5 minutes
```

async def delete\_old\_user\_messages():
while True:
now = datetime.now(timezone.utc)
to\_delete = \[m for m in user\_messages if now - m\["timestamp"] > timedelta(minutes=3)]

```
    for m in to_delete:
        try:
            await bot.delete_message(chat_id=CHANNEL_ID, message_id=m["message_id"])
            print(f"Deleted user message {m['message_id']}")
            user_messages.remove(m)
        except TelegramError as e:
            print(f"User delete failed: {e}")

    await asyncio.sleep(30)
```
