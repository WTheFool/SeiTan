import discord

PUNISHER_ROLE_NAME = "Punisher"

def is_sinner_anywhere(user_id):
    from database.db import cursor
    cursor.execute("SELECT 1 FROM sentences WHERE user_id=? LIMIT 1", (user_id,))
    return cursor.fetchone() is not None

def is_authorized(ctx):
    if is_sinner_anywhere(ctx.author.id):
        return False

    # server owner always allowed
    if ctx.guild.owner_id == ctx.author.id:
        return True

    role = discord.utils.get(ctx.author.roles, name=PUNISHER_ROLE_NAME)
    return role is not None

def is_admin(user, guild):
    if is_sinner_anywhere(user.id):
        return False

    if guild.owner_id == user.id:
        return True
    
    role = discord.utils.get(user.roles, name=PUNISHER_ROLE_NAME)
    return role is not None
