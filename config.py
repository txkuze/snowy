import os
import re
from os import getenv

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from pyrogram import filters

# ===== BASIC CONFIG (REHNE DO) =====

API_ID = int(getenv("API_ID", "26950458"))
API_HASH = getenv("API_HASH", "d818b8d530e4a9b209509815ab1b9c7c")

UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/txkuze/snowy",
)
BOT_TOKEN = getenv("BOT_TOKEN", "")
OPENAI_API_KEY = getenv("OPENAI_API_KEY")

MONGO_DB_URI = getenv(
    "MONGO_DB_URI",
    "mongodb+srv://knight4563:knight4563@cluster0.a5br0se.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

MUSIC_BOT_NAME = getenv("MUSIC_BOT_NAME", "Infinity_X_Destiny_Bot")
PRIVATE_BOT_MODE = getenv("PRIVATE_BOT_MODE", None)

DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 100000))

# ===== LOGGER (REHNE DO) =====

LOGGER_ID = int(getenv("LOGGER_ID", "-1002869205475"))
GBAN_LOG_CHAT = int(getenv("GBAN_LOG_CHAT", "-1002869205475"))

OWNER_ID = getenv("OWNER_ID", "7487670897")
SUDO_USERS = getenv("SUDO_USERS", "7487670897")

# ===== HEROKU (AUTO WORK) =====

HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

# ===== SUPPORT =====

SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/dark_musictm")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/cuties_logs")

# ===== IMAGES (REHNE DO BHAI 😄) =====

START_IMG_URL = getenv("START_IMG_URL", "https://graph.org/file/7c703f3d157b477bd5879-4463312df2304b779f.jpg")
PING_IMG_URL = START_IMG_URL
PLAYLIST_IMG_URL = START_IMG_URL
STATS_IMG_URL = START_IMG_URL
TELEGRAM_AUDIO_URL = START_IMG_URL
TELEGRAM_VIDEO_URL = START_IMG_URL
STREAM_IMG_URL = START_IMG_URL
SOUNCLOUD_IMG_URL = START_IMG_URL
YOUTUBE_IMG_URL = START_IMG_URL
SPOTIFY_ARTIST_IMG_URL = START_IMG_URL
SPOTIFY_ALBUM_IMG_URL = START_IMG_URL
SPOTIFY_PLAYLIST_IMG_URL = START_IMG_URL

# ===== FUNCTIONS =====

def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))

DURATION_LIMIT = time_to_seconds(f"{DURATION_LIMIT_MIN}:00")

# ===== VALIDATION =====

if SUPPORT_CHANNEL and not re.match(r"^https?://", SUPPORT_CHANNEL):
    raise SystemExit("SUPPORT_CHANNEL must start with https://")

if SUPPORT_CHAT and not re.match(r"^https?://", SUPPORT_CHAT):
    raise SystemExit("SUPPORT_CHAT must start with https://")

# ===== OTHERS =====

BANNED_USERS = filters.user()
TEMP_DB_FOLDER = "tempdb"
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}
