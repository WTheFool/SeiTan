import discord
from discord.ext import commands

from systems.permissions import is_authorized


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def setpunisher(self, ctx, role: discord.Role):

        if ctx.guild.owner_id != ctx.author.id:
            return await ctx.send("Owner only.")

        # future: store role in DB
        await ctx.send(f"Punisher role set to {role.name}")


    @commands.command()
    async def setuphell(self, ctx):

        if not is_authorized(ctx):
            return await ctx.send("No permission.")

        channel = discord.utils.get(ctx.guild.text_channels, name="hell")

        if not channel:
            await ctx.guild.create_text_channel("hell")

        await ctx.send("#HELL is ready.")


async def setup(bot):
    await bot.add_cog(Admin(bot))