import asyncio
import discord
from database.db import cursor
from systems.personality import pick_joke

async def ping_loop(bot):

    await bot.wait_until_ready()

    while not bot.is_closed():

        cursor.execute("SELECT user_id, guild_id FROM sentences")
        rows = cursor.fetchall()

        for user_id, guild_id in rows:

            guild = bot.get_guild(guild_id)
            if not guild:
                continue

            member = guild.get_member(user_id)
            channel = discord.utils.get(guild.text_channels, name="hell")

            if channel and member:
                joke = pick_joke(guild_id)
                await channel.send(
                    f"{member.mention} → {joke}"
                )

        await asyncio.sleep(28800)  # 8 hours = 3x per day
