import asyncio
import os
from datetime import timedelta

import discord

DEFAULT_NAME = os.getenv("DEFAULT_NAME") or "JD"
EMOTE = os.getenv("EMOTE") or ":feed_jd:"


async def handle_adoption(bot, message: discord.Message) -> None:
    user_id = message.author.id
    if user_id in bot.adoption_in_progress:
        return

    bot.adoption_in_progress.add(user_id)
    try:
        def check_name(dm_message: discord.Message) -> bool:
            return dm_message.author == message.author and dm_message.channel == message.author.dm_channel

        def check_confirmation(dm_message: discord.Message) -> bool:
            return (
                dm_message.author == message.author
                and dm_message.channel == message.author.dm_channel
                and dm_message.content.lower() in ["yes", "no"]
            )

        while True:
            await message.author.send(
                f"{message.author.mention}, what would you like to name your JD?"
            )

            try:
                name_msg = await bot.wait_for("message", check=check_name, timeout=60.0)
            except asyncio.TimeoutError:
                return

            proposed_name = name_msg.content.strip()
            await message.author.send(
                f"Would you like to name your JD '{proposed_name}'? (reply with 'yes' or 'no')"
            )

            try:
                reaction_msg = await bot.wait_for("message", check=check_confirmation, timeout=60.0)
            except asyncio.TimeoutError:
                return

            if reaction_msg.content.lower() == "yes":
                jd_name = proposed_name or DEFAULT_NAME
                break

        user_id_str = bot.user_key(message.author.id)
        bot.jd_data[user_id_str] = {
            "name": jd_name,
            "creation_time": bot.iso(bot.now()),
            "last_fed": bot.iso(bot.now() - timedelta(days=1)),  # allow immediate feeding
            "total_feedings": 0,
            "dead": False,
        }
        bot.save_data()
        await message.channel.send(
            f"{message.author.mention} has adopted a new JD named '{jd_name}'! Don't forget to feed him! {EMOTE}"
        )
    finally:
        bot.adoption_in_progress.discard(user_id)
