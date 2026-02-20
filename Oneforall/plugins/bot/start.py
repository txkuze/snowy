import time
import asyncio
import random

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from youtubesearchpython.__future__ import VideosSearch

import config
from config import BANNED_USERS
from Oneforall import app
from Oneforall.misc import _boot_
from Oneforall.plugins.sudo.sudoers import sudoers_list
from Oneforall.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from Oneforall.utils.decorators.language import LanguageStart
from Oneforall.utils.formatters import get_readable_time
from Oneforall.utils.inline import help_pannel, private_panel, start_panel
from strings import get_string
from Oneforall.misc import SUDOERS

# ==============================
# 🔒 FORCE SUB CHANNELS
# ==============================

FORCE_CHANNEL_1 = config.FORCE_CHANNEL_1
FORCE_CHANNEL_2 = config.FORCE_CHANNEL_2

STICKER = [
    "CAACAgUAAxkBAAEQEGVpSR-TuCKHP8D69SvDAAH2Gn7QjXEAAtIEAAKP9uhXzLPwoqMKxuQ2BA",
    "CAACAgUAAxkBAAEQEGVpSR-TuCKHP8D69SvDAAH2Gn7QjXEAAtIEAAKP9uhXzLPwoqMKxuQ2BA",
    "CAACAgUAAxkBAAEQEGVpSR-TuCKHP8D69SvDAAH2Gn7QjXEAAtIEAAKP9uhXzLPwoqMKxuQ2BA",
]

EMOJIOS = ["🚩", "🥀", "🪄", "🩷", "⚡", "❤️‍🩹", "🩶", "🩵", "💜", "🕊"]


# ==============================
# 🔒 FORCE SUB CHECK FUNCTION
# ==============================

async def force_sub_check(message: Message):
    try:
        user_id = message.from_user.id

        member1 = await app.get_chat_member(f"@{FORCE_CHANNEL_1}", user_id)
        member2 = await app.get_chat_member(f"@{FORCE_CHANNEL_2}", user_id)

        if member1.status in ["left", "kicked"] or member2.status in ["left", "kicked"]:

            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⁠・ᴊσɪη ᴄʜᴧηηєʟ 1 📢✨",
                            url=f"https://t.me/{FORCE_CHANNEL_1}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⁠・ᴊσɪη ᴄʜᴧηηєʟ 1 📢✨",
                            url=f"https://t.me/{FORCE_CHANNEL_2}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⁠・ᴊσɪηєᴅ ✅✨",
                            callback_data="check_sub"
                        )
                    ]
                ]
            )

            await message.reply_photo(
                photo=config.START_IMG_URL,
                caption="✦ᴀᴄᴄєss ᴅєηɪєᴅ ❌\n❍📜ʏσᴜ ᴍᴜsᴛ ᴊσɪη ʙσᴛʜ ᴄʜᴧηηєʟs ᴛσ ᴜsє ᴛʜɪs ʙσᴛ 🔒✨",
                reply_markup=buttons
            )
            return True

    except Exception as e:
        print(e)

    return False


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):

    # 🔒 Force Join Check
    if await force_sub_check(message):
        return

    await add_served_user(message.from_user.id)
    await message.react("❤")

    accha = await message.reply_text(text=random.choice(EMOJIOS))
    await asyncio.sleep(1.3)
    await accha.edit("🏓..ᴍᴇᴇɴʏ..ᴍɪɴʏ..ᴍᴏᴇ✨")
    await asyncio.sleep(0.2)
    await accha.edit("_.ᴍᴇᴇɴʏ__ ꨄ︎ sтαятιиg..__")
    await asyncio.sleep(0.2)
    await accha.edit("__.ʜєʟʟσ ʜσω ᴧʀє ʏσᴜ 🩷 .__")
    await asyncio.sleep(0.2)
    await accha.delete()

    umm = await message.reply_sticker(sticker=random.choice(STICKER))
    await asyncio.sleep(2)
    await umm.delete()

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name[0:4] == "help":
            keyboard = help_pannel(_)
            return await message.reply_photo(
                photo=config.START_IMG_URL,
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
                has_spoiler=True,
            )

        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
            return

        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]

            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )

            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="˹ ɪɴꜰɪɴɪᴛʏ ✘ ɴᴇᴛᴡᴏʀᴋ˼ 🎧",
                            url="https://t.me/dark_musictm"
                        ),
                        InlineKeyboardButton(
                            text=_["S_B_9"],
                            url=config.SUPPORT_CHAT
                        ),
                    ],
                ]
            )

            await m.delete()
            await app.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=searched_text,
                reply_markup=key,
            )

            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )

    else:
        out = private_panel(_)
        await message.reply_photo(
            photo=config.START_IMG_URL,
            caption=_["start_2"].format(message.from_user.mention, app.mention),
            reply_markup=InlineKeyboardMarkup(out),
            has_spoiler=True,
        )

        if await is_on_off(2):
            return await app.send_message(
                chat_id=config.LOGGER_ID,
                text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
            )


# ==============================
# 🔁 CALLBACK CHECK
# ==============================

@app.on_callback_query(filters.regex("check_sub"))
async def check_subscription(client, callback_query: CallbackQuery):

    user_id = callback_query.from_user.id

    try:
        member1 = await app.get_chat_member(f"@{FORCE_CHANNEL_1}", user_id)
        member2 = await app.get_chat_member(f"@{FORCE_CHANNEL_2}", user_id)

        if member1.status not in ["left", "kicked"] and member2.status not in ["left", "kicked"]:
            await callback_query.message.delete()
            await callback_query.message.reply_text("✅ Subscription Verified!\n\nNow send /start again.")
        else:
            await callback_query.answer("❌ You have not joined both channels!", show_alert=True)

    except Exception as e:
        print(e)
