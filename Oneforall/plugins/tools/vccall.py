import asyncio
from datetime import datetime
from logging import getLogger
from typing import Dict, Set

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.raw import functions

from Oneforall import app
from Oneforall.utils.database import get_assistant

LOGGER = getLogger(__name__)

# ───────── CONFIG ─────────
VC_LOG_CHANNEL_ID = -1003634796457  # ✅ PUT YOUR VC LOG CHANNEL ID HERE

prefixes = [".", "!", "/", "@", "?", "'"]

# ───────── STATE ─────────
vc_active_users: Dict[int, Set[int]] = {}
active_vc_chats: Set[int] = set()
vc_logging_status: Dict[int, bool] = {}


# ───────── SMALL CAPS ─────────
def to_small_caps(text: str):
    mapping = {
        "a":"ᴀ","b":"ʙ","c":"ᴄ","d":"ᴅ","e":"ᴇ","f":"ꜰ","g":"ɢ","h":"ʜ","i":"ɪ","j":"ᴊ",
        "k":"ᴋ","l":"ʟ","m":"ᴍ","n":"ɴ","o":"ᴏ","p":"ᴘ","q":"ǫ","r":"ʀ","s":"s","t":"ᴛ",
        "u":"ᴜ","v":"ᴠ","w":"ᴡ","x":"x","y":"ʏ","z":"ᴢ",
        "A":"ᴀ","B":"ʙ","C":"ᴄ","D":"ᴅ","E":"ᴇ","F":"ꜰ","G":"ɢ","H":"ʜ","I":"ɪ","J":"ᴊ",
        "K":"ᴋ","L":"ʟ","M":"ᴍ","N":"ɴ","O":"ᴏ","P":"ᴘ","Q":"ǫ","R":"ʀ","S":"s","T":"ᴛ",
        "U":"ᴜ","V":"ᴠ","W":"ᴡ","X":"x","Y":"ʏ","Z":"ᴢ"
    }
    return "".join(mapping.get(c, c) for c in text)


# ───────── VC LOGGER CORE ─────────
async def load_vc_logger_status():
    # You can implement persistent storage here if needed
    pass

async def get_vc_logger_status(chat_id: int) -> bool:
    return vc_logging_status.get(chat_id, False)


@app.on_message(filters.command("vclogger", prefixes=prefixes) & filters.group)
async def vclogger_command(_, message: Message):
    chat_id = message.chat.id
    args = message.text.split()

    if len(args) == 1:
        status = await get_vc_logger_status(chat_id)
        await message.reply(
            f"🎧 <b>ᴠ¢ ℓσggєʀ:</b> <b>{to_small_caps(str(status))}</b>\n\n"
            "➤ <code>/vclogger on</code>\n"
            "➤ <code>/vclogger off</code>"
        )
        return

    arg = args[1].lower()
    if arg in ("on", "enable", "yes"):
        vc_logging_status[chat_id] = True
        active_vc_chats.add(chat_id)
        asyncio.create_task(monitor_vc_chat(chat_id))
        await message.reply("✅ <b>ᴠ¢ ℓσggєʀ ᴇɴαвℓє∂</b>")

    elif arg in ("off", "disable", "no"):
        vc_logging_status[chat_id] = False
        active_vc_chats.discard(chat_id)
        vc_active_users.pop(chat_id, None)
        await message.reply("🚫 <b>ᴠ¢ ℓσggєʀ ∂ιѕαвℓє∂</b>")


async def get_group_call_participants(userbot, peer):
    try:
        full = await userbot.invoke(functions.channels.GetFullChannel(channel=peer))
        if not full.full_chat.call:
            return []

        call = full.full_chat.call
        res = await userbot.invoke(
            functions.phone.GetGroupParticipants(call=call, ids=[], sources=[], offset="", limit=100)
        )
        return res.participants
    except Exception:
        return []


async def monitor_vc_chat(chat_id: int):
    userbot = await get_assistant(chat_id)
    if not userbot:
        return

    while chat_id in active_vc_chats and await get_vc_logger_status(chat_id):
        peer = await userbot.resolve_peer(chat_id)
        participants = await get_group_call_participants(userbot, peer)

        new_users = {p.peer.user_id for p in participants if hasattr(p.peer, "user_id")}
        old_users = vc_active_users.get(chat_id, set())

        for uid in new_users - old_users:
            asyncio.create_task(handle_user_join(chat_id, uid, userbot))

        for uid in old_users - new_users:
            asyncio.create_task(handle_user_leave(chat_id, uid, userbot))

        vc_active_users[chat_id] = new_users
        await asyncio.sleep(5)


