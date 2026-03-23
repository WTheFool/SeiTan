from discord.ext import commands

from systems.permissions import is_admin
from database.db import cursor, conn


class Personality(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def check(self, ctx):
        return is_admin(ctx.author, ctx.guild)

    @commands.command()
    async def addphrase(self, ctx, *, text):

        if not self.check(ctx):
            return await ctx.send("No permission.")

        cursor.execute("INSERT INTO phrase_rules VALUES (?, ?, ?)", (ctx.guild.id, text, ctx.author.id))
        conn.commit()

        await ctx.send("Phrase added.")

    @commands.command()
    async def addjoke(self, ctx, *, text):

        if not self.check(ctx):
            return await ctx.send("No permission.")

        cursor.execute("INSERT INTO jokes VALUES (?, ?)", (ctx.guild.id, text))
        conn.commit()

        await ctx.send("Joke added.")


async def setup(bot):
    await bot.add_cog(Personality(bot))