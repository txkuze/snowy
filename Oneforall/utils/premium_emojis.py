from pyrogram.types import MessageEntity

# ==========================================
# 🔥 PREMIUM EMOJI STORAGE
# Replace IDs with real custom_emoji_id
# ==========================================

PREMIUM_EMOJIS = {

    # Love & Heart
    "heart_red": "REPLACE_ID",
    "heart_pink": "REPLACE_ID",
    "heart_fire": "REPLACE_ID",

    # Sparkles & Magic
    "sparkle": "REPLACE_ID",
    "magic": "REPLACE_ID",
    "fairy": "REPLACE_ID",

    # Fire & Energy
    "fire": "REPLACE_ID",
    "bolt": "REPLACE_ID",
    "rocket": "REPLACE_ID",

    # Music Related
    "music_note": "REPLACE_ID",
    "headphones": "REPLACE_ID",
    "vinyl": "REPLACE_ID",

    # Premium Style Emojis
    "crown": "REPLACE_ID",
    "diamond": "REPLACE_ID",
    "star_glow": "REPLACE_ID",

    # Admin / Owner Style
    "shield": "REPLACE_ID",
    "verified": "REPLACE_ID",
    "king": "REPLACE_ID",

}

# ==========================================
# 🔥 Helper Function
# ==========================================

def premium_emoji(name: str, offset: int):
    """
    Returns MessageEntity for premium emoji
    """

    if name not in PREMIUM_EMOJIS:
        raise ValueError(f"Premium emoji '{name}' not found!")

    return MessageEntity(
        type="custom_emoji",
        offset=offset,
        length=1,
        custom_emoji_id=PREMIUM_EMOJIS[name]
    )


# ==========================================
# 🔥 Auto Inject Function
# ==========================================

def inject_premium(text: str, emoji_name: str):
    """
    Adds premium emoji at beginning of text
    """

    full_text = " " + text

    entity = premium_emoji(emoji_name, offset=0)

    return full_text, [entity]
