# warzone.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from collections import defaultdict
import random

# =========================
# Storage
# =========================
games = {}  # {chat_id: {mode: game_data}}
leaderboards = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
# structure: leaderboards[chat_id][mode][user_id] = wins

# =========================
# Game settings
# =========================
MAX_PLAYERS = 6
STARTING_HP = 5
MODES = ["Battle Royale", "Shootout", "Zombie Survival", "Tank War", "Space Shooter", "Battle Cards"]

# =========================
# Start command
# =========================
@Client.on_message(filters.command("warzone") & filters.group)
async def start_warzone(client: Client, message: Message):
    chat_id = message.chat.id
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(mode, callback_data=f"warzone_mode:{mode}")] for mode in MODES]
    )
    await message.reply_text(
        "🔥 Welcome to Warzone Mini-Games! Choose a game mode:",
        reply_markup=keyboard
    )

# =========================
# Handle game mode selection
# =========================
@Client.on_callback_query()
async def warzone_callbacks(client: Client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user = callback_query.from_user
    data = callback_query.data

    # === Select mode ===
    if data.startswith("warzone_mode:"):
        mode = data.split(":")[1]
        if chat_id not in games:
            games[chat_id] = {}
        if mode in games[chat_id]:
            return await callback_query.answer("This game is already waiting for players!", show_alert=True)

        # Initialize game
        games[chat_id][mode] = {
            "players": [],
            "started": False,
            "hp": {},
            "round": 0
        }

        join_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ Join Game", callback_data=f"warzone_join:{mode}")]]
        )

        await callback_query.message.edit_text(
            f"🎮 {mode} started! Click ✅ Join Game to participate (max {MAX_PLAYERS} players).",
            reply_markup=join_button
        )
        await callback_query.answer()

    # === Join game ===
    elif data.startswith("warzone_join:"):
        mode = data.split(":")[1]
        if chat_id not in games or mode not in games[chat_id]:
            return await callback_query.answer("No such game active.", show_alert=True)

        game = games[chat_id][mode]

        if user.id in [p.id for p in game["players"]]:
            return await callback_query.answer("You already joined!", show_alert=True)
        if len(game["players"]) >= MAX_PLAYERS:
            return await callback_query.answer("Game is full!", show_alert=True)

        game["players"].append(user)
        game["hp"][user.id] = STARTING_HP

        if len(game["players"]) < 2:
            await callback_query.answer(f"{user.mention} joined! Waiting for more players...")
            await callback_query.message.edit_text(
                f"{mode} waiting for players...\n{len(game['players'])}/{MAX_PLAYERS} joined.",
                reply_markup=callback_query.message.reply_markup
            )
        else:
            # Start game
            game["started"] = True
            await start_warzone_round(client, chat_id, mode, callback_query.message)
        return

    # === In-game actions ===
    elif data.startswith("warzone_action:"):
        _, mode, action = data.split(":")
        if chat_id not in games or mode not in games[chat_id]:
            return await callback_query.answer("Game not active.", show_alert=True)

        game = games[chat_id][mode]
        user_id = user.id
        if user_id not in [p.id for p in game["players"]]:
            return await callback_query.answer("You are not in this game!", show_alert=True)
        if "actions" not in game:
            game["actions"] = {}
        if user_id in game["actions"]:
            return await callback_query.answer("You already acted this round!", show_alert=True)

        # Register action
        game["actions"][user_id] = action
        await callback_query.answer(f"You chose {action}")

        # Check if all players acted
        if len(game["actions"]) == len(game["players"]):
            await process_warzone_round(client, chat_id, mode, callback_query.message)
        return

# =========================
# Start round
# =========================
async def start_warzone_round(client, chat_id, mode, message):
    game = games[chat_id][mode]
    game["round"] += 1
    game["actions"] = {}

    hp_status = "\n".join([f"{p.mention}: {'❤️'*game['hp'][p.id]} ({game['hp'][p.id]})" for p in game["players"]])
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton(a, callback_data=f"warzone_action:{mode}:{a}") for a in ["Attack", "Defend", "Heal"]]]
    )
    await message.edit_text(
        f"⚔️ {mode} - Round {game['round']}\n\nPlayers HP:\n{hp_status}\n\nChoose your action:",
        reply_markup=buttons
    )

# =========================
# Process round actions
# =========================
async def process_warzone_round(client, chat_id, mode, message):
    game = games[chat_id][mode]
    results = []

    # Shuffle player order
    players = game["players"]
    random.shuffle(players)

    for p in players:
        action = game["actions"][p.id]
        if action == "Attack":
            # Attack random other player
            targets = [t for t in players if t.id != p.id and game["hp"][t.id] > 0]
            if targets:
                target = random.choice(targets)
                hit = random.random() < 0.7  # 70% success
                if hit:
                    game["hp"][target.id] -= 1
                    results.append(f"{p.mention} attacked {target.mention} ✅")
                else:
                    results.append(f"{p.mention} attacked {target.mention} ❌")
            else:
                results.append(f"{p.mention} tried to attack but no targets!")
        elif action == "Defend":
            results.append(f"{p.mention} defended 🛡️")
        elif action == "Heal":
            game["hp"][p.id] += 1
            results.append(f"{p.mention} healed ❤️")

    # Check for eliminated players
    alive_players = [p for p in players if game["hp"][p.id] > 0]

    # End game if 1 or 0 players left
    if len(alive_players) <= 1:
        text = "\n".join(results) + "\n\n"
        if alive_players:
            winner = alive_players[0]
            leaderboards[chat_id][mode][winner.id] += 1
            text += f"🏆 {winner.mention} wins the {mode}!"
        else:
            text += "No one survived! Game over."
        await message.edit_text(text, reply_markup=None)
        del games[chat_id][mode]
        return

    # Continue next round
    hp_status = "\n".join([f"{p.mention}: {'❤️'*game['hp'][p.id]} ({game['hp'][p.id]})" for p in alive_players])
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton(a, callback_data=f"warzone_action:{mode}:{a}") for a in ["Attack", "Defend", "Heal"]]]
    )
    await message.edit_text(
        f"⚔️ {mode} - Round {game['round']}\n\nResults:\n" + "\n".join(results) + "\n\nPlayers HP:\n" + hp_status + "\n\nChoose your next action:",
        reply_markup=buttons
    )
    # Update alive players
    game["players"] = alive_players

# =========================
# Leaderboard
# =========================
@Client.on_message(filters.command("warlead") & filters.group)
async def warzone_leaderboard(client: Client, message: Message):
    chat_id = message.chat.id
    if chat_id not in leaderboards:
        return await message.reply_text("No games played yet!")

    text = "🏆 Warzone Leaderboards 🏆\n\n"
    for mode in MODES:
        if mode in leaderboards[chat_id] and leaderboards[chat_id][mode]:
            text += f"**{mode}**\n"
            sorted_players = sorted(leaderboards[chat_id][mode].items(), key=lambda x: x[1], reverse=True)
            for idx, (user_id, wins) in enumerate(sorted_players[:10], 1):
                text += f"{idx}. [User](tg://user?id={user_id}) - {wins} wins\n"
            text += "\n"
    await message.reply_text(text, disable_web_page_preview=True)
