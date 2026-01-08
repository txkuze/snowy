import random
import requests
from pyrogram import filters
from pyrogram.enums import PollType
from Oneforall import app

print("🧠 LOADING QUIZ...")

@app.on_message(filters.command("quiz"))
async def quiz(client, message):
    print("🧠 /quiz command received!")  # Debug
    
    await message.reply("🧠 **Quiz loading...**")
    
    try:
        # Simple API call
        url = "https://opentdb.com/api.php?amount=1&category=9&type=multiple"
        data = requests.get(url).json()["results"][0]
        
        question = data["question"]
        correct = data["correct_answer"]
        incorrect = data["incorrect_answers"]
        answers = incorrect + [correct]
        random.shuffle(answers)
        correct_id = answers.index(correct)
        
        await app.send_poll(
            chat_id=message.chat.id,
            question=f"🧠 **QUIZ!**

{question}",
            options=answers,
            is_anonymous=False,
            type=PollType.QUIZ,
            correct_option_id=correct_id
        )
        print("✅ Quiz sent successfully!")
        await message.delete()
        
    except Exception as e:
        print(f"❌ Quiz error: {e}")
        await message.edit(f"❌ Error: {e}")

print("✅ QUIZ LOADED - /quiz should work NOW!")
