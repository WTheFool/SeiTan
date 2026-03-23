from database.db import cursor, conn


def add_punishment(user_id):

    cursor.execute("""
    INSERT OR IGNORE INTO memory (user_id)
    VALUES (?)
    """, (user_id,))

    cursor.execute("""
    UPDATE memory
    SET total_punishments = total_punishments + 1
    WHERE user_id=?
    """, (user_id,))

    conn.commit()


def get_flag(user_id):

    cursor.execute("""
    SELECT total_punishments FROM memory
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()
    if not row:
        return "normal"

    p = row[0]

    if p >= 50:
        return "high_threat"
    if p >= 20:
        return "repeat_offender"

    return "normal"