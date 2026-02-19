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

def register_badwords_guard(app: Client):

    # --------------------------
    # /free command
    # --------------------------
    @app.on_message(filters.command("free") & filters.group)
    async def free_user(client: Client, message: Message):

        if not await is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ Admin only command.")

        if not message.reply_to_message:
            return await message.reply_text("Reply to a user to free them.")

        target_id = message.reply_to_message.from_user.id
        chat_id = message.chat.id

        FREE_USERS.setdefault(chat_id, set()).add(target_id)

        await message.reply_text("✅ User is now exempt from bad word filter.")


    # --------------------------
    # /unfree command
    # --------------------------
    @app.on_message(filters.command("unfree") & filters.group)
    async def unfree_user(client: Client, message: Message):

        if not await is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ Admin only command.")

        if not message.reply_to_message:
            return await message.reply_text("Reply to a user to remove exemption.")

        target_id = message.reply_to_message.from_user.id
        chat_id = message.chat.id

        if chat_id in FREE_USERS:
            FREE_USERS[chat_id].discard(target_id)

        await message.reply_text("🚫 User is no longer exempt.")


    # --------------------------
    # MAIN FILTER
    # --------------------------
    @app.on_message(filters.text & filters.group)
    async def badword_handler(client: Client, message: Message):

        if not message.text or not message.from_user:
            return

        chat_id = message.chat.id
        user_id = message.from_user.id

        # Skip admins
        if await is_admin(client, chat_id, user_id):
            return

        # Skip freed users
        if user_id in FREE_USERS.get(chat_id, set()):
            return

        # Check bad words
        if not contains_bad_word(message.text):
            return

        # Delete message
        try:
            await client.delete_messages(chat_id, message.id)
        except Exception as e:
            print("Delete Error:", e)

        # Warning system
        key = (chat_id, user_id)
        WARNINGS[key] = WARNINGS.get(key, 0) + 1
        warn_count = WARNINGS[key]

        try:
            if warn_count == 1:
                await message.reply_text(
                    "⚠️ Warning 1/3\nAbusive language detected."
                )

            elif warn_count == 2:
                await client.restrict_chat_member(
                    chat_id,
                    user_id,
                    ChatPermissions(),
                    until_date=datetime.utcnow() + timedelta(minutes=15)
                )
                await message.reply_text(
                    "🔇 Warning 2/3\nMuted for 15 minutes."
                )

            else:
                await client.ban_chat_member(chat_id, user_id)
                await message.reply_text(
                    "🚫 User banned for repeated abusive behavior."
                )

        except ChatAdminRequired:
            await message.reply_text(
                "❌ I need admin permissions to take action."
            )
