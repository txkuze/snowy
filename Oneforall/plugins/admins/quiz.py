import random
import time
import requests
import asyncio
from datetime import datetime
from pyrogram import filters
from pyrogram.enums import ChatAction, PollType, ParseMode

from Oneforall import app, mongodb

# CONFIG
CHATS_COLL = db.chats
STATS_COLL = db.quiz_stats
LOGGER_ID = -1003634796457 # ← CHANGE TO YOUR LOG CHANNEL ID

last_command_time = {}

async def get_target_chats():
    """Get all groups from mongodb.chats"""
    try:
        cursor = CHATS_COLL.find({"type": {"$in": ["group", "supergroup"]}})
        return [doc["chat_id"] async for doc in cursor]
    except:
        return []

async def log_quiz_sent(chat_id: int, chat_title: str = None):
    """Log to special channel"""
    if not LOGGER_ID or LOGGER_ID == "":
        return
    try:
        start_time = datetime.now().strftime("%H:%M:%S")
        await app.send_message(
            LOGGER_ID,
            f"🧠 **Quiz Sent** `{start_time}`
"
            f"📱 **Chat:** {chat_title or chat_id}
"
            f"🔗 **ID:** `{chat_id}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        print(f"Log failed: {e}")

async def send_quiz(chat_id: int):
    """Send single quiz poll"""
    categories = [9, 17, 18, 20, 21, 27]
    await app.send_chat_action(chat_id, ChatAction.TYPING)
    
    try:
        url = f"https://opentdb.com/api.php?amount=1&category={random.choice(categories)}&type=multiple"
        response = requests.get(url, timeout=10).json()
        data = response["results"][0]
        
        question = data["question"]
        correct = data["correct_answer"]
        incorrect = data["incorrect_answers"]
        answers = incorrect + [correct]
        random.shuffle(answers)
        correct_id = answers.index(correct)
        
        poll = await app.send_poll(
            chat_id=chat_id,
            question=f"🧠 **QUIZ TIME!**

{question}",
            options=answers,
            is_anonymous=False,
            type=PollType.QUIZ,
            correct_option_id=correct_id
        )
        return poll.id
    except Exception as e:
        print(f"Quiz send error {chat_id}: {e}")
        return None

@app.on_message(filters.command("quiz"))
async def quiz_cmd(client, message):
    """Manual /quiz command"""
    uid = message.from_user.id
    current_time = time.time()
    
    if uid in last_command_time and current_time - last_command_time[uid] < 5:
        return await message.reply("⏳ **Wait 5 seconds!**")
    
    last_command_time[uid] = current_time
    await message.reply("🧠 **Quiz loading...**")
    
    poll_id = await send_quiz(message.chat.id)
    if poll_id:
        await message.delete()  # Clean command after success
    else:
        await message.edit("❌ **Quiz failed to load!**")

async def auto_quiz_loop():
    """Auto quizzes every hour"""
    INTERVAL = 3600  # 1 hour
    while True:
        try:
            chats = await get_target_chats()
            print(f"🧠 Auto quiz → {len(chats)} groups")
            
            for chat_id in chats:
                try:
                    chat = await app.get_chat(chat_id)
                    await log_quiz_sent(chat_id, getattr(chat, 'title', None))
                    await send_quiz(chat_id)
                    await asyncio.sleep(2)  # 2s delay between groups
                except Exception as e:
                    print(f"Auto quiz fail {chat_id}: {e}")
        except Exception as e:
            print(f"Auto loop error: {e}")
        
        await asyncio.sleep(INTERVAL)

# STARTUP
@app.on_startup()
async def startup():
    asyncio.create_task(auto_quiz_loop())
    print("🧠 ✅ FULL QUIZ SYSTEM LOADED!")
    print("📱 Commands: /quiz")
    print("🔄 Auto hourly quizzes started")

print("🧠 Quiz plugin loading...")
