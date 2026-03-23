import discord
from discord.ext import commands

from systems.permissions import is_authorized
from systems.memory import add_punishment, get_flag
from systems.analytics import log
from systems.reactions import react


class Punishment(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def seitan(self, ctx, member: discord.Member):

        if not is_authorized(ctx):
            return await ctx.send(react("no_permission"))

        channel = discord.utils.get(ctx.guild.text_channels, name="hell")

        if not channel:
            channel = await ctx.guild.create_text_channel("hell")

        add_punishment(member.id)
        flag = get_flag(member.id)

        log(ctx.guild.id, "punish")

        await channel.send(
            f"{member.mention}\n{react('hell')}\nFlag: {flag}"
        )


async def setup(bot):
    await bot.add_cog(Punishment(bot))