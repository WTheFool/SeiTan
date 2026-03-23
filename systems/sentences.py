from database.db import cursor, conn
from datetime import datetime


def assign_sentence(user_id, guild_id, days, mode, reason="No reason provided."):

    cursor.execute("""
    INSERT OR REPLACE INTO sentences (user_id, guild_id, days_left, original_days, mode, last_check, reason)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, guild_id, days, days, mode, str(datetime.utcnow()), reason))

    conn.commit()


def get_sentence(user_id, guild_id):

    cursor.execute("""
    SELECT days_left, mode, original_days FROM sentences
    WHERE user_id=? AND guild_id=?
    """, (user_id, guild_id))

    return cursor.fetchone()


def decrement_day(user_id, guild_id):

    data = get_sentence(user_id, guild_id)
    if not data:
        return

    days_left, mode, original_days = data

    new_days = days_left - 1

    cursor.execute("""
    UPDATE sentences
    SET days_left=?
    WHERE user_id=? AND guild_id=?
    """, (new_days, user_id, guild_id))

    conn.commit()
