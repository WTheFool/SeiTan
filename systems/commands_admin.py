import discord
from discord.ext import commands

from systems.permissions import is_admin
from database.db import cursor, conn
from database.db_methods import SentencesDB

class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def check(self, ctx):
        return is_admin(ctx.author, ctx.guild)

    @commands.command()
    async def sinners(self, ctx):

        if not self.check(ctx):
            return await ctx.send("No permission.")

        cursor.execute("""
        SELECT user_id, days_left, mode
        FROM sentences
        WHERE guild_id=?
        """, (ctx.guild.id,))

        rows = cursor.fetchall()

        if not rows:
            return await ctx.send("No sinners.")

        msg = "**☠️ Sinners:**\n"

        for uid, days_left, mode in rows:
            member = ctx.guild.get_member(uid)
            name = member.display_name if member else uid
            msg += f"- {name} | {mode} | {days_left} days left\n"

        await ctx.send(msg)
        
    @commands.command()
    async def addmock(self, ctx, *, text):
        if not self.check(ctx):
            return await ctx.send("No permission.")

        cursor.execute("INSERT INTO mocks (guild_id, text) VALUES (?, ?)", (ctx.guild.id, text))
        conn.commit()

        await ctx.send("Mocking phrase added.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
