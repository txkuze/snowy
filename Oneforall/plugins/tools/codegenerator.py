import os
import re
import time
import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# ==========================================
# CONFIGURATION (Fetching from Heroku Vars)
# ==========================================

# Pyrogram Credentials
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Black Box API Configuration
BLACKBOX_API_URL = os.environ.get("BLACKBOX_API_URL", "https://api.blackbox.ai/v1/chat/completions")
BLACKBOX_API_KEY = os.environ.get("BLACKBOX_API_KEY")
BLACKBOX_MODEL = os.environ.get("BLACKBOX_MODEL", "gpt-3.5-turbo")

# Check if essential variables are missing
if not all([API_ID, API_HASH, BOT_TOKEN, BLACKBOX_API_KEY]):
    print("❌ Error: Please set API_ID, API_HASH, BOT_TOKEN, and BLACKBOX_API_KEY in Heroku Config Vars.")
    exit()

# Supported Languages Map
LANGUAGES = {
    "py": "python",
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "html": "html",
    "css": "css",
    "c": "c",
    "c++": "cpp",
    "cpp": "cpp",
    "java": "java",
    "go": "go",
    "rust": "rust",
    "sql": "sql",
    "php": "php"
}

# ==========================================
# BOT CLIENT
# ==========================================

app = Client(
    "code_generator_bot",
    api_id=int(API_ID),  # Convert to integer as required by Pyrogram
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_code_from_blackbox(language: str, prompt: str) -> str:
    """
    Calls the Black Box API to generate code.
    """
    full_prompt = f"Write a {language} code for: {prompt}. Only provide the code, no explanations."

    payload = {
        "model": BLACKBOX_MODEL,
        "messages": [
            {"role": "user", "content": full_prompt}
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BLACKBOX_API_KEY}"
    }

    try:
        response = requests.post(BLACKBOX_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        else:
            return str(data)

    except Exception as e:
        print(f"API Error: {e}")
        return f"Error: {str(e)}"

# ==========================================
# MESSAGE HANDLER
# ==========================================

@app.on_message(filters.command("code") & (filters.private | filters.group))
async def handle_code_generation(client: Client, message: Message):
    """
    Handles /codepy, /codejs, etc., commands.
    Works in both Private Messages and Groups.
    """
    
    # 1. Parse the command
    command_parts = message.text.split(" ", 2)
    
    if len(command_parts) < 2:
        await message.reply(
            "❌ **Invalid Format!**\n\n"
            "Use: `/codepy <prompt>`\n"
            "Example: `/codepy create a hello world function`\n\n"
            "**Supported Languages:** py, js, html, c++, java, go, rust, sql, php"
        )
        return

    # Get the command trigger (e.g., "codepy")
    cmd_trigger = message.command[0]
    
    # Extract language suffix
    if not cmd_trigger.startswith("code"):
        return
    
    lang_key = cmd_trigger.replace("code", "")
    
    if lang_key not in LANGUAGES:
        await message.reply(f"❌ Language `{lang_key}` is not supported.")
        return

    # Get the prompt (remove the command from the message)
    prompt = message.text.replace(f"/{cmd_trigger}", "").strip()

    if not prompt:
        await message.reply("⚠️ Please provide a prompt.")
        return

    # 2. Notify user processing
    processing_msg = await message.reply(f"⚙️ Generating **{LANGUAGES[lang_key]}** code for: *{prompt}*...")

    # 3. Generate Code
    generated_code = get_code_from_blackbox(LANGUAGES[lang_key], prompt)

    # 4. Handle Error
    if "Error" in generated_code:
        await processing_msg.edit(generated_code)
        return

    # 5. Create a file
    file_extension = LANGUAGES[lang_key]
    file_name = f"generated_code.{file_extension}"
    
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(generated_code)

        # 6. Send the file
        await message.reply_document(
            document=file_name,
            caption=f"✅ **Generated {LANGUAGES[lang_key].title()} Code**\n"
                    f"📝 **Prompt:** `{prompt}`"
        )
        
        await processing_msg.delete()

    except Exception as e:
        await processing_msg.edit(f"❌ Failed to create file: {str(e)}")
    
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

# ==========================================
# START BOT
# ==========================================

print("🤖 Bot Starting with Heroku Config...")
app.run()
