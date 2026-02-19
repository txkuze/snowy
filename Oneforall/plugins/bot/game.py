from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Oneforall import app
import re

# small caps map
SMALL_CAPS = str.maketrans({
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ",
    "f": "ғ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ",
    "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ",
    "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ",
    "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ",
    "z": "ᴢ"
})

def style_text(text: str) -> str:
    lines = text.split("\n")
    output = []

    for line in lines:
        # keep links and commands untouched
        if re.search(r"(https?://\S+|/\w+)", line):
            output.append("> " + line)
        else:
            output.append("> " + line.lower().translate(SMALL_CAPS))

    return "\n".join(output)

@app.on_callback_query(filters.regex("^games_menu$"))
async def games_menu(_, query):
    # loading state hatane ke liye
    await query.answer()

    raw_text = (
        "🎮 ᴀᴠᴀɪʟᴀʙʟᴇ ɢᴀᴍᴇs\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎯 ʜᴏᴡ ᴛᴏ ᴘʟᴀʏ\n\n"
        "➤ ᴜsᴇ /ɢᴀᴍᴇ ᴄᴏᴍᴍᴀɴᴅ\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🕹️ ɢᴀᴍᴇs ʟɪsᴛ\n\n"
        "① ᴛɪᴄ ᴛᴀᴄ ᴛᴏᴇ\n"
        "➤ ᴄʟᴀssɪᴄ ② ᴘʟᴀʏᴇʀ ɢᴀᴍᴇ\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ ᴍᴏʀᴇ ɢᴀᴍᴇs ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ sᴏᴏɴ\n"
        "✨ ᴇᴀᴄʜ ɢᴀᴍᴇ ɪs ᴄᴀʀᴇғᴜʟʟʏ ᴅᴇsɪɢɴᴇᴅ\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🥀 ᴀʟʟ ᴄʀᴇᴅɪᴛs ɢᴏ ᴛᴏ ᴍʏ ᴅᴇᴠᴇʟᴏᴘᴇʀ\n"
        "[✦ ʀᴏᴏʜɪ ❕](https://t.me/roohi_queen_bot)"
    )

    await query.message.edit_text(
        raw_text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔙 Back", callback_data="mbot_cb")]
            ]
        ),
        disable_web_page_preview=True
    )
