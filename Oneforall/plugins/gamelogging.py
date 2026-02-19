"""
Pyrogram Plugin: Game Hub Logger
=================================
Drop this file into your bot's plugins/ directory.

Logs all game-related Telegram events including:
  - WebApp launches (when users open a game from the bot)
  - /game, /play, /leaderboard, /profile commands
  - Inline button interactions with game_* data
  - Any message in the group containing your WebApp link

Setup:
  1. Copy this file to: plugins/game_logger.py
  2. Set your WEBAPP_URL below (your Lovable/published URL)
  3. Optionally set MONGODB_URI to also log to MongoDB directly
  4. The plugin auto-logs to console + MongoDB Atlas

Dependencies (add to requirements.txt):
  pyrogram>=2.0.0
  motor>=3.0.0          # async MongoDB (optional, for direct DB logging)
  python-dotenv>=1.0.0  # for .env support (optional)
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

# ─── Configuration ────────────────────────────────────────────────────────────
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://telegram-game-hub.vercel.app/")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://knight4563:knight4563@cluster0.a5br0se.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
MONGODB_DB = os.getenv("MONGODB_DB", "telegram_game_hub")
LOG_COLLECTION = "game_events"
LOGGER_EDGE_URL = os.getenv(
    "GAME_LOGGER_EDGE_URL",
    "https://tvrnjaysfnbwovmlevqb.supabase.co/functions/v1/game-logger",
)

# Supported games config
GAMES = {
    "carrom":        {"name": "Carrom",         "emoji": "🎯"},
    "chess":         {"name": "Chess",           "emoji": "♟"},
    "car-race":      {"name": "Car Race",        "emoji": "🏎"},
    "hill-climbing": {"name": "Hill Climbing",   "emoji": "⛰"},
    "snake-ladder":  {"name": "Snake & Ladder",  "emoji": "🐍"},
    "ludo":          {"name": "Ludo",            "emoji": "🎲"},
}

# ─── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GameHub] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("game_hub")

# ─── MongoDB (optional) ───────────────────────────────────────────────────────
_mongo_collection = None

async def _get_mongo_collection():
    """Lazily initialize async MongoDB connection."""
    global _mongo_collection
    if _mongo_collection is not None:
        return _mongo_collection
    if not MONGODB_URI:
        return None
    try:
        import motor.motor_asyncio
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
        db = client[MONGODB_DB]
        _mongo_collection = db[LOG_COLLECTION]
        log.info("Connected to MongoDB Atlas: %s/%s", MONGODB_DB, LOG_COLLECTION)
        return _mongo_collection
    except ImportError:
        log.warning("motor not installed. pip install motor to enable MongoDB logging.")
        return None
    except Exception as e:
        log.error("MongoDB connection failed: %s", e)
        return None


# ─── Core Logger ──────────────────────────────────────────────────────────────
async def log_event(
    event_type: str,
    user_id: int,
    username: str,
    first_name: str,
    chat_id: Optional[int] = None,
    chat_title: Optional[str] = None,
    game_id: Optional[str] = None,
    mode: Optional[str] = None,
    room_code: Optional[str] = None,
    extra: Optional[dict] = None,
):
    """Write a structured game event to console + MongoDB."""
    doc = {
        "type": event_type,
        "userId": str(user_id),
        "username": username or f"user{user_id}",
        "firstName": first_name,
        "gameId": game_id or "unknown",
        "mode": mode,
        "roomCode": room_code,
        "chatId": str(chat_id) if chat_id else None,
        "chatTitle": chat_title,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "telegram-bot-plugin",
        **(extra or {}),
    }

    # Console log
    log.info(
        "EVENT %-20s | user=%-20s | game=%-15s | mode=%-10s | chat=%s",
        event_type,
        f"{username}({user_id})",
        game_id or "N/A",
        mode or "N/A",
        chat_title or chat_id or "DM",
    )

    # MongoDB (async, non-blocking)
    col = await _get_mongo_collection()
    if col is not None:
        try:
            await col.insert_one(doc)
        except Exception as e:
            log.error("MongoDB insert failed: %s", e)


def _extract_user(obj):
    """Extract user info from message or callback query."""
    user = getattr(obj, "from_user", None)
    if not user:
        return 0, "", ""
    return user.id, user.username or f"user{user.id}", user.first_name or ""


def _extract_chat(obj):
    """Extract chat info."""
    chat = getattr(obj, "chat", None)
    if not chat:
        return None, None
    return chat.id, getattr(chat, "title", None)


# ─── Build Game Menu ──────────────────────────────────────────────────────────
def build_game_menu() -> InlineKeyboardMarkup:
    """Inline keyboard with all games as WebApp buttons."""
    buttons = []
    game_list = list(GAMES.items())
    for i in range(0, len(game_list), 2):
        row = []
        for game_id, info in game_list[i:i+2]:
            row.append(InlineKeyboardButton(
                text=f"{info['emoji']} {info['name']}",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/lobby/{game_id}"),
            ))
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton("🏆 Leaderboard", web_app=WebAppInfo(url=f"{WEBAPP_URL}/leaderboard")),
        InlineKeyboardButton("👤 Profile", web_app=WebAppInfo(url=f"{WEBAPP_URL}/profile")),
    ])
    buttons.append([
        InlineKeyboardButton(
            "🎮 Open Full Hub",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )
    ])
    return InlineKeyboardMarkup(buttons)


# ─── Command Handlers ─────────────────────────────────────────────────────────
@Client.on_message(filters.command(["start", "play", "game", "games"]))
async def cmd_start(client: Client, message: Message):
    user_id, username, first_name = _extract_user(message)
    chat_id, chat_title = _extract_chat(message)
    cmd = message.command[0] if message.command else "start"

    await log_event(
        event_type="bot_command",
        user_id=user_id,
        username=username,
        first_name=first_name,
        chat_id=chat_id,
        chat_title=chat_title,
        extra={"command": f"/{cmd}"},
    )

    await message.reply_text(
        f"👋 Hey **{first_name}**!\n\n"
        "🎮 **Game Hub** — Choose a game to play:\n\n"
        + "\n".join(f"{v['emoji']} **{v['name']}**" for v in GAMES.values())
        + "\n\n💡 All games support **Solo**, **VS Bot** and **Multiplayer**!",
        reply_markup=build_game_menu(),
    )


@Client.on_message(filters.command(["leaderboard", "lb", "top"]))
async def cmd_leaderboard(client: Client, message: Message):
    user_id, username, first_name = _extract_user(message)
    chat_id, chat_title = _extract_chat(message)

    await log_event(
        event_type="leaderboard_viewed",
        user_id=user_id,
        username=username,
        first_name=first_name,
        chat_id=chat_id,
        chat_title=chat_title,
    )

    await message.reply_text(
        "🏆 **Leaderboard**\nView full rankings in the hub:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🏆 Open Leaderboard",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/leaderboard"),
            )
        ]]),
    )


@Client.on_message(filters.command(["profile", "stats", "me"]))
async def cmd_profile(client: Client, message: Message):
    user_id, username, first_name = _extract_user(message)
    chat_id, chat_title = _extract_chat(message)

    await log_event(
        event_type="profile_viewed",
        user_id=user_id,
        username=username,
        first_name=first_name,
        chat_id=chat_id,
        chat_title=chat_title,
    )

    await message.reply_text(
        f"👤 **{first_name}'s Profile**\nView your full stats and coin history:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "👤 Open Profile",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/profile"),
            )
        ]]),
    )


@Client.on_message(filters.command(["join"]))
async def cmd_join(client: Client, message: Message):
    """Handle /join ROOMCODE — logs the join attempt and opens the game."""
    user_id, username, first_name = _extract_user(message)
    chat_id, chat_title = _extract_chat(message)
    args = message.command[1:] if len(message.command) > 1 else []
    room_code = args[0].upper() if args else None

    await log_event(
        event_type="room_join_attempt",
        user_id=user_id,
        username=username,
        first_name=first_name,
        chat_id=chat_id,
        chat_title=chat_title,
        mode="online",
        room_code=room_code,
        extra={"command": "/join", "hasCode": bool(room_code)},
    )

    if not room_code:
        await message.reply_text(
            "Usage: `/join ROOMCODE`\n\nGet the room code from the player who created the match.",
            parse_mode="markdown",
        )
        return

    await message.reply_text(
        f"🎮 Joining room **{room_code}**...",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                f"🎮 Join Room {room_code}",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}?join={room_code}"),
            )
        ]]),
    )


# ─── WebApp Data Receiver ─────────────────────────────────────────────────────
@Client.on_message(filters.web_app_data)
async def on_webapp_data(client: Client, message: Message):
    """Receive structured events sent from the WebApp via sendData()."""
    user_id, username, first_name = _extract_user(message)
    chat_id, chat_title = _extract_chat(message)

    raw = message.web_app_data.data if message.web_app_data else "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"raw": raw}

    event_type = data.get("type", "webapp_event")
    game_id = data.get("gameId")
    mode = data.get("mode")

    await log_event(
        event_type=event_type,
        user_id=user_id,
        username=username,
        first_name=first_name,
        chat_id=chat_id,
        chat_title=chat_title,
        game_id=game_id,
        mode=mode,
        room_code=data.get("roomCode"),
        extra={k: v for k, v in data.items() if k not in ("type", "gameId", "mode", "roomCode")},
    )

    # Acknowledge silently (WebApp data messages shouldn't be replied to visibly)
    try:
        await message.delete()
    except Exception:
        pass


# ─── Callback Query Handler ───────────────────────────────────────────────────
@Client.on_callback_query(filters.regex(r"^game_"))
async def on_game_callback(client: Client, callback_query: CallbackQuery):
    """Handle inline button callbacks prefixed with game_"""
    user_id, username, first_name = _extract_user(callback_query)
    chat_id, chat_title = _extract_chat(callback_query.message)
    data = callback_query.data or ""

    parts = data.split("_", 2)
    game_id = parts[1] if len(parts) > 1 else "unknown"
    action = parts[2] if len(parts) > 2 else "open"

    await log_event(
        event_type="game_button_clicked",
        user_id=user_id,
        username=username,
        first_name=first_name,
        chat_id=chat_id,
        chat_title=chat_title,
        game_id=game_id,
        extra={"callbackData": data, "action": action},
    )

    await callback_query.answer(f"Opening {GAMES.get(game_id, {}).get('name', game_id)}...")


# ─── Group: Any member opens the WebApp ───────────────────────────────────────
@Client.on_message(
    filters.group
    & filters.regex(r"t\.me/\w+/\w+|lovable\.app|game")
)
async def on_group_game_mention(client: Client, message: Message):
    """Log when anyone in a group mentions a game link."""
    user_id, username, first_name = _extract_user(message)
    chat_id, chat_title = _extract_chat(message)

    await log_event(
        event_type="group_game_mention",
        user_id=user_id,
        username=username,
        first_name=first_name,
        chat_id=chat_id,
        chat_title=chat_title,
        extra={"messageText": (message.text or "")[:200]},
    )


# ─── Error Handler ────────────────────────────────────────────────────────────
@Client.on_message(filters.command(["help", "hubhelp"]))
async def cmd_help(client: Client, message: Message):
    user_id, username, first_name = _extract_user(message)
    await log_event("help_requested", user_id, username, first_name)
    await message.reply_text(
        "🎮 **Game Hub — Bot Commands**\n\n"
        "/start or /games — Open the game hub\n"
        "/join `ROOMCODE` — Join an online match by code\n"
        "/leaderboard — View top players\n"
        "/profile — Your stats and coins\n"
        "/help — Show this message\n\n"
        "**Games available:**\n"
        + "\n".join(f"{v['emoji']} {v['name']}" for v in GAMES.values()),
        parse_mode="markdown",
    )
