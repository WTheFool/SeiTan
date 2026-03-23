import discord
from systems.phrase_engine import validate_phrase
from systems.cycle_engine import record_response, process_cycle
from systems.sentence_logic import apply_sentence_effect
from systems.anti_spam import can_ping
from database.db import cursor, conn
from database.db_methods import SettingsDB, SentencesDB

async def handle_message(bot, message):

    if message.author.bot:
        return

    guild = message.guild
    if not guild:
        return

    # Skip commands
    if message.content.startswith("!"):
        return

    # ONLY #HELL COUNTS
    if message.channel.name != "hell":
        return

    user_id = message.author.id
    guild_id = guild.id

    # check if user is actually sentenced
    row = SentencesDB.get_sentence(user_id, guild_id)
    if not row:
        return

    days_left, _, mode = row
    
    # ensure active cycle
    cursor.execute("SELECT pending FROM cycle_state WHERE user_id=? AND guild_id=?", (user_id, guild_id))
    state_row = cursor.fetchone()
    if not state_row or state_row[0] == 0:
        return

    # validate phrase
    valid = validate_phrase(guild_id, message.content)

    if valid:

        record_response(user_id, guild_id)

        result = process_cycle(user_id, guild_id, mode=mode)

        apply_sentence_effect(user_id, guild_id, mode, result)

        await message.channel.send("✔ Accepted. The cycle continues.")

        # Check if sentence is over (days_left <= 0)
        check_row = SentencesDB.get_sentence(user_id, guild_id)
        if check_row and check_row[0] <= 0:
            sinner_role = discord.utils.get(guild.roles, name="Sinner")
            repented_role = discord.utils.get(guild.roles, name="Repented")
            if not repented_role:
                repented_role = await guild.create_role(name="Repented", color=discord.Color.light_grey())
                
            if sinner_role in message.author.roles:
                await message.author.remove_roles(sinner_role)
                
            await message.author.add_roles(repented_role)
            await message.channel.send(f"{message.author.mention} has fully repented and is free to leave #HELL.")
            
            is_global = SettingsDB.is_global_hell(guild_id)
            SentencesDB.delete_sentence(user_id, guild_id, is_global)
    else:
        await message.channel.send("❌ Incorrect phrase.")
