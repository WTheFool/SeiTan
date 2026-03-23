from database.db import cursor, conn


def log(guild_id, event):

    cursor.execute("""
    INSERT OR IGNORE INTO analytics (guild_id)
    VALUES (?)
    """, (guild_id,))

    if event == "punish":
        cursor.execute("""
        UPDATE analytics SET total_punishments = total_punishments + 1
        WHERE guild_id=?
        """, (guild_id,))

    elif event == "appeal":
        cursor.execute("""
        UPDATE analytics SET appeals = appeals + 1
        WHERE guild_id=?
        """, (guild_id,))

    elif event == "deny":
        cursor.execute("""
        UPDATE analytics SET denials = denials + 1
        WHERE guild_id=?
        """, (guild_id,))

    conn.commit()