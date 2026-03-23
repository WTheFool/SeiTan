import discord
from discord.ext import commands
from website.keep_alive import keep_alive  # Ensure keep_alive.py is in a folder named 'website'
import asyncio
import os

# Your custom imports
import config
from database.db import init_db, cursor
from systems.ping_system import ping_loop
from systems.scheduler import sentence_loop
from systems.sentence_logic import justice_loop
from systems.message_listener import handle_message
from systems.sentences import assign_sentence

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Initialize Bot using the prefix from your config.py
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
    # Handle custom message logic
    await handle_message(bot, message)
    # Process standard commands
    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    user_id = member.id
    guild_id = member.guild.id

    # Check if they are a sinner in THIS server
    cursor.execute("SELECT days_left FROM sentences WHERE user_id=? AND guild_id=?", (user_id, guild_id))
    row = cursor.fetchone()

    if row:
        sinner_role = discord.utils.get(member.guild.roles, name="Sinner")
        if sinner_role:
            await member.add_roles(sinner_role)

        channel = discord.utils.get(member.guild.text_channels, name="hell")
        if channel:
            await channel.send(f"Welcome back, {member.mention}. Did you think escaping would save you?")

    else:
        # Check if Global Hell is enabled
        cursor.execute("SELECT global_hell FROM guild_settings WHERE guild_id=?", (guild_id,))
        setting_row = cursor.fetchone()

        if setting_row and setting_row[0] == 1:
            # Check if they are a sinner ANYWHERE else
            cursor.execute("SELECT days_left, mode FROM sentences WHERE user_id=? LIMIT 1", (user_id,))
            global_sinner = cursor.fetchone()

            if global_sinner:
                days_left, mode = global_sinner
                assign_sentence(user_id, guild_id, days_left, mode)

                sinner_role = discord.utils.get(member.guild.roles, name="Sinner")
                if not sinner_role:
                    sinner_role = await member.guild.create_role(name="Sinner", color=discord.Color.dark_red())

                await member.add_roles(sinner_role)

                channel = discord.utils.get(member.guild.text_channels, name="hell")
                if not channel:
                    channel = await member.guild.create_text_channel("hell")

                await channel.send(f"🌍 {member.mention} has arrived. Their sins followed them into Global Hell.")


async def load():
    # Load your extensions/cogs
    await bot.load_extension("systems.commands_punishment")
    await bot.load_extension("systems.commands_admin")
    await bot.load_extension("systems.commands_personality")
    await bot.load_extension("cogs.stats")


async def main():
    # Initialize the database
    init_db()

    async with bot:
        # Load extensions
        await load()

        # Start the bot using the TOKEN from config.py
        # (Which pulls from Render's Environment Variable 'DISCORD_TOKEN')
        if not config.TOKEN:
            print("CRITICAL ERROR: 'DISCORD_TOKEN' not found in Environment Variables!")
            return

        await bot.start(config.TOKEN)


if __name__ == "__main__":
    # 1. Start the Flask server (runs in a separate thread)
    # This keeps Render happy by responding to its "Health Check"
    keep_alive()

    # 2. Start the Discord Bot main loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutting down...")