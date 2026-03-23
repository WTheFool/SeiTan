import discord
from discord.ext import commands
import time
import math
import random
import sqlite3

from systems.permissions import is_admin
from database.db import cursor, conn
from systems.sentences import assign_sentence
from systems.personality import pick_phrase
from systems.safety import check_cooldown
from systems.ui_views import AppealView
from database.db_methods import SettingsDB, SentencesDB, CooldownDB

DEFAULT_MOCKS = [
    "The gods are deaf to you right now.",
    "Did you really think it would be that easy?",
    "Your suffering is entertaining. Keep waiting.",
    "Patience is a virtue you clearly lack.",
    "Scream all you want. Nobody is listening."
]

def get_mocks(guild_id):
    cursor.execute("SELECT text FROM mocks WHERE guild_id=?", (guild_id,))
    rows = cursor.fetchall()
    return [r[0] for r in rows] if rows else DEFAULT_MOCKS


class Punishment(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        
        # Ensure tables exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appeal_cooldowns (
            user_id INTEGER PRIMARY KEY,
            last_appeal REAL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mocks (
            guild_id INTEGER,
            text TEXT
        )
        """)
        conn.commit()

    def check(self, ctx):
        # We also want to let the server owner bypass, even if there's a bug in is_admin
        if ctx.guild.owner_id == ctx.author.id:
            return True
        return is_admin(ctx.author, ctx.guild)

    @commands.group(invoke_without_command=True)
    async def seitan(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Usage: !seitan help")

    @seitan.command(name="go")
    async def seitan_go(self, ctx, to: str, hell: str, member: discord.Member, days: int, mode: str, *, reason: str = "No reason provided."):
        if to.lower() != "to" or hell.lower() != "hell":
            return await ctx.send("Usage: !seitan go to hell <@user> <days> <mode> [reason]")

        if not self.check(ctx):
            return await ctx.send("No permission.")

        channel = discord.utils.get(ctx.guild.text_channels, name="hell")
        if not channel:
            channel = await ctx.guild.create_text_channel("hell")

        sinner_role = discord.utils.get(ctx.guild.roles, name="Sinner")
        if not sinner_role:
            # Create the role if it doesn't exist and restrict permissions
            sinner_role = await ctx.guild.create_role(name="Sinner", color=discord.Color.dark_red())
            for c in ctx.guild.channels:
                try:
                    await c.set_permissions(sinner_role, read_messages=False, send_messages=False)
                except discord.Forbidden:
                    pass
            # ensure they can read/write in #hell
            try:
                await channel.set_permissions(sinner_role, read_messages=True, send_messages=True)
            except discord.Forbidden:
                pass

        # Remove Repented role if they have it
        repented_role = discord.utils.get(ctx.guild.roles, name="Repented")
        if repented_role and repented_role in member.roles:
            await member.remove_roles(repented_role)

        await member.add_roles(sinner_role)

        # Assigning sentence with reason
        assign_sentence(member.id, ctx.guild.id, days, mode, reason)

        await channel.send(
            f"☠️ {member.mention} sent to HELL\n"
            f"Reason: {reason}\n"
            f"Phrase: {pick_phrase(ctx.guild.id)}"
        )
        
    @seitan.command(name="sins")
    async def seitan_sins(self, ctx, member: discord.Member):
        if not self.check(ctx):
            return await ctx.send("No permission.")
            
        cursor.execute("SELECT reason, guild_id FROM sentences WHERE user_id=?", (member.id,))
        row = cursor.fetchone()
        
        if not row:
            return await ctx.send(f"{member.display_name} is pure... for now.")
            
        reason, origin_guild_id = row
        origin_guild = self.bot.get_guild(origin_guild_id)
        origin_name = origin_guild.name if origin_guild else f"Unknown Server ({origin_guild_id})"
        
        embed = discord.Embed(title=f"The Sins of {member.display_name}", color=discord.Color.dark_red())
        embed.add_field(name="Reason for Punishment", value=reason, inline=False)
        embed.set_footer(text=f"Condemned by: {origin_name}")
        
        await ctx.send(embed=embed)

    @seitan.command(name="beg")
    async def seitan_beg(self, ctx, member: discord.Member):
        if not self.check(ctx):
            return await ctx.send("No permission.")
            
        CooldownDB.reset_appeal_cooldown(member.id)
        await ctx.send(f"The appeal cooldown for {member.mention} has been reset. They may beg again.")
        
    @seitan.command(name="appeal")
    async def seitan_appeal(self, ctx, *, message: str = ""):
        # ONLY sinners can use this
        row = SentencesDB.get_sentence(ctx.author.id, ctx.guild.id)
        
        if not row:
            return await ctx.send("You are not a Sinner. You have no need for appeals.", ephemeral=True)
            
        if len(message) > 150:
            return await ctx.send("Your plea is too long. Max 150 characters.", ephemeral=True)
            
        if not message:
            message = "Please let me go."

        # Check cooldown (GLOBAL)
        last_appeal = CooldownDB.get_appeal_cooldown(ctx.author.id)
        now = time.time()
        
        if last_appeal:
            # 1 week = 604800 seconds
            if now - last_appeal < 604800:
                remaining = 604800 - (now - last_appeal)
                days = int(remaining // 86400)
                hours = int((remaining % 86400) // 3600)
                
                mocks = get_mocks(ctx.guild.id)
                mock = random.choice(mocks)
                return await ctx.send(f"{mock} Try again in {days}d {hours}h.", ephemeral=True)
                
        # Insert or update global cooldown
        CooldownDB.set_appeal_cooldown(ctx.author.id, now)

        embed = discord.Embed(title="New Appeal Request", description=f"**{ctx.author.display_name}** pleads for mercy.", color=discord.Color.gold())
        embed.add_field(name="Message", value=f"\"{message}\"")
        embed.add_field(name="Current Sentence", value=f"{row[0]} days remaining", inline=False)
        
        view = AppealView(ctx.author.id, self.bot)
        
        # Try to send to a punisher channel or just reply in chat
        await ctx.send(embed=embed, view=view)

    @seitan.command(name="enable")
    async def seitan_enable(self, ctx, *, feature: str):
        if ctx.guild.owner_id != ctx.author.id:
            return await ctx.send("Only the server owner can use this command.")

        if feature.lower() == "global hell":
            SettingsDB.set_global_hell(ctx.guild.id, 1)
            await ctx.send("🌍 Global Hell has been enabled for this server.")
        else:
            await ctx.send(f"Unknown feature: {feature}")

    @seitan.command(name="disable")
    async def seitan_disable(self, ctx, *, feature: str):
        if ctx.guild.owner_id != ctx.author.id:
            return await ctx.send("Only the server owner can use this command.")

        if feature.lower() == "global hell":
            SettingsDB.set_global_hell(ctx.guild.id, 0)
            await ctx.send("🌍 Global Hell has been disabled for this server.")
        else:
            await ctx.send(f"Unknown feature: {feature}")

    @seitan.command(name="sentence")
    async def seitan_sentence(self, ctx):
        # We need to allow sinners to use this, but `check` might block them if they are not admin.
        # Wait, commands don't automatically use `self.check` unless we add it as a decorator or call it.
        # Since we use `if not self.check(ctx):` manually in commands, we can just omit it here!
        row = SentencesDB.get_sentence(ctx.author.id, ctx.guild.id)

        if not row:
            return await ctx.send("You are not currently condemned to #HELL in this server.", ephemeral=True)

        days_left, original_days, mode = row
        await ctx.send(f"🔥 {ctx.author.mention}, you have **{days_left} days** remaining. (Mode: {mode})", ephemeral=True)

    @seitan.command(name="grant")
    async def seitan_grant(self, ctx, authority_type: str, member: discord.Member = None):
        if not self.check(ctx):
            return await ctx.send("No permission.")
            
        if authority_type.lower() == "authority":
            if ctx.guild.owner_id != ctx.author.id:
                return await ctx.send("Only the server owner can grant Punisher authority.")
                
            punisher_role = discord.utils.get(ctx.guild.roles, name="Punisher")
            if not punisher_role:
                punisher_role = await ctx.guild.create_role(name="Punisher", color=discord.Color.dark_purple(), permissions=discord.Permissions(manage_messages=True, kick_members=True))
                
            await member.add_roles(punisher_role)
            await ctx.send(f"🔱 Congratulations, {member.mention}! You have been granted Punisher authority.")
            
        elif authority_type.lower() == "vision":
            vision_role = discord.utils.get(ctx.guild.roles, name="Hellish Observer")
            if not vision_role:
                vision_role = await ctx.guild.create_role(name="Hellish Observer", color=discord.Color.dark_grey())
                
            channel = discord.utils.get(ctx.guild.text_channels, name="hell")
            if channel:
                try:
                    await channel.set_permissions(vision_role, read_messages=True, send_messages=False)
                except discord.Forbidden:
                    pass
                    
            await member.add_roles(vision_role)
            await ctx.send(f"👁️ {member.mention} has been granted vision into #HELL.")

    @seitan.command(name="strip")
    async def seitan_strip(self, ctx, authority_type: str, member: discord.Member = None):
        if ctx.guild.owner_id != ctx.author.id:
            return await ctx.send("Only the server owner can use this command.")

        if authority_type.lower() == "authority":
            punisher_role = discord.utils.get(ctx.guild.roles, name="Punisher")
            if punisher_role and punisher_role in member.roles:
                await member.remove_roles(punisher_role)
                await ctx.send(f"❌ {member.mention} has had their Punisher authority stripped.")
            else:
                await ctx.send(f"{member.mention} does not have Punisher authority.")

    @seitan.command(name="blind")
    async def seitan_blind(self, ctx, member: discord.Member):
        if not self.check(ctx):
            return await ctx.send("No permission.")

        vision_role = discord.utils.get(ctx.guild.roles, name="Hellish Observer")
        if vision_role and vision_role in member.roles:
            await member.remove_roles(vision_role)
            await ctx.send(f"👁️‍🗨️ {member.mention} has been blinded to the suffering in #HELL.")
        else:
            await ctx.send(f"{member.mention} is already blind to #HELL.")

    @seitan.command(name="help")
    async def seitan_help(self, ctx):
        is_owner = ctx.guild.owner_id == ctx.author.id
        punisher = self.check(ctx)
        
        row = SentencesDB.get_sentence(ctx.author.id, ctx.guild.id)
        is_sinner = bool(row)

        embed = discord.Embed(title="SeiTan Command List", color=discord.Color.red())

        if is_sinner:
            embed.add_field(name="Sinner Commands", value="""
            `!seitan sentence` - Check how many days you have remaining in HELL.
            `!seitan appeal [message]` - Plead for mercy. Max 150 characters. Has a 1 week cooldown.
            """, inline=False)
            
        if punisher or is_owner:
            embed.add_field(name="Punisher Commands", value="""
            `!seitan go to hell <@user> <days> <mode> [reason]` - Send a user to HELL.
            `!seitan sins <@user>` - See the reason a user was sent to HELL.
            `!seitan beg <@user>` - Reset a Sinner's appeal cooldown.
            `!seitan grant vision <@user>` - Grant someone read-only access to #HELL.
            `!seitan blind <@user>` - Remove someone's read-only access to #HELL.
            `!sinners` - View the list of all users currently in HELL.
            `!addphrase <phrase>` - Add a custom apology phrase.
            `!addjoke <joke>` - Add a custom bad joke to mock the sinners.
            `!addmock <phrase>` - Add a custom appeal rejection mock.
            `!seitanstats` - View punishment analytics.
            """, inline=False)
            
        if is_owner:
            embed.add_field(name="Owner Only Commands", value="""
            `!seitan grant authority <@user>` - Make a user a Punisher.
            `!seitan strip authority <@user>` - Remove Punisher authority from a user.
            `!seitan enable/disable global hell` - Toggle Cross-Server Punishments.
            """, inline=False)

        if not is_sinner and not punisher and not is_owner:
            embed.description = "You are but a mortal. Stay pure, lest you find yourself needing these commands."

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Punishment(bot))
