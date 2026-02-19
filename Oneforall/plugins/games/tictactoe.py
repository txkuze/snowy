import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Oneforall import app
from Oneforall.core.mongo import mongodb

games = {}
db = mongodb.xoxo_leaderboard

EMPTY = "⬜"
X = "❌"
O = "⭕"

WIN = [
    [0,1,2],[3,4,5],[6,7,8],
    [0,3,6],[1,4,7],[2,5,8],
    [0,4,8],[2,4,6]
]

# ───── HELPERS ─────

def check(board):
    for a,b,c in WIN:
        if board[a] == board[b] == board[c] != EMPTY:
            return board[a]
    if EMPTY not in board:
        return "draw"
    return None

def init_game(gid, user):
    games[gid] = {
        "board": [EMPTY]*9,
        "p1": user.id,
        "p1_name": user.first_name,
        "p2": None,
        "p2_name": None,
        "turn": X,
        "mode": None,
        "finished": False
    }

def is_player(g, uid):
    return uid in (g["p1"], g["p2"])

def board_kb(gid, board):
    rows = []
    for i in range(0,9,3):
        rows.append([
            InlineKeyboardButton(board[i], callback_data=f"xoxo:{gid}:{i}"),
            InlineKeyboardButton(board[i+1], callback_data=f"xoxo:{gid}:{i+1}"),
            InlineKeyboardButton(board[i+2], callback_data=f"xoxo:{gid}:{i+2}")
        ])
    rows.append([
        InlineKeyboardButton("🔁 Rematch", callback_data=f"xoxo_rematch:{gid}"),
        InlineKeyboardButton("🛑 End Game", callback_data=f"xoxo_end:{gid}")
    ])
    return InlineKeyboardMarkup(rows)

def bot_move(board):
    for i in range(9):
        if board[i] == EMPTY:
            board[i] = O
            if check(board) == O:
                board[i] = EMPTY
                return i
            board[i] = EMPTY
    for i in range(9):
        if board[i] == EMPTY:
            board[i] = X
            if check(board) == X:
                board[i] = EMPTY
                return i
            board[i] = EMPTY
    if board[4] == EMPTY:
        return 4
    return random.choice([i for i in range(9) if board[i] == EMPTY])

async def add_win(uid, name):
    if uid:
        await db.update_one(
            {"user_id": uid},
            {"$inc": {"wins": 1}, "$set": {"name": name}},
            upsert=True
        )

# ───── /game ─────

@app.on_message(filters.command("game"))
async def game_menu(_, m):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌⭕ Tic Tac Toe", callback_data="game_xoxo")]
    ])
    await m.reply("🎮 <b>Game Center</b>\n\nChoose a game:", reply_markup=kb)

@app.on_callback_query(filters.regex("^game_xoxo$"))
async def game_xoxo(_, q: CallbackQuery):
    if q.message.chat.id in games:
        return await q.answer("⚠️ Game already running!", show_alert=True)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Play with Friend", callback_data="xoxo_friend")],
        [InlineKeyboardButton("🤖 Play with Bot", callback_data="xoxo_bot")]
    ])
    await q.message.edit_text("❌⭕ <b>Tic Tac Toe</b>\n\nChoose mode:", reply_markup=kb)

# ───── FRIEND MODE ─────

@app.on_callback_query(filters.regex("^xoxo_friend$"))
async def friend_mode(_, q: CallbackQuery):
    init_game(q.message.chat.id, q.from_user)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Join Game", callback_data=f"xoxo_join:{q.message.chat.id}")]
    ])
    await q.message.edit_text(
        f"❌⭕ <b>Tic Tac Toe</b>\n\n"
        f"👤 Player 1: <b>{q.from_user.first_name}</b>\n"
        f"⏳ Waiting for Player 2…",
        reply_markup=kb
    )

# ───── BOT MODE ─────

@app.on_callback_query(filters.regex("^xoxo_bot$"))
async def bot_mode(_, q: CallbackQuery):
    init_game(q.message.chat.id, q.from_user)
    g = games[q.message.chat.id]
    g["mode"] = "bot"
    g["p2_name"] = "Bot 🤖"

    await q.message.edit_text(
        f"🤖 <b>Bot Mode</b>\n\n"
        f"❌ {g['p1_name']}\n"
        f"⭕ Bot 🤖\n\n"
        f"🔄 <b>Your Turn</b>",
        reply_markup=board_kb(q.message.chat.id, g["board"])
    )

# ───── JOIN FRIEND ─────

