from database.db import cursor, conn

def get_mood(guild_id):

    cursor.execute("SELECT mood FROM guild_settings WHERE guild_id=?", (guild_id,))
    row = cursor.fetchone()

    return row[0] if row and row[0] else "calm"


def set_mood(guild_id, mood):
    cursor.execute("""
    UPDATE guild_settings
    SET mood=?
    WHERE guild_id=?
    """, (mood, guild_id))
    conn.commit()