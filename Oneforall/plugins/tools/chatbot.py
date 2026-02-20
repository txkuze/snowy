import os
from pyrogram import Client, filters
from pyrogram.types import Message
from openai import AsyncOpenAI

# ==========================
# 🔑 OPENAI SETUP
# ==========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Backup: Agar environment variable nahi milta
    OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE" 

ai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ==========================
# 📊 STORAGE
# ==========================

CHATBOT_STATUS = {}        # {chat_id: True/False}
USER_MEMORY = {}           # {(chat_id, user_id): [messages]}
MAX_MEMORY = 10            # Memory thodi badha di hai for better context


# ==========================
# 🛠 ADMIN CHECK
# ==========================

async def is_admin(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception:
        return False


# ==========================
# 🎵 VC CONTROL HANDLER
# ==========================

async def handle_vc_command(message: Message, ai_text: str):
    text = ai_text.lower().strip()

    # PLAY logic
    if text.startswith("play:"):
        query = text.replace("play:", "").strip()
        await message.reply_text(f"🎵 **Playing:** `{query}`")
        # Yahan aap apna music player function call kar sakte hain
        return True

    # Control Commands
    controls = {
        "pause music": ("⏸ **Pausing music...**", "pause"),
        "resume music": ("▶️ **Resuming music...**", "resume"),
        "skip music": ("⏭ **Skipping track...**", "skip"),
        "stop music": ("⏹ **Stopping music...**", "stop")
    }

    for key, (reply, cmd) in controls.items():
        if key in text:
            await message.reply_text(reply)
            # Yahan command execute karein: await music_cmd(cmd)
            return True

    return False


# ==========================
# 🤖 REGISTER FUNCTION
# ==========================

def register_chatbot(app: Client):

    # 🔘 TOGGLE COMMAND
    @app.on_message(filters.command("chatbot") & filters.group)
    async def toggle_chatbot(client: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        if not await is_admin(client, chat_id, user_id):
            return await message.reply_text("❌ Sirf Admins hi ise control kar sakte hain.")

        if len(message.command) < 2:
            status = CHATBOT_STATUS.get(chat_id, False)
            return await message.reply_text(f"🤖 **Status:** {'Salu (ON)' if status else 'Band (OFF)'}\n\nUse: `/chatbot on` ya `/chatbot off`")

        arg = message.command[1].lower()

        if arg in ["on", "enable", "true"]:
            CHATBOT_STATUS[chat_id] = True
            await message.reply_text("🤖 **Snowy AI Chatbot Active!**\nAb aap mujhse baat kar sakte hain ya music control karwa sakte hain.")
        elif arg in ["off", "disable", "false"]:
            CHATBOT_STATUS[chat_id] = False
            await message.reply_text("✅ **Chatbot band kar diya gaya hai.**")
        else:
            await message.reply_text("Usage: `/chatbot on` or `/chatbot off`")

    # 💬 MAIN AI HANDLER
    @app.on_message(filters.text & filters.group & ~filters.bot)
    async def ai_handler(client: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Status Check
        if not CHATBOT_STATUS.get(chat_id, False):
            return

        # Filters: Sirf reply hone par ya trigger words par chale (taki spam na ho)
        text = message.text.lower()
        is_reply_to_me = message.reply_to_message and message.reply_to_message.from_user.id == (await client.get_me()).id
        trigger_words = ["snowy", "music", "play", "bot", "assistant"]
        
        if not (any(word in text for word in trigger_words) or is_reply_to_me):
            return

        # Memory Management
        key = (chat_id, user_id)
        if key not in USER_MEMORY:
            USER_MEMORY[key] = []

        # Prompt setup
        system_prompt = {
            "role": "system",
            "content": (
                "You are Snowy, a helpful Telegram music AI. "
                "Keep responses short and cool. "
                "For music controls, use EXACTLY these formats:\n"
                "play: song name\n"
                "pause music\n"
                "resume music\n"
                "skip music\n"
                "stop music\n"
                "If not a control command, just chat normally."
            )
        }

        # Add user message to history
        USER_MEMORY[key].append({"role": "user", "content": message.text})
        
        # Keep only last N messages for context
        history = USER_MEMORY[key][-MAX_MEMORY:]

        try:
            # AI request
            response = await ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[system_prompt] + history,
                max_tokens=250
            )

            ai_reply = response.choices[0].message.content
            
            # Save AI response to memory
            USER_MEMORY[key].append({"role": "assistant", "content": ai_reply})

            # Check for VC Commands
            vc_executed = await handle_vc_command(message, ai_reply)

            if not vc_executed:
                await message.reply_text(ai_reply)

        except Exception as e:
            print(f"AI Error: {e}")
            # Silent fail for better UX, or uncomment below:
            # await message.reply_text("⚠️ Kuch technical issue hai, baad mein try karein.")

