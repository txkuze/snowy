import re
import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import ChatMemberStatus, ChatPermissions
from pyrogram.errors import ChatAdminRequired

from openai import OpenAI

# ==============================
# 🔑 SET YOUR OPENAI API KEY
# ==============================

OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

client_ai = OpenAI(api_key=OPENAI_API_KEY)

# ==============================
# ⚠️ WARNING STORAGE (memory)
# ==============================

WARNINGS = {}

# ==============================
# 🔗 LINK DETECTION
# ==============================

def contains_link(text: str):
    text = text.lower()

    if re.search(r'https?://', text):
        return True

    if re.search(r'@\w{4,}', text):
        return True

    if "t.me/" in text:
        return True

    return False

# ==============================
# 🤖 AI MODERATION CHECK
# ==============================

async def ai_moderation_check(text: str):
    try:
        response = client_ai.moderations.create(
            model="omni-moderation-latest",
            input=text
        )

        result = response.results[0]

        if result.flagged:
            return True

        return False

    except Exception as e:
        print("AI Moderation Error:", e)
        return False

# ==============================
# 🛡 MAIN REGISTRATION FUNCTION
# ==============================

def register_ai_guard(app: Client):

    @app.on_message(filters.text & filters.group)
    async def ai_guard_handler(client: Client, message: Message):

        if not message.text:
            return

        user_id = message.from_user.id
        chat_id = message.chat.id

        # Skip admins & owner
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return

        violation = False

        # 🔎 Check link spam first (instant)
        if contains_link(message.text):
            violation = True

        # 🤖 AI moderation check
        if await ai_moderation_check(message.text):
            violation = True

        if not violation:
            return

        # Delete message
        try:
            await message.delete()
        except:
            pass

        # Increase warning
        WARNINGS[user_id] = WARNINGS.get(user_id, 0) + 1
        warn_count = WARNINGS[user_id]

        try:
            # 1️⃣ First offense → Warn
            if warn_count == 1:
                await message.reply_text(
                    "⚠️ Warning 1/3\nInappropriate content or spam detected."
                )

            # 2️⃣ Second offense → 10 min mute
            elif warn_count == 2:
                await client.restrict_chat_member(
                    chat_id,
                    user_id,
                    ChatPermissions(),
                    until_date=datetime.now() + timedelta(minutes=10)
                )
                await message.reply_text(
                    "🔇 Warning 2/3\nUser muted for 10 minutes."
                )

            # 3️⃣ Third offense → Ban
            else:
                await client.ban_chat_member(chat_id, user_id)
                await message.reply_text(
                    "🚫 User banned for repeated violations."
                )

        except ChatAdminRequired:
            await message.reply_text(
                "❌ I need ban & restrict permissions to take action."
              )
