import asyncio
import discord
import time

from database.db import cursor, conn
from systems.cycle_engine import start_cycle, process_cycle
from systems.anti_spam import can_ping
from systems.phrase_engine import get_random_phrase
from database.db_methods import SettingsDB, SentencesDB, CooldownDB

def apply_sentence_effect(user_id, guild_id, mode, result):
    row = SentencesDB.get_sentence(user_id, guild_id)
    if not row:
        return
        
    days_left, original_days, _ = row
    
    if result == "success":
        # Check global cooldown to prevent double reductions across servers
        is_global = SettingsDB.is_global_hell(guild_id)
        
        if is_global:
            last_reduction = CooldownDB.get_global_reduction_cooldown(user_id)
            now = time.time()
            if last_reduction:
                if now - last_reduction < 86400: # Less than a day
                    return # Don't reduce, already reduced today globally
                    
            CooldownDB.set_global_reduction_cooldown(user_id, now)

        new_days = days_left - 1
        SentencesDB.update_days(user_id, guild_id, new_days, is_global)
        return
            
    elif result == "fail":
        if mode == "incremental":
            new_days = days_left + 1
        elif mode == "consecutive":
            new_days = original_days
        else: # default
            new_days = days_left
    else:
        new_days = days_left
        
    # Prevent negative values just in case
    if new_days < 0:
        new_days = 0
            
    if result == "fail":
        SentencesDB.update_days(user_id, guild_id, new_days, False)


async def justice_loop(bot):

    await bot.wait_until_ready()

    while not bot.is_closed():

        # We must check days_left > 0 to avoid continuing counting when it shouldn't
        rows = SentencesDB.get_all_active_sentences()

        for user_id, guild_id, mode in rows:

            guild = bot.get_guild(guild_id)
            if not guild:
                continue

            member = guild.get_member(user_id)
            if not member:
                continue

            channel = discord.utils.get(guild.text_channels, name="hell")
            if not channel:
                continue

            # PROCESS RESULT (from previous cycle)
            result = process_cycle(user_id, guild_id, mode=mode)
            if result and result != "no_active_cycle":
                apply_sentence_effect(user_id, guild_id, mode, result)

            # Re-check days_left after applying effect before starting new cycle
            chk = SentencesDB.get_sentence(user_id, guild_id)
            if chk and chk[0] > 0:
                # START NEW CYCLE
                start_cycle(user_id, guild_id)

                if can_ping(user_id):
                    phrase = get_random_phrase(guild_id)
                    await channel.send(f"{member.mention} say -> \"{phrase}\"")
                    await asyncio.sleep(10)  # Stagger pings to avoid spamming

        await asyncio.sleep(86400)  # 1 cycle per day