@app.on_callback_query(filters.regex("^xoxo_join"))
async def join_friend(_, q: CallbackQuery):
    gid = int(q.data.split(":")[1])
    g = games.get(gid)
    if not g or q.from_user.id == g["p1"]:
        return

    g["p2"] = q.from_user.id
    g["p2_name"] = q.from_user.first_name
    g["mode"] = "friend"

    await q.message.edit_text(
        f"🎮 <b>Game Started!</b>\n\n"
        f"❌ {g['p1_name']}\n"
        f"⭕ {g['p2_name']}\n\n"
        f"🔄 <b>Turn: ❌</b>",
        reply_markup=board_kb(gid, g["board"])
    )

# ───── MOVE (REMATCH SAFE) ─────

@app.on_callback_query(filters.regex("^xoxo:"))
async def move(_, q: CallbackQuery):
    _, gid, pos = q.data.split(":")
    gid, pos = int(gid), int(pos)
    g = games.get(gid)

    if not g or g["finished"] or not is_player(g, q.from_user.id):
        return
    if g["board"][pos] != EMPTY:
        return

    uid = q.from_user.id

    # FRIEND MODE
    if g["mode"] == "friend":
        if g["turn"] == X and uid != g["p1"]:
            return
        if g["turn"] == O and uid != g["p2"]:
            return

        g["board"][pos] = g["turn"]
        res = check(g["board"])

        if res in (X, O):
            g["finished"] = True
            winner_id = g["p1"] if res == X else g["p2"]
            winner_name = g["p1_name"] if res == X else g["p2_name"]
            await add_win(winner_id, winner_name)
            return await q.message.edit_text(
                f"🏆 <b>{winner_name} Wins!</b>",
                reply_markup=board_kb(gid, g["board"])
            )

        if res == "draw":
            g["finished"] = True
            return await q.message.edit_text(
                "🤝 <b>Match Draw!</b>",
                reply_markup=board_kb(gid, g["board"])
            )

        g["turn"] = O if g["turn"] == X else X

    # BOT MODE
    else:
        if uid != g["p1"]:
            return

        g["board"][pos] = X
        res = check(g["board"])

        if res == X:
            g["finished"] = True
            await add_win(g["p1"], g["p1_name"])
            return await q.message.edit_text(
                f"🏆 <b>{g['p1_name']} Wins!</b>",
                reply_markup=board_kb(gid, g["board"])
            )

        if res == "draw":
            g["finished"] = True
            return await q.message.edit_text(
                "🤝 <b>Match Draw!</b>",
                reply_markup=board_kb(gid, g["board"])
            )

        # BOT MOVE
        b = bot_move(g["board"])
        g["board"][b] = O
        res = check(g["board"])

        if res == O:
            g["finished"] = True
            return await q.message.edit_text(
                "🤖 <b>Bot Wins!</b>",
                reply_markup=board_kb(gid, g["board"])
            )

    await q.message.edit_text(
        f"❌ {g['p1_name']}\n⭕ {g['p2_name']}\n\n🔄 <b>Turn:</b> {g['turn']}",
        reply_markup=board_kb(gid, g["board"])
    )

# ───── REMATCH ─────

@app.on_callback_query(filters.regex("^xoxo_rematch:"))
async def rematch(_, q: CallbackQuery):
    gid = int(q.data.split(":")[1])
    g = games.get(gid)

    if not g or q.from_user.id not in (g["p1"], g["p2"]):
        return await q.answer("❌ Not allowed", show_alert=True)

    g["board"] = [EMPTY]*9
    g["turn"] = X
    g["finished"] = False

    await q.message.edit_text(
        f"🔁 <b>Rematch Started!</b>\n\n"
        f"❌ {g['p1_name']}\n"
        f"⭕ {g['p2_name']}\n\n"
        f"🔄 <b>Turn: ❌</b>",
        reply_markup=board_kb(gid, g["board"])
    )

# ───── END GAME ─────

@app.on_callback_query(filters.regex("^xoxo_end"))
async def end_game(_, q: CallbackQuery):
    games.pop(int(q.data.split(":")[1]), None)
    await q.message.edit_text("🛑 <b>Game Ended</b>")

# ───── FORCE END CMD ─────

@app.on_message(filters.command("endxoxo"))
async def endxoxo(_, m):
    g = games.get(m.chat.id)
    if not g:
        return await m.reply("❌ No active game.")
    if m.from_user.id not in (g["p1"], g["p2"]):
        return await m.reply("❌ You are not part of this game.")
    games.pop(m.chat.id)
    await m.reply("🛑 <b>Game Force Ended</b>")

# ───── LEADERBOARD ─────

@app.on_message(filters.command("xoxotop"))
async def leaderboard(_, m):
    text = "🏆 <b>XOXO Leaderboard</b>\n\n"
    i = 1
    async for u in db.find().sort("wins", -1).limit(10):
        text += f"{i}. <b>{u.get('name','Player')}</b> — {u['wins']} wins\n"
        i += 1
    await m.reply(text)
