import discord

SINNER = "Sinner"
REPENTED = "Repented"
PUNISHER = "Punisher"


async def set_role(member, role_name):

    role = discord.utils.get(member.guild.roles, name=role_name)

    if role:
        await member.add_roles(role)


async def remove_role(member, role_name):

    role = discord.utils.get(member.guild.roles, name=role_name)

    if role:
        await member.remove_roles(role)