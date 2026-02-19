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

ROB_MAX_NORMAL = 10_000
ROB_MAX_PREMIUM = 100_000

ROB_COOLDOWN = 60 * 20
PROTECT_DURATION = 60 * 60 * 24
PROTECT_COOLDOWN = 60 * 60 * 24
GIFT_COOLDOWN = 60 * 60 * 12

KILL_COST = 1000
REVIVE_SELF_COST = 2000
REVIVE_OTHER_COST = 2500
PROTECT_COST = 5000

SHOP: Dict[str, Dict[str, int]] = {
    "knife": {"price": 1500, "power": 1},
    "gun": {"price": 5000, "power": 2},
    "shield": {"price": 5000, "power": 0},
    "revive_potion": {"price": 3000, "power": 0},
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
            "balance": 0,
            "kills": 0,
            "deaths": 0,
            "is_dead": False
        }},
        upsert=True
    )
    await COOLDOWNS.update_one(
        {"user_id": uid},
        {"$setOnInsert": {
            "user_id": uid,
            "daily": 0,
            "rob": 0,
            "gift": 0,
            "protect_cd": 0,
            "shield_until": 0
        }},
        upsert=True
    )
    await INVENTORY.update_one(
        {"user_id": uid},
        {"$setOnInsert": {"user_id": uid, "items": {}}},
        upsert=True
    )

async def _get_user(uid: int) -> dict:
    await _ensure_user(uid)
    return await ECONOMY.find_one({"user_id": uid}) or {}

async def _get_cd(uid: int) -> dict:
    await _ensure_user(uid)
    return await COOLDOWNS.find_one({"user_id": uid}) or {}

async def _get_inv(uid: int) -> dict:
    await _ensure_user(uid)
    return await INVENTORY.find_one({"user_id": uid}) or {"items": {}}

async def _add_money(uid: int, amount: int):
    await ECONOMY.update_one(
        {"user_id": uid},
        {"$inc": {"balance": int(amount)}}
    )

async def _set_dead(uid: int, dead: bool):
    await ECONOMY.update_one(
        {"user_id": uid},
        {"$set": {"is_dead": bool(dead)}}
    )

async def _add_kill(uid: int):
    await ECONOMY.update_one(
        {"user_id": uid},
        {"$inc": {"kills": 1}}
    )

async def _add_death(uid: int):
    await ECONOMY.update_one(
        {"user_id": uid},
        {"$inc": {"deaths": 1}}
    )

async def _is_shielded(uid: int) -> Tuple[bool, int]:
    cd = await _get_cd(uid)
    until = int(cd.get("shield_until", 0))
    return (_now() < until), until

def _fmt_time_left(sec: int) -> str:
    if sec < 0:
        sec = 0
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h:
        return f"{h}ʜ {m}ᴍ"
    if m:
        return f"{m}ᴍ {s}s"
    return f"{s}s"

async def _inv_add(uid: int, item: str, qty: int = 1):
    await INVENTORY.update_one(
        {"user_id": uid},
        {"$inc": {f"items.{item}": int(qty)}},
        upsert=True
    )

def _premium(message) -> bool:
    return bool(getattr(message.from_user, "is_premium", False))

# ────────────────────────────
# /bal
# ────────────────────────────
@app.on_message(filters.command(["bal", "balance"]))
async def roshni_bal(_, message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    data = await _get_user(target.id)

    bal = int(data.get("balance", 0))
    kills = int(data.get("kills", 0))
    dead = bool(data.get("is_dead", False))
    shielded, _ = await _is_shielded(target.id)

    text = (
        "୨୧ **ʀᴏsʜɴɪ’ꜱ ᴡᴀʟʟᴇᴛ** ୨୧\n\n"
        f"✦ ᴜsᴇʀ · {target.mention}\n"
        f"✦ ʙᴀʟᴀɴᴄᴇ · `${bal:,}`\n"
        f"✦ ᴋɪʟʟs · `{kills}`\n"
        f"✦ sᴛᴀᴛᴜs · `{'ᴅᴇᴀᴅ' if dead else 'ᴀʟɪᴠᴇ'}`\n"
        f"✦ sʜɪᴇʟᴅ · `{'ᴏɴ' if shielded else 'ᴏғғ'}`\n\n"
        "✿ _ʀᴏsʜɴɪ ᴡᴀᴛᴄʜᴇs ᴏᴠᴇʀ ʏᴏᴜ_"
    )
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ────────────────────────────
# /daily
# ────────────────────────────
@app.on_message(filters.command(["daily", "claim"]))
async def roshni_daily(_, message):
    uid = message.from_user.id
    prem = _premium(message)
    cd = await _get_cd(uid)

    now = _now()
    last = int(cd.get("daily", 0))
    if now - last < 86400:
        left = 86400 - (now - last)
        return await message.reply_text(
            f"⏳ **ʟᴏᴠᴇ, ᴄᴏᴍᴇ ʙᴀᴄᴋ ɪɴ `{_fmt_time_left(left)}`**",
            parse_mode=ParseMode.MARKDOWN
        )

    reward = DAILY_PREMIUM if prem else DAILY_NORMAL
    await _add_money(uid, reward)
    await COOLDOWNS.update_one({"user_id": uid}, {"$set": {"daily": now}}, upsert=True)

    await message.reply_text(
        f"🎁 **ᴅᴀɪʟʏ ʙʟᴇssɪɴɢ ʀᴇᴄᴇɪᴠᴇᴅ**\n"
        f"💖 ʀᴏsʜɴɪ ɢᴀᴠᴇ ʏᴏᴜ `${reward:,}`",
        parse_mode=ParseMode.MARKDOWN
    )

# ────────────────────────────
# /items
# ────────────────────────────
@app.on_message(filters.command(["items"]))
async def roshni_items(_, message):
    uid = message.from_user.id
    inv = await _get_inv(uid)
    items = inv.get("items", {})

    inv_lines = []
    for k, v in items.items():
        if int(v) > 0:
            inv_lines.append(f"✦ `{k}` x`{v}`")

    inv_txt = "\n".join(inv_lines) if inv_lines else "_ɴᴏᴛʜɪɴɢ ɪɴ ʏᴏᴜʀ ʙᴀɢ ʏᴇᴛ_"

    shop_lines = []
    for name, meta in SHOP.items():
        shop_lines.append(f"✦ `{name}` — `${meta['price']:,}`")

    shop_txt = "\n".join(shop_lines)

    text = (
        "🎒 **ʀᴏsʜɴɪ’ꜱ ɪɴᴠᴇɴᴛᴏʀʏ**\n\n"
        f"{inv_txt}\n\n"
        "🛍️ **sᴏғᴛ ʟɪᴛᴛʟᴇ sʜᴏᴘ**\n"
        f"{shop_txt}\n\n"
        "✿ _ᴛʀᴇᴀᴛ ʏᴏᴜʀsᴇʟғ ɢᴇɴᴛʟʏ_"
    )
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
