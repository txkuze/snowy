import re
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import ChatMemberStatus, ChatPermissions
from pyrogram.errors import ChatAdminRequired

# ==============================
# ⚠️ WARNING STORAGE (memory)
# ==============================

WARNINGS = {}

# ==============================
# 🔞 BAD WORDS LIST
# ==============================

BAD_WORDS = [
    "porn","masterstock","bchenchod","madarchod","bhenchod","bhenshok",
    "bhenstok","master","pussy","randi","bund","chut","dick","fuck",
    "gand","loda","nunu","lop","pom","bc","mc","maderchod",
    "motherfucker","bhosadike","betichod","chunni","chinaal",
    "chudai khana","chudan chuda","chut ka pujari","chut ka bhoot",
    "gaand ka makhan","gaand main lassan","gaand main danda",
    "gaand main keera","gaand mein bambu","gaandfat",
    "pote kitne bhi bade ho","lund ke niche hi rehte hai",
    "hazaar lund teri gaand main","jhat ke baal","jhaant ke pissu",
    "kadak mall","kali choot ke safaid jhaat","khotey ki aulda",
    "kutte ka awlat","kutte ki jat","kutte ke tatte","kutte ke poot",
    "teri maa ki choot","lavde ke bal","lund chus","lund ke pasine",
    "meri gand ka khatmal","moot","mootna","najayaz paidaish",
    "rundi khana","sadi hui gaand","teri gaand main kute ka lund",
    "teri maa ka bhosda","teri maa ki chut",
    "tere gaand mein keede paday",
    "banall","/banall",".banall",
    "bio","join my bio","join bio","join links from my bio"
]

# ==============================
# 🔎 TEXT NORMALIZER
# ==============================

def normalize_text(text: str):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)  # remove symbols
    text = re.sub(r'\s+', ' ', text)         # normalize spaces
    return text.strip()

# ==============================
# 🚨 DETECTION SYSTEM
# ==============================

def contains_bad_word(text: str):
    text = normalize_text(text)
    compact = text.replace(" ", "")

    for word in BAD_WORDS:
        clean_word = word.replace(" ", "")

        # Short word protection (avoid false positives)
        if len(clean_word) <= 2:
            pattern = r'\b' + re.escape(clean_word) + r'\b'
            if re.search(pattern, text):
                return True
        else:
            if clean_word in compact:
                return True

    return False

  #bio link 

def contains_link_or_username(text: str):
    text = text.lower()

    # Detect http/https links
    if re.search(r'https?://', text):
        return True

    # Detect telegram username mentions like @username
    if re.search(r'@\w{4,}', text):
        return True

    # Detect t.me links
    if "t.me/" in text:
        return True

    return False
  

# ==============================
# 🛡 MAIN HANDLER
# ==============================

def register_antiporn(app: Client):

    @app.on_message(filters.text & filters.group)
    async def anti_porn_handler(client: Client, message: Message):

        if not message.text:
            return

        if not contains_bad_word(message.text):
            return

        user_id = message.from_user.id
        chat_id = message.chat.id

        # Skip admins & owner
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return

        # Delete message
        try:
            await message.delete()
        except:
            pass

        # Increase warning
        WARNINGS[user_id] = WARNINGS.get(user_id, 0) + 1
        warn_count = WARNINGS[user_id]

        try:
            # 1️⃣ First offense → Warn
            if warn_count == 1:
                await message.reply_text(
                    "⚠️ Warning 1/3\nInappropriate language detected."
                )

            # 2️⃣ Second offense → 10 min mute
            elif warn_count == 2:
                await client.restrict_chat_member(
                    chat_id,
                    user_id,
                    ChatPermissions(),
                    until_date=datetime.now() + timedelta(minutes=10)
                )
                await message.reply_text(
                    "🔇 Warning 2/3\nUser muted for 10 minutes."
                )

            # 3️⃣ Third offense → Ban
            else:
                await client.ban_chat_member(chat_id, user_id)
                await message.reply_text(
                    "🚫 User banned for repeated abusive language."
                )

        except ChatAdminRequired:
            await message.reply_text(
                "❌ I need ban & restrict permissions to take action."
)
