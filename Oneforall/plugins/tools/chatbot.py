import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from openai import AsyncOpenAI

# ==========================
# 🔑 HEROKU ENV VARIABLES
# ==========================

API_ID = int(os.environ.get("API_ID"))  # Heroku Config Vars se lega
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Fallback for local testing (optional)
if not API_ID:
    API_ID = int(os.environ.get("12345678", "12345678"))
if not API_HASH:
    API_HASH = os.environ.get("API_HASH", "your_hash_here")
if not BOT_TOKEN:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token")
if not OPENAI_API_KEY:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-your-key")

ai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ==========================
# 📊 STORAGE
# ==========================

CHATBOT_STATUS = {}
USER_MEMORY = {}
MAX_MEMORY = 10

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
    text = ai_text.lower().strip()

    if text.startswith("play:"):
        query = text.replace("play:", "").strip()
        await message.reply_text(f"🎵 **Playing:** `{query}`")
        return True

    controls = {
        "pause music": ("⏸ Pausing music...", "pause"),
        "resume music": ("▶️ Resuming music...", "resume"),
        "skip music": ("⏭ Skipping track...", "skip"),
        "stop music": ("⏹ Stopping music...", "stop")
    }

    for key, (reply, cmd) in controls.items():
        if key in text:
            await message.reply_text(reply)
            return True

    return False

# ==========================
# 🤖 MAIN BOT
# ==========================

app = Client("snowy_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==========================
# 👋 START COMMAND
# ==========================

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 **Hello! I'm Snowy AI Bot!**\n\n"
        "I can help you with:\n"
        "• AI Chat\n"
        "• Music Control\n\n"
        "Add me to a group and make me admin to use chatbot features!"
    )

# ==========================
# 📌 CHATBOT TOGGLE COMMAND
# ==========================

@app.on_message(filters.command("chatbot"))
async def toggle_chatbot(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if group
    if message.chat.type == "private":
        return await message.reply_text(
            "❌ Ye command sirf groups mein kaam karta hai!\n\n"
            "Group mein add karein aur admin banayein."
        )

    # Admin check
    if not await is_admin(client, chat_id, user_id):
        return await message.reply_text("❌ Sirf Admins hi ise control kar sakte hain.")

    # Get command arguments
    if len(message.command) < 2:
        status = CHATBOT_STATUS.get(chat_id, False)
        status_text = "✅ Active" if status else "❌ Inactive"
        return await message.reply_text(
            f"🤖 **Chatbot Status:** {status_text}\n\n"
            "**Commands:**\n"
            "• `/chatbot enable` - Bot chalana\n"
            "• `/chatbot disable` - Bot band karna"
        )

    arg = message.command[1].lower()

    if arg in ["enable", "on", "start"]:
        CHATBOT_STATUS[chat_id] = True
        await message.reply_text("✅ **Chatbot enable kar diya gaya!**")
        
    elif arg in ["disable", "off", "stop"]:
        CHATBOT_STATUS[chat_id] = False
        await message.reply_text("✅ **Chatbot disable kar diya gaya!**")
        
    else:
        await message.reply_text("❓ Use `/chatbot enable` or `/chatbot disable`")

# ==========================
# 💬 MAIN AI HANDLER
# ==========================

@app.on_message(filters.text & ~filters.bot)
async def ai_handler(client: Client, message: Message):
    # Skip if private
    if message.chat.type == "private":
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Check if chatbot enabled
    if not CHATBOT_STATUS.get(chat_id, False):
        return

    text = message.text.lower()
    
    # Check reply to bot
    bot_user = await client.get_me()
    is_reply_to_me = False
    if message.reply_to_message:
        is_reply_to_me = message.reply_to_message.from_user.id == bot_user.id
    
    # Trigger words
    trigger_words = ["snowy", "music", "play", "bot", "assistant", "song", "hey"]
    
    if not (any(word in text for word in trigger_words) or is_reply_to_me):
        return

    await message.reply_chat_action("typing")

    # Memory
    key = (chat_id, user_id)
    if key not in USER_MEMORY:
        USER_MEMORY[key] = []

    system_prompt = {
        "role": "system",
        "content": (
            "You are Snowy, a helpful Telegram music AI assistant. "
            "Keep responses short and friendly. "
            "For music controls, reply with EXACTLY these formats:\n"
            "play: song name\n"
            "pause music\n"
            "resume music\n"
            "skip music\n"
            "stop music\n"
            "Otherwise, just chat normally."
        )
    }

    USER_MEMORY[key].append({"role": "user", "content": message.text})
    history = USER_MEMORY[key][-MAX_MEMORY:]

    try:
        response = await ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[system_prompt] + history,
            max_tokens=200
        )

        ai_reply = response.choices[0].message.content
        
        USER_MEMORY[key].append({"role": "assistant", "content": ai_reply})

        vc_executed = await handle_vc_command(message, ai_reply)

        if not vc_executed:
            await message.reply_text(ai_reply)

    except Exception as e:
        print(f"❌ Error: {e}")
        await message.reply_text("⚠️ Kuch issue ho gaya, baad mein try karein.")

# ==========================
# 🚀 START
# ==========================

async def main():
    print("🤖 Snowy Bot Running on Heroku...")
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
