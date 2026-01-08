import random
import asyncio
from pyrogram import filters
from Oneforall import app
from Oneforall.mongo import db

# Economy DB
ECONOMY_COLL = db.baka_economy
PROTECT_COLL = db.baka_protect

@app.on_message(filters.command("daily"))
async def daily_cmd(client, message):
    user_id = message.from_user.id
    
    # Premium check (user_id in premium list or sub)
    is_premium = False  # Add your premium check logic
    
    try:
        user_data = await ECONOMY_COLL.find_one({"user_id": user_id})
        last_daily = user_data.get("last_daily", 0) if user_data else 0
        
        current_time = time.time()
        if current_time - last_daily < 86400:  # 24 hours
            remaining = 86400 - (current_time - last_daily)
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            return await message.reply(f"⏳ Come back in **{hours}h {mins}m** for daily!")
        
        amount = 2000 if is_premium else 1000
        await ECONOMY_COLL.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "balance": user_data.get("balance", 0) + amount, "last_daily": current_time}},
            upsert=True
        )
        
        await message.reply(f"💰 **Daily claimed!** +${amount:,}
💳 **New balance:** ${user_data.get('balance', 0) + amount:,}")
        
    except Exception as e:
        await message.reply("❌ **Error claiming daily!**")

@app.on_message(filters.command("bal", "balance"))
async def bal_cmd(client
