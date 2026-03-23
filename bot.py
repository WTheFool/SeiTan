import discord
from discord.ext import commands
from website.keep_alive import keep_alive
import asyncio
import os

from dotenv import load_dotenv
load_dotenv()

import config
from database.db import init_db, cursor
from systems.ping_system import ping_loop
from systems.scheduler import sentence_loop
from systems.sentence_logic import justice_loop
from systems.message_listener import handle_message
from systems.ui_views import JoinAppealView

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f"SeiTan online as {bot.user}")
    
    # Start background loops
    bot.loop.create_task(ping_loop(bot))
    bot.loop.create_task(sentence_loop(bot))
    bot.loop.create_task(justice_loop(bot))

@bot.event
async def on_guild_join(guild):
    # Auto-create the #hell channel on join
    channel = discord.utils.get(guild.text_channels, name="hell")
    if not channel:
        await guild.create_text_channel("hell")

@bot.event
async def on_message(message):
    await handle_message(bot, message)
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    user_id = member.id
    guild_id = member.guild.id
    
    # Check if they are a sinner in THIS server
    cursor.execute("SELECT days_left FROM sentences WHERE user_id=? AND guild_id=?", (user_id, guild_id))
    row = cursor.fetchone()
    
    is_sinner_here = bool(row)
    
    if is_sinner_here:
        sinner_role = discord.utils.get(member.guild.roles, name="Sinner")
        if sinner_role:
            await member.add_roles(sinner_role)
            
        channel = discord.utils.get(member.guild.text_channels, name="hell")
        if channel:
            await channel.send(f"Welcome back, {member.mention}. Did you think escaping the server would save you?")
            
    else:
        # Check if Global Hell is enabled
        cursor.execute("SELECT global_hell FROM guild_settings WHERE guild_id=?", (guild_id,))
        setting_row = cursor.fetchone()
        
        if setting_row and setting_row[0] == 1:
            # Look for the worst active sentence across all servers for this user
            cursor.execute("SELECT days_left, mode, reason, guild_id FROM sentences WHERE user_id=? ORDER BY days_left DESC LIMIT 1", (user_id,))
            global_sinner = cursor.fetchone()
            
            if global_sinner:
                days_left, _, reason, origin_guild_id = global_sinner
                
                origin_guild = bot.get_guild(origin_guild_id)
                origin_name = origin_guild.name if origin_guild else f"Unknown Server ({origin_guild_id})"
                
                # Send the join appeal to a punisher-friendly channel. We default to #hell if it exists.
                channel = discord.utils.get(member.guild.text_channels, name="hell")
                if not channel:
                    channel = member.guild.text_channels[0] # Fallback to first channel if #hell not found yet
                    
                embed = discord.Embed(title="⚠️ GLOBAL HELL INTRUDER", description=f"{member.mention} has joined the server. They are currently serving a sentence in another realm.", color=discord.Color.dark_orange())
                embed.add_field(name="Sins", value=reason, inline=False)
                embed.add_field(name="Sentence Remaining", value=f"{days_left} days", inline=True)
                embed.add_field(name="Origin Server", value=origin_name, inline=True)
                
                view = JoinAppealView(user_id, days_left, reason, origin_guild_id, bot)
                
                await channel.send(embed=embed, view=view)

async def load():
    await bot.load_extension("systems.commands_punishment")
    await bot.load_extension("systems.commands_admin")
    await bot.load_extension("systems.commands_personality")
    await bot.load_extension("cogs.stats")


async def main():
    init_db()
    async with bot:
        await load()
        await bot.start(config.TOKEN)


if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
