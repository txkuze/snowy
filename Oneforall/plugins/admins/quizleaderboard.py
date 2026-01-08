import asyncio
import requests
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.enums import ParseMode
from Oneforall import app
from Oneforall.mongo import db

STATS_COLL = db.quiz_stats  # Fixed: use db not mongodb
CHATS_COLL = db.chats

# 🎥 VIDEO + IMAGE (Your URLs)
LEADERBOARD_VIDEO = "https://files.catbox.moe/dtcr9p.mp4"
TROPHY_IMAGE = "https://files.catbox.moe/qplosp.jpg"

@app.on_poll_voted()
async def track_quiz_results(client, poll):
    """Auto track scores when users vote quiz"""
    if not poll.quiz:
        return
        
    chat_id = poll.chat.id
    voters = poll.recent_voters or []
    
    for voter_id in voters:
        is_correct = poll.correct_option_id == poll.option_ids.get(voter_id)
        
        await STATS_COLL.update_one(
            {"chat_id": chat_id, "user_id": voter_id},
            {
                "$setOnInsert": {"chat_id": chat_id, "user_id": voter_id, "username": f"User_{voter_id}"},
                "$inc": {"correct": 1 if is_correct else 0}
            },
            upsert=True
        )

async def get_target_chats():
    """Get all groups"""
    cursor = CHATS_COLL.find({"type": {"$in": ["group", "supergroup"]}})
    return [doc["chat_id"] async for doc in cursor]

async def get_quiz_leaderboard(chat_id: int, limit=10):
    """Get top 10 users by correct answers"""
    pipeline = [
        {"$match": {"chat_id": chat_id}},
        {"$group": {
            "_id": "$user_id",
            "username": {"$first": "$username"},
            "user_id": {"$first": "$user_id"},
            "correct_count": {"$sum": "$correct"}
        }},
        {"$sort": {"correct_count": -1}},
        {"$limit": limit}
    ]
    return list(STATS_COLL.aggregate(pipeline))

async def send_leaderboard(chat_id: int, manual=False):
    """Send leaderboard with video/image"""
    top_users = await get_quiz_leaderboard(chat_id)
    
    if not top_users:
        msg = await app.send_message(chat_id, "🏆 **No quiz stats yet! Play some quizzes first.**")
    else:
        text = "🏆 **QUIZ LEADERBOARD** (Top 10)

"
        for i, user in enumerate(top_users, 1):
            name = user.get("username", f"ID {user['user_id']}")
            score = user["correct_count"]
            emoji = "🥇🥈🥉"[i-1] if i <= 3 else f"{i}."
            text += f"{emoji} **{name}** → `{score}` ✅
"
        
        # 🎥 Try video first
        try:
            msg = await app.send_video(
                chat_id=chat_id,
                video=LEADERBOARD_VIDEO,
                caption=text,
                parse_mode=ParseMode.MARKDOWN,
                supports_streaming=True,
                duration=10
            )
        except:
            # Fallback image
            msg = await app.send_photo(
                chat_id=chat_id,
                photo=TROPHY_IMAGE,
                caption=text,
                parse_mode=ParseMode.MARKDOWN
            )
        
        # 📌 Auto-pin (auto only)
        if not manual:
            try:
                await app.pin_chat_message(chat_id, msg.id, notify=False)
            except:
                pass
    
    return msg

# 🔥 MAIN COMMANDS - Works instantly!
@app.on_message(filters.command(["quizlead", "leaderboard", "lb"]))
async def quizlead_cmd(client, message):
    """Manual leaderboard command"""
    await message.reply("📊 **Loading leaderboard...**")
    await send_leaderboard(message.chat.id, manual=True)
    await message.delete()  # Clean command

async def auto_leaderboard_loop():
    """Auto leaderboards 3PM + 9PM"""
    while True:
        now = datetime.now()
        afternoon = now.replace(hour=15, minute=0, second=0, microsecond=0)
        night = now.replace(hour=21, minute=0, second=0, microsecond=0)
        
        next_time = afternoon if now < afternoon else night
        if now > night:
            next_time += timedelta(days=1)
        
        await asyncio.sleep((next_time - now).total_seconds())
        
        chats = await get_target_chats()
        print(f"📊 Auto LB → {len(chats)} groups")
        for chat_id in chats:
            try:
                await send_leaderboard(chat_id)
            except Exception as e:
                print(f"LB failed {chat_id}: {e}")

@app.on_startup()
async def startup():
    asyncio.create_task(auto_leaderboard_loop())
    print("📊 QuizLead LOADED!")
    print("📱 Commands: /quizlead /leaderboard /lb")