async def handle_user_join(chat_id: int, user_id: int, userbot):
    user = await userbot.get_users(user_id)
    chat = await app.get_chat(chat_id)
    now = datetime.now().strftime("%d %b %Y • %H:%M:%S")
    mention = f'<a href="tg://user?id={user_id}"><b>{to_small_caps(user.first_name)}</b></a>'

    msg_text = (
        f"<blockquote>╭─━━━━━━━─╮\n"
        f"│  🎶 ᴠ¢ υѕєʀ ᴊσιηєᴅ  │\n"
        f"╰─━━━━━━━─╯\n"
        f"╭─━━━━━━━━━━━━─╮\n"
        f"│ 👤 ɴᴀмє      : {to_small_caps(user.first_name)}\n"
        f"│ 🧬 υѕєʀι∂   : {user.id}\n"
        f"│ 🛡️ υѕєʀηαмє : @{user.username or 'ɴ/α'}\n"
        f"│ 💌 ᴄнαт    : {chat.title}\n"
        f"│ 🆔 ᴄнαт ι∂ : {chat.id}\n"
        f"│ ⏳ ᴛιмє     : {now}\n"
        f"╰─━━━━━━━━━━━━─╯</blockquote>"
    )
    await app.send_message(chat_id, msg_text)
    await app.send_message(VC_LOG_CHANNEL_ID, msg_text)


async def handle_user_leave(chat_id: int, user_id: int, userbot):
    user = await userbot.get_users(user_id)
    chat = await app.get_chat(chat_id)
    now = datetime.now().strftime("%d %b %Y • %H:%M:%S")
    mention = f'<a href="tg://user?id={user_id}"><b>{to_small_caps(user.first_name)}</b></a>'

    msg_text = (
        f"<blockquote>╭─━━━━━━━─╮\n"
        f"│  🌌 ᴠ¢ υѕєʀ ℓєƒт   │\n"
        f"╰─━━━━━━━─╯\n"
        f"╭─━━━━━━━━━━━━─╮\n"
        f"│ 👤 ɴᴀмє      : {to_small_caps(user.first_name)}\n"
        f"│ 🧬 υѕєʀι∂   : {user.id}\n"
        f"│ 🛡️ υѕєʀηαмє : @{user.username or 'ɴ/α'}\n"
        f"│ 💌 ᴄнαт    : {chat.title}\n"
        f"│ 🆔 ᴄнαт ι∂ : {chat.id}\n"
        f"│ ⏳ ᴛιмє     : {now}\n"
        f"╰─━━━━━━━━━━━━─╯</blockquote>"
    )
    await app.send_message(chat_id, msg_text)
    await app.send_message(VC_LOG_CHANNEL_ID, msg_text)


# Optional: Show current VC members in a similar stylish box
@app.on_message(filters.command("vcmembers", prefixes=prefixes) & filters.group)
async def vcmembers_command(_, message: Message):
    chat_id = message.chat.id
    userbot = await get_assistant(chat_id)
    if not userbot:
        return await message.reply("⚠️ No assistant available for VC monitoring.")

    participants = await get_group_call_participants(userbot, await userbot.resolve_peer(chat_id))
    if not participants:
        return await message.reply("ℹ️ ᴠ¢ ιѕ ᴇмρтʏ.")

    msg_text = "<blockquote>╭─━━━━━━━─╮\n│  🌟 ᴠ¢ мємвєяѕ │\n╰─━━━━━━━─╯\n</blockquote>"
    for p in participants:
        user = await userbot.get_users(p.peer.user_id)
        msg_text += (
            f"<blockquote expandable>╭─━━━━━━━━━━━━─╮\n"
            f"│ 👤 ɴᴀмє      : {to_small_caps(user.first_name)}\n"
            f"│ 🧬 υѕєʀι∂   : {user.id}\n"
            f"│ 🛡️ υѕєʀηαмє : @{user.username or 'ɴ/α'}\n"
            f"╰─━━━━━━━━━━━━─╯\n</blockquote expandable>"
        )

    await message.reply(msg_text)


# ───────── INIT ─────────
async def initialize_vc_logger():
    await load_vc_logger_status()
