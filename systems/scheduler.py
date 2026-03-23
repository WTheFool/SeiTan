import asyncio
from database.db import cursor, conn
from systems.sentences import decrement_day
import discord


async def sentence_loop(bot):

    await bot.wait_until_ready()

    while not bot.is_closed():

        cursor.execute("SELECT user_id, guild_id FROM sentences")
        rows = cursor.fetchall()

        for user_id, guild_id in rows:

            guild = bot.get_guild(guild_id)
            if not guild:
                continue

            member = guild.get_member(user_id)
            if not member:
                continue

            channel = discord.utils.get(guild.text_channels, name="hell")

            cursor.execute("""
            SELECT days_left FROM sentences
            WHERE user_id=? AND guild_id=?
            """, (user_id, guild_id))

            row = cursor.fetchone()
            if not row:
                continue
                
            days = row[0]

            if days <= 0:
                sinner_role = discord.utils.get(guild.roles, name="Sinner")
                repented_role = discord.utils.get(guild.roles, name="Repented")
                if sinner_role in member.roles:
                    await member.remove_roles(sinner_role)
                if repented_role:
                    await member.add_roles(repented_role)

                if channel:
                    await channel.send(f"{member.mention} has repented.")
                    
                cursor.execute("DELETE FROM sentences WHERE user_id=? AND guild_id=?", (user_id, guild_id))
                conn.commit()

        await asyncio.sleep(86400)  # 1 day cycle
