import random
import time
from typing import Dict, Tuple

from pyrogram import filters
from pyrogram.enums import ParseMode

from Oneforall import app
from Oneforall.mongo import db

# ────────────────────────────
# Collections
# ────────────────────────────
ECONOMY = db.roshni_economy
COOLDOWNS = db.roshni_cooldowns
INVENTORY = db.roshni_inventory

# ────────────────────────────
# Config
# ────────────────────────────
DAILY_NORMAL = 1000
DAILY_PREMIUM = 2000

ROB_MAX_PERCENT = 0.35 # Max 35% of victim's wallet
ROB_COOLDOWN = 3600 # 1 Hour

KILL_COST = 1000
REVIVE_SELF_COST = 2000
PROTECT_COST = 5000
PROTECT_DURATION = 86400 # 24 Hours

SHOP: Dict[str, Dict[str, int]] = {
    "knife": {"price": 1500, "power": 1, "desc": "Increases kill success"},
    "gun": {"price": 5000, "power": 2, "desc": "High kill success rate"},
    "shield": {"price": 5000, "power": 0, "desc": "Protect from kills/robs"},
    "revive_potion": {"price": 3000, "power": 0, "desc": "Use to revive yourself"},
}

# ────────────────────────────
# Helpers
# ────────────────────────────
def _now() -> int:
    return int(time.time())

async def _ensure_user(uid: int):
    await ECONOMY.update_one(
        {"user_id": uid},
        {"$setOnInsert": {
            "user_id": uid,
            "balance": 500,
            "kills": 0,
            "deaths": 0,
            "is_dead": False
        }},
        upsert=True
    )

async def _get_user(uid: int) -> dict:
    await _ensure_user(uid)
    return await ECONOMY.find_one({"user_id": uid}) or {}

async def _get_cd(uid: int) -> dict:
    return await COOLDOWNS.find_one({"user_id": uid}) or {}

async def _get_inv(uid: int) -> dict:
    inv = await INVENTORY.find_one({"user_id": uid})
    return inv.get("items", {}) if inv else {}

def _fmt_time_left(sec: int) -> str:
    h, m = sec // 3600, (sec % 3600) // 60
    return f"{h}ʜ {m}ᴍ" if h else f"{m}ᴍ {sec % 60}s"

# ────────────────────────────
# Commands: Info & Daily
# ────────────────────────────

