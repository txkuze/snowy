import random
import time
import requests
import asyncio

from pyrogram import filters
from pyrogram.enums import ChatAction, PollType, ParseMode

from Oneforall import app
from Oneforall.mongo import db

# ⚙️ CONFIG
CHATS_COLL = db.chats
STATS_COLL = db.quiz_stats
LOGGER_ID = -1003634796457  # ← PUT YOUR LOG CHANNEL/GROUP ID HERE

last_command_time = {}

async def get_target_chats():
    cursor = CHATS_COLL.find({"type": {"$in": ["group", "supergroup"]}})
    return [doc["chat_id"] async for doc in cursor]


async def log_quiz_sent(chat_id: int, chat_title: str = None):
    """Log quiz timing to special channel"""
    if not LOGGER_ID or LOGGER_ID == "":
        return
        
    try:
        start_time = datetime.now().strftime("%H:%M:%S")
        await app.send_message(
            LOGGER_ID,
            f"🧠 **Quiz Sent** `{start_time}`"
            f"📱 **Chat:** {chat_title or chat_id}"
            f"🔗 **ID:** `{chat_id}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass


async def send_quiz(chat_id: int):
    categories = [9, 17, 18, 20, 21, 27]
    await app.send_chat_action(chat_id, ChatAction.TYPING)

    url = f"https://opentdb.com/api.php?amount=1&category={random.choice(categories)}&type=multiple"
    response = requests.get(url).json()
    question_data = response["results"][0]

    question = question_data["question"]
    correct_answer = question_data["correct_answer"]
    incorrect_answers = question_data["incorrect_answers"]

    all_answers = incorrect_answers + [correct_answer]
    random.shuffle(all_answers)
    cid = all_answers.index(correct_answer)

    poll = await app.send_poll(
        chat_id=chat_id,
        question=f"🧠 **ᴡᴀɪᴛ 𝟻 sᴇᴄᴏɴᴅ!**

{question}",
        options=all_answers,
        is_anonymous=False,
        type=PollType.QUIZ,
        correct_option_id=cid,
    )
    return poll.id


@app.on_message(filters.command(["quiz"]))
async def quiz_cmd(client, message):
    user_id = message.from_user.id
    current_time = time.time()

    if user_id in last_command_time and current_time - last_command_time[user_id] < 5:
        return await message.reply_text("⏳ **ᴡᴀɪᴛ 𝟻 sᴇᴄᴏɴᴅ ! **")

    last_command_time[user_id] = current_time
    await send_quiz(message.chat.id)


async def auto_quiz_loop():
    INTERVAL = 3600  # 1 hour
    while True:
        try:
            chats = await get_target_chats()
            print(f"🧠 Quiz → {len(chats)} groups")
            
            for chat_id in chats:
                try:
                    # Get chat title for log
                    chat = await app.get_chat(chat_id)
                    await log_quiz_sent(chat_id, chat.title)
                    await send_quiz(chat_id)
                except Exception as e:
                    print(f"Quiz failed {chat_id}: {e}")
        except Exception as e:
            print(f"Quiz loop error: {e}")
        await asyncio.sleep(INTERVAL)


@app.on_startup()
async def startup():
    asyncio.create_task(auto_quiz_loop())
    print("🧠ᴀᴜᴛᴏ ǫᴜɪᴢ sᴛᴀʀᴛᴇᴅ")
