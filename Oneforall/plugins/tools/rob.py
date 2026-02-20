from Oneforall import user_collection
from pyrogram import filters
from pyrogram.types import Message
import random


@bot.on_message(filters.command("rob"))
async def rob_cmd(_, message: Message):
    # Must reply to someone
    if not message.reply_to_message:
        return await message.reply(
            "❗ **Reply to a user!**\n\n"
            "Usage: `/rob [amount]`\n"
            "Example: `/rob 500` (reply to user with 500 amount)"
        )

    target = message.reply_to_message.from_user
    robber = message.from_user

    # Can't rob yourself
    if target.id == robber.id:
        return await message.reply("❌ **You can't rob yourself!**")

    # Amount required
    if len(message.command) < 2:
        return await message.reply(
            "❗ **Enter amount!**\n\n"
            "Usage: `/rob [amount]`"
        )

    try:
        amount = int(message.command[1])
    except ValueError:
        return await message.reply("❗ **Enter a valid number!**")

    if amount < 1:
        return await message.reply("❌ **Amount must be at least 1!**")

    if amount > 100000:
        return await message.reply("⚠️ **Maximum amount is 100000!**")

    # Fetch robber data
    robber_data = await user_collection.find_one({"id": robber.id})
    if not robber_data:
        robber_data = {"id": robber.id, "balance": 0, "lockbalance": False}
        await user_collection.insert_one(robber_data)
        robber_data = await user_collection.find_one({"id": robber.id})

    # Fetch target data
    target_data = await user_collection.find_one({"id": target.id})
    if not target_data:
        target_data = {"id": target.id, "balance": 0, "lockbalance": False}
        await user_collection.insert_one(target_data)
        target_data = await user_collection.find_one({"id": target.id})

    # Get balances
    robber_balance = robber_data.get("balance", 0)
    target_balance = target_data.get("balance", 0)

    # Check if target's balance is locked
    if target_data.get("lockbalance", False):
        return await message.reply(
            f"🔒 **{target.first_name}**'s balance is locked!\n"
            f"You can't rob them!"
        )

    # Check if target has enough balance
    if target_balance < amount:
        return await message.reply(
            f"😅 **{target.first_name}** has only **${target_balance}**.\n"
            f"Ask for less amount!"
        )

    # Rob success/fail chance (50% each)
    success = random.randint(1, 100)

    if success <= 50:
        # SUCCESS — transfer money
        await user_collection.update_one(
            {"id": target.id},
            {"$inc": {"balance": -amount}}
        )
        await user_collection.update_one(
            {"id": robber.id},
            {"$inc": {"balance": amount}}
        )

        new_robber_balance = robber_balance + amount
        new_target_balance = target_balance - amount

        return await message.reply(
            f"💰 **Robbery Successful!**\n\n"
            f"👤 **Robber:** {robber.first_name}\n"
            f"🎯 **Victim:** {target.first_name}\n"
            f"💵 **Amount:** ${amount}\n\n"
            f"📊 **New Balances:**\n"
            f"• {robber.first_name}: **${new_robber_balance}**\n"
            f"• {target.first_name}: **${new_target_balance}**"
        )

    else:
        # FAIL — robber pays fine (30%)
        fine = int(amount * 0.30)

        # Check if robber can pay fine
        if robber_balance < fine:
            return await message.reply(
                f"🚨 **Robbery Failed!**\n\n"
                f"You need **${fine}** to pay the penalty,\n"
                f"but you only have **${robber_balance}**!"
            )

        await user_collection.update_one(
            {"id": robber.id},
            {"$inc": {"balance": -fine}}
        )
        await user_collection.update_one(
            {"id": target.id},
            {"$inc": {"balance": fine}}
        )

        new_robber_balance = robber_balance - fine
        new_target_balance = target_balance + fine

        return await message.reply(
            f"🚨 **Robbery Failed!**\n\n"
            f"👤 **Robber:** {robber.first_name}\n"
            f"🎯 **Victim:** {target.first_name}\n"
            f"💸 **Fine:** ${fine} (30% of amount)\n\n"
            f"📊 **New Balances:**\n"
            f"• {robber.first_name}: **${new_robber_balance}**\n"
            f"• {target.first_name}: **${new_target_balance}**"
        )


@bot.on_message(filters.command("unlockbalance"))
async def unlock_balance_cmd(_, message: Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})

    # Create account if not exists
    if not user:
        new_user = {"id": user_id, "balance": 0, "lockbalance": False}
        await user_collection.insert_one(new_user)
        user = await user_collection.find_one({"id": user_id})

    # Check if already unlocked
    if not user.get("lockbalance", False):
        return await message.reply("🔓 **Your balance is already unlocked!**")

    # Unlock balance
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"lockbalance": False}}
    )

    await message.reply("🔓 **Your balance has been unlocked!**")


@bot.on_message(filters.command("lockbalance"))
async def lock_balance_cmd(_, message: Message):
    user_id = message.from_user.id
    user = await user_collection.find_one({"id": user_id})

    # Create account if not exists
    if not user:
        new_user = {"id": user_id, "balance": 0, "lockbalance": False}
        await user_collection.insert_one(new_user)
        user = await user_collection.find_one({"id": user_id})

    # Check if already locked
    if user.get("lockbalance", False):
        return await message.reply("🔒 **Your balance is already locked!**")

    # Lock balance
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"lockbalance": True}}
    )

    await message.reply("🔒 **Your balance has been locked!**")