@app.on_message(filters.command(["bal", "balance"]))
async def roshni_bal(_, message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    data = await _get_user(target.id)
    inv = await _get_cd(target.id)
    
    shielded = inv.get("shield_until", 0) > _now()
    
    text = (
        "୨୧ **ʀᴏsʜɴɪ’ꜱ ᴡᴀʟʟᴇᴛ** ୨୧\n\n"
        f"✦ ᴜsᴇʀ · {target.mention}\n"
        f"✦ ʙᴀʟᴀɴᴄᴇ · `${data.get('balance', 0):,}`\n"
        f"✦ ᴋɪʟʟs · `{data.get('kills', 0)}`\n"
        f"✦ sᴛᴀᴛᴜs · `{'ᴅᴇᴀᴅ' if data.get('is_dead') else 'ᴀʟɪᴠᴇ'}`\n"
        f"✦ sʜɪᴇʟᴅ · `{'ᴏɴ' if shielded else 'ᴏғғ'}`"
    )
    await message.reply_text(text)

@app.on_message(filters.command(["daily", "claim"]))
async def roshni_daily(_, message):
    uid = message.from_user.id
    data = await _get_user(uid)
    
    if data.get("is_dead"):
        return await message.reply_text("💀 **ʏᴏᴜ ᴀʀᴇ ᴅᴇᴀᴅ, ʙᴀᴋᴀ!**\n_ɢʜᴏsᴛs ᴄᴀɴ'ᴛ ᴛᴏᴜᴄʜ ᴍᴏɴᴇʏ. ᴜsᴇ /revive_")

    cd = await _get_cd(uid)
    if _now() - cd.get("daily", 0) < 86400:
        left = 86400 - (_now() - cd.get("daily", 0))
        return await message.reply_text(f"⏳ **ᴄᴏᴍᴇ ʙᴀᴄᴋ ɪɴ `{_fmt_time_left(left)}`**")

    reward = DAILY_PREMIUM if getattr(message.from_user, "is_premium", False) else DAILY_NORMAL
    await ECONOMY.update_one({"user_id": uid}, {"$inc": {"balance": reward}})
    await COOLDOWNS.update_one({"user_id": uid}, {"$set": {"daily": _now()}}, upsert=True)
    await message.reply_text(f"🎁 **ʀᴏsʜɴɪ sᴍɪʟᴇᴅ!**\n`+${reward:,}` ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ.")

# ────────────────────────────
# Commands: Combat (Kill/Rob/Revive)
# ────────────────────────────

@app.on_message(filters.command("kill"))
async def roshni_kill(_, message):
    killer_id = message.from_user.id
    if not message.reply_to_message:
        return await message.reply_text("❗ **ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴘᴇʀsᴏɴ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴍᴜʀᴅᴇʀ.**")

    victim = message.reply_to_message.from_user
    killer_data = await _get_user(killer_id)
    victim_data = await _get_user(victim.id)
    victim_cd = await _get_cd(victim.id)

    if killer_data.get("is_dead"): return await message.reply_text("💀 **ʏᴏᴜ ᴀʀᴇ ᴀ ɢʜᴏsᴛ.**")
    if victim_data.get("is_dead"): return await message.reply_text("❗ **ᴛʜᴇʏ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴅᴇᴀᴅ.**")
    if victim_cd.get("shield_until", 0) > _now(): return await message.reply_text("🛡️ **ᴛʜᴇʏ ᴀʀᴇ ᴘʀᴏᴛᴇᴄᴛᴇᴅ ʙʏ ᴀ sʜɪᴇʟᴅ!**")
    if killer_data.get("balance", 0) < KILL_COST: return await message.reply_text(f"💸 **ᴋɪʟʟɪɴɢ ɪsɴ'ᴛ ᴄʜᴇᴀᴘ.** ɴᴇᴇᴅ `${KILL_COST}`")

    # Success rate logic
    inv = await _get_inv(killer_id)
    chance = 20 # Base 20%
    if inv.get("gun", 0) > 0: chance = 60
    elif inv.get("knife", 0) > 0: chance = 40

    await ECONOMY.update_one({"user_id": killer_id}, {"$inc": {"balance": -KILL_COST}})
    
    if random.randint(1, 100) <= chance:
        await ECONOMY.update_one({"user_id": victim.id}, {"$set": {"is_dead": True}, "$inc": {"deaths": 1}})
        await ECONOMY.update_one({"user_id": killer_id}, {"$inc": {"kills": 1, "balance": 500}})
        await message.reply_text(f"🎯 **ʜᴇᴀᴅsʜᴏᴛ!**\nʏᴏᴜ ᴋɪʟʟᴇᴅ {victim.mention} ᴀɴᴅ ᴇᴀʀɴᴇᴅ `$500` ʙᴏᴜɴᴛʏ.")
    else:
        await message.reply_text(f"🔫 **ʏᴏᴜ ᴍɪssᴇᴅ!**\n{victim.mention} ʟᴀᴜɢʜᴇᴅ ᴀᴛ ʏᴏᴜ. ʏᴏᴜ ʟᴏsᴛ `${KILL_COST}`")

@app.on_message(filters.command("revive"))
async def roshni_revive(_, message):
    uid = message.from_user.id
    data = await _get_user(uid)
    inv = await _get_inv(uid)

    if not data.get("is_dead"): return await message.reply_text("🌸 **ʏᴏᴜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴀʟɪᴠᴇ.**")

    # Check for potion first
    if inv.get("revive_potion", 0) > 0:
        await INVENTORY.update_one({"user_id": uid}, {"$inc": {"items.revive_potion": -1}})
        await ECONOMY.update_one({"user_id": uid}, {"$set": {"is_dead": False}})
        return await message.reply_text("🧪 **ʏᴏᴜ ᴅʀᴀɴᴋ ᴛʜᴇ ᴘᴏᴛɪᴏɴ ᴀɴᴅ ᴄᴀᴍᴇ ʙᴀᴄᴋ ᴛᴏ ʟɪғᴇ!**")

    if data.get("balance", 0) < REVIVE_SELF_COST:
        return await message.reply_text(f"🏥 **ʜᴏsᴘɪᴛᴀʟ ʙɪʟʟs ᴀʀᴇ ʜɪɢʜ.**\nɴᴇᴇᴅ `${REVIVE_SELF_COST}` ᴛᴏ ʀᴇᴠɪᴠᴇ.")

    await ECONOMY.update_one({"user_id": uid}, {"$set": {"is_dead": False}, "$inc": {"balance": -REVIVE_SELF_COST}})
    await message.reply_text("🏥 **ᴛʜᴇ ᴅᴏᴄᴛᴏʀs sᴀᴠᴇᴅ ʏᴏᴜ!**\nʏᴏᴜ ᴀʀᴇ ᴀʟɪᴠᴇ ᴀɢᴀɪɴ.")

# ────────────────────────────
# Commands: Shop & Inventory
# ────────────────────────────

@app.on_message(filters.command(["shop", "items"]))
async def roshni_shop(_, message):
    inv = await _get_inv(message.from_user.id)
    
    shop_txt = "🛍️ **ʀᴏsʜɴɪ’ꜱ sᴏғᴛ sʜᴏᴘ**\n\n"
    for item, info in SHOP.items():
        shop_txt += f"✦ `{item}` — `${info['price']:,}`\n   _{info['desc']}_\n\n"
    
    my_items = "\n".join([f"• {k} (x{v})" for k, v in inv.items() if v > 0]) or "_Empty_"
    shop_txt += f"🎒 **ʏᴏᴜʀ ʙᴀɢ:**\n{my_items}\n\n**ᴜsᴇ `/buy [item]` ᴛᴏ ᴘᴜʀᴄʜᴀsᴇ**"
    await message.reply_text(shop_txt)

@app.on_message(filters.command("buy"))
async def roshni_buy(_, message):
    if len(message.command) < 2: return await message.reply_text("🛍️ **ᴡʜᴀᴛ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙᴜʏ?**")
    
    item = message.command[1].lower()
    if item not in SHOP: return await message.reply_text("❌ **ɪᴛᴇᴍ ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ sʜᴏᴘ.**")

    uid = message.from_user.id
    user_data = await _get_user(uid)
    price = SHOP[item]["price"]

    if user_data.get("balance", 0) < price:
        return await message.reply_text(f"💸 **ʏᴏᴜ ᴀʀᴇ ᴛᴏᴏ ᴘᴏᴏʀ ᴛᴏ ʙᴜʏ `{item}`.**")

    await ECONOMY.update_one({"user_id": uid}, {"$inc": {"balance": -price}})
    await INVENTORY.update_one({"user_id": uid}, {"$inc": {f"items.{item}": 1}}, upsert=True)
    
    # Special logic for shield - activate it immediately
    if item == "shield":
        await COOLDOWNS.update_one({"user_id": uid}, {"$set": {"shield_until": _now() + PROTECT_DURATION}}, upsert=True)
        await message.reply_text(f"🛡️ **sʜɪᴇʟᴅ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ғᴏʀ 24 ʜᴏᴜʀs!**")
    else:
        await message.reply_text(f"🛒 **ᴘᴜʀᴄʜᴀsᴇᴅ `{item}` sᴜᴄᴄᴇssғᴜʟʟʏ!**")
  
