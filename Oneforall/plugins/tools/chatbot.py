import os
from pyrogram import Client, filters
from pyrogram.types import Message
from openai import AsyncOpenAI

# ==========================
# 🔑 OPENAI SETUP
# ==========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing")

ai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ==========================
# 📊 STORAGE
# ==========================

CHATBOT_STATUS = {}        # {chat_id: True/False}
USER_MEMORY = {}           # {(chat_id, user_id): [messages]}
MAX_MEMORY = 6


# ==========================
# 🛠 ADMIN CHECK
# ==========================

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False


# ==========================
# 🎵 VC CONTROL HANDLER
# ==========================

async def handle_vc_command(message: Message, ai_text: str):
    text = ai_text.lower()

    # PLAY
    if text.startswith("play:"):
        query = text.replace("play:", "").strip()
        await message.reply_text(f"🎵 Playing: {query}")
        # 👉 connect this to your existing /play logic
        return True

    # PAUSE
    if "pause music" in text:
        await message.reply_text("⏸ Pausing music...")
        return True

    # RESUME
    if "resume music" in text:
        await message.reply_text("▶️ Resuming music...")
        return True

    # SKIP
    if "skip music" in text:
        await message.reply_text("⏭ Skipping track...")
        return True

    # STOP
    if "stop music" in text:
        await message.reply_text("⏹ Stopping music...")
        return True

    return False


# ==========================
# 🤖 REGISTER FUNCTION
# ==========================

def register_chatbot(app: Client):

    # --------------------------
    # 🔘 TOGGLE COMMAND
    # --------------------------
    @app.on_message(filters.command("chatbot") & filters.group)
    async def toggle_chatbot(client: Client, message: Message):

        chat_id = message.chat.id
        user_id = message.from_user.id

        if not await is_admin(client, chat_id, user_id):
            return await message.reply_text("❌ Admin only command.")

        # If no argument → show status
        if len(message.command) < 2:
            status = CHATBOT_STATUS.get(chat_id, False)
            return await message.reply_text(
                f"🤖 Chatbot status: {'ON' if status else 'OFF'}"
            )

        arg = message.command[1].lower()

        if arg in ["on", "enable"]:
            CHATBOT_STATUS[chat_id] = True
            return await message.reply_text(
                "🤖 Hello! I'm Snowy chatbot integrated with music features 🎵"
            )

        elif arg in ["off", "disable"]:
            CHATBOT_STATUS[chat_id] = False
            return await message.reply_text(
                "✅ Ok switching off chatbot mode."
            )

        else:
            return await message.reply_text(
                "Usage:\n/chatbot on\n/chatbot off"
            )

    # --------------------------
    # 💬 MAIN AI HANDLER
    # --------------------------
    @app.on_message(filters.text & filters.group)
    async def ai_handler(client: Client, message: Message):

        chat_id = message.chat.id
        user_id = message.from_user.id

        if not CHATBOT_STATUS.get(chat_id, False):
            return

        text = message.text.lower()

        trigger_words = ["snowy", "music", "hi", "hello"]

        if not any(word in text for word in trigger_words):
            return

        key = (chat_id, user_id)

        if key not in USER_MEMORY:
            USER_MEMORY[key] = []

        USER_MEMORY[key].append({"role": "user", "content": message.text})
        USER_MEMORY[key] = USER_MEMORY[key][-MAX_MEMORY:]

        try:
            response = await ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are Snowy, a Telegram music AI assistant.\n"
                            "If user asks for music recommendation, suggest 3 songs.\n"
                            "If user wants to control VC, respond STRICTLY like:\n"
                            "play: song name\n"
                            "pause music\n"
                            "resume music\n"
                            "skip music\n"
                            "stop music\n"
                            "Otherwise reply short and friendly."
                        )
                    }
                ] + USER_MEMORY[key],
                max_tokens=200
            )

            ai_reply = response.choices[0].message.content

            USER_MEMORY[key].append({"role": "assistant", "content": ai_reply})
            USER_MEMORY[key] = USER_MEMORY[key][-MAX_MEMORY:]

            vc_used = await handle_vc_command(message, ai_reply)

            if not vc_used:
                await message.reply_text(ai_reply)

        except Exception as e:
            print("AI Error:", e)
            await message.reply_text("⚠️ AI error occurred.")
