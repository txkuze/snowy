import os
import re
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import ChatAdminRequired

from openai import AsyncOpenAI

# ==============================
# 🔑 OPENAI KEY
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found")

ai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ==============================
# ⚠️ WARNING STORAGE (PER GROUP)
# ==============================

WARNINGS = {}  # {(chat_id, user_id): count}

# ==============================
# 🔗 LINK DETECTION
# ==============================

def contains_link(text: str):
    text = text.lower()

    if re.search(r'https?://', text):
        return True

    if "t.me/" in text:
        return True

    if re.search(r'@\w{4,}', text):
        return True

    return False

# ==============================
# 🤖 AI MODERATION (FIXED)
# ==============================

async def ai_moderation_check(text: str):
    try:
        response = await ai_client.moderations.create(
            model="omni-moderation-latest",
            input=text
        )

        # New SDK structure
        flagged = response.results[0].flagged
        return flagged

    except Exception as e:
        print("AI Moderation Error:", e)
        return False

# ==============================
# 🛡 REGISTER FUNCTION
# ==============================

def register_ai_guard(app: Client):

    @app.on_message(filters.text & filters.group)
    async def ai_guard_handler(client: Client, message: Message):

        if not message.text or not message.from_user:
            return

        user_id = message.from_user.id
        chat_id = message.chat.id

        # Skip admins safely
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status in ["administrator", "creator"]:
                return
        except:
            return

        violation = False

        # Fast link detection
        if contains_link(message.text):
            violation = True

        # AI moderation
        if not violation:
            if await ai_moderation_check(message.text):
                violation = True

        if not violation:
            return

        # Delete message
        try:
            await client.delete_messages(chat_id, message.id)
        except Exception as e:
            print("Delete Error:", e)

        # Increase warning per group
        key = (chat_id, user_id)
        WARNINGS[key] = WARNINGS.get(key, 0) + 1
        warn_count = WARNINGS[key]

        try:
            if warn_count == 1:
                await message.reply_text(
                    "⚠️ Warning 1/3\nInappropriate content detected."
                )

            elif warn_count == 2:
                await client.restrict_chat_member(
                    chat_id,
                    user_id,
                    ChatPermissions(),
                    until_date=datetime.utcnow() + timedelta(minutes=10)
                )
                await message.reply_text(
                    "🔇 Warning 2/3\nMuted for 10 minutes."
                )

            else:
                await client.ban_chat_member(chat_id, user_id)
                await message.reply_text(
                    "🚫 User banned for repeated violations."
                )

        except ChatAdminRequired:
            await message.reply_text(
                "❌ I need admin permissions to take action."
                )
