from pyrogram import filters, enums
from pyrogram.types import ChatMemberUpdated
from Oneforall import app
from logging import getLogger

LOGGER = getLogger(__name__)

WELCOME_TEXT = """
⸻⬫⸺〈💖 𝐖ᴇʟᴄᴏᴍᴇ 𝐓ᴏ {group} 💖〉⸺⬫⸻

╭─────────༺✨༻────────╮
 🌸 ➻ 𝐍ᴀᴍᴇ        » {name}
 🆔 ➻ 𝐈ᴅ          » {id}
 🔖 ➻ 𝐔ꜱᴇʀɴᴀᴍᴇ   » {username}
 👥 ➻ 𝐓ᴏᴛᴀʟ 𝐌ᴇᴍʙᴇʀ𝐬 » {members}
╰─────────༺✨༻────────╯

🎉💫 𝐘ᴀʏ! 𝐘ᴏᴜ’ʀᴇ 𝐍ᴏᴡ 𝐏ᴀʀᴛ 𝐎ғ 𝐎ᴜʀ 𝐅ᴀᴍɪʟʏ 💫🎉
💗✨ 𝐄ɴᴊᴏʏ 𝐓ʜᴇ 𝐕ɪʙᴇ𝐬 • 𝐅ᴇᴇʟ 𝐓ʜᴇ 𝐌ᴜꜱɪᴄ ✨💗
"""

@app.on_chat_member_updated(filters.group, group=-3)
async def welcome_member(_, member: ChatMemberUpdated):
    # ❌ Ignore leaves / bans / restrictions
    if (
        not member.new_chat_member
        or member.new_chat_member.status
        in {enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED}
    ):
        return

    user = member.new_chat_member.user
    chat = member.chat

    try:
        members_count = await app.get_chat_members_count(chat.id)
    except Exception:
        members_count = "—"

    name = user.first_name or "Unknown"
    username = f"@{user.username}" if user.username else "None"

    text = WELCOME_TEXT.format(
        group=chat.title or "This Group",
        name=name,
        id=user.id,
        username=username,
        members=members_count,
    )

    try:
        await app.send_message(
            chat.id,
            text,
            disable_web_page_preview=True
        )
    except Exception as e:
        LOGGER.error(e)
