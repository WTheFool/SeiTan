import discord

PUNISHER_ROLE_NAME = "Punisher"

def is_sinner_anywhere(user_id):
    from database.db import cursor
    cursor.execute("SELECT 1 FROM sentences WHERE user_id=? LIMIT 1", (user_id,))
    return cursor.fetchone() is not None

def is_authorized(ctx):
    # Server owner is ALWAYS authorized to use admin commands, even if they are a sinner somewhere else.
    if ctx.guild.owner_id == ctx.author.id:
        return True

    # If not the owner, check if they are a sinner anywhere
    if is_sinner_anywhere(ctx.author.id):
        return False

    role = discord.utils.get(ctx.author.roles, name=PUNISHER_ROLE_NAME)
    return role is not None

def is_admin(user, guild):
    # Server owner is ALWAYS an admin
    if guild.owner_id == user.id:
        return True
        
    # If not the owner, check if they are a sinner anywhere
    if is_sinner_anywhere(user.id):
        return False
    
    role = discord.utils.get(user.roles, name=PUNISHER_ROLE_NAME)
    return role is not None
