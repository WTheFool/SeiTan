import discord
from discord.ext import commands
from database.db import cursor
from systems.permissions import is_admin


class Stats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def seitanstats(self, ctx):
        if not is_admin(ctx.author, ctx.guild) and ctx.guild.owner_id != ctx.author.id:
            return await ctx.send("No permission.")

        # Total punishments in this server
        cursor.execute("SELECT total_punishments FROM analytics WHERE guild_id=?", (ctx.guild.id,))
        analytics_row = cursor.fetchone()
        server_punishments = analytics_row[0] if analytics_row else 0

        # Longest sentence in this server
        cursor.execute("SELECT MAX(original_days) FROM sentences WHERE guild_id=?", (ctx.guild.id,))
        longest_sentence_row = cursor.fetchone()
        longest_sentence = longest_sentence_row[0] if longest_sentence_row and longest_sentence_row[0] else 0

        # Current sinners in this server
        cursor.execute("SELECT COUNT(*) FROM sentences WHERE guild_id=?", (ctx.guild.id,))
        current_sinners_server = cursor.fetchone()[0]

        # Current sinners globally
        cursor.execute("SELECT COUNT(*) FROM sentences")
        current_sinners_global = cursor.fetchone()[0]

        # Total punishments globally
        cursor.execute("SELECT SUM(total_punishments) FROM analytics")
        global_punishments_row = cursor.fetchone()
        global_punishments = global_punishments_row[0] if global_punishments_row and global_punishments_row[0] else 0

        # Max streak globally (or per server)
        cursor.execute("SELECT MAX(max_streak) FROM cycle_state WHERE guild_id=?", (ctx.guild.id,))
        max_streak_row = cursor.fetchone()
        max_streak = max_streak_row[0] if max_streak_row and max_streak_row[0] else 0

        embed = discord.Embed(title="📊 SeiTan Server Statistics", color=discord.Color.red())
        
        embed.add_field(name="Server Punishments", value=f"☠️ {server_punishments} Total\n🔥 {current_sinners_server} Active Sinners", inline=True)
        embed.add_field(name="Global Punishments", value=f"🌍 {global_punishments} Total\n🌐 {current_sinners_global} Active Sinners", inline=True)
        
        embed.add_field(name="Records (Server)", value=f"⏳ Longest Sentence: {longest_sentence} days\n🔥 Highest Streak: {max_streak} consecutive apologies", inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))
