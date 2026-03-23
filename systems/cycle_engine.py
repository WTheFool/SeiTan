from datetime import datetime, timedelta
from database.db import cursor, conn


PING_WINDOW_MINUTES = 30


def ensure_state(user_id, guild_id):

    cursor.execute("""
    INSERT OR IGNORE INTO cycle_state (user_id, guild_id)
    VALUES (?, ?)
    """, (user_id, guild_id))

    conn.commit()


def start_cycle(user_id, guild_id):

    ensure_state(user_id, guild_id)

    cursor.execute("""
    UPDATE cycle_state
    SET last_ping=?, pending=1
    WHERE user_id=? AND guild_id=?
    """, (str(datetime.utcnow()), user_id, guild_id))

    conn.commit()


def record_response(user_id, guild_id):

    ensure_state(user_id, guild_id)

    cursor.execute("""
    UPDATE cycle_state
    SET last_response=?, pending=0
    WHERE user_id=? AND guild_id=?
    """, (str(datetime.utcnow()), user_id, guild_id))

    conn.commit()


def process_cycle(user_id, guild_id, mode="incremental"):

    ensure_state(user_id, guild_id)

    cursor.execute("""
    SELECT last_ping, last_response, pending, missed_days, current_streak, max_streak
    FROM cycle_state
    WHERE user_id=? AND guild_id=?
    """, (user_id, guild_id))

    row = cursor.fetchone()
    if not row:
        return None

    last_ping, last_response, pending, missed, current_streak, max_streak = row

    if not pending:
        return "no_active_cycle"

    ping_time = datetime.fromisoformat(last_ping)
    now = datetime.utcnow()

    # 30-minute validation window
    if last_response:
        response_time = datetime.fromisoformat(last_response)

        if response_time <= ping_time + timedelta(minutes=PING_WINDOW_MINUTES):
            # SUCCESS LOGIC
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
                
            cursor.execute("""
            UPDATE cycle_state
            SET pending=0, current_streak=?, max_streak=?
            WHERE user_id=? AND guild_id=?
            """, (current_streak, max_streak, user_id, guild_id))
            conn.commit()
            return "success"

    # FAILED RESPONSE LOGIC
    current_streak = 0 # reset streak on fail
    
    if mode == "incremental":
        missed += 1  # punishment grows

    elif mode == "consecutive":
        missed += 1  # breaks streak

    cursor.execute("""
    UPDATE cycle_state
    SET pending=0,
        missed_days=?,
        current_streak=?
    WHERE user_id=? AND guild_id=?
    """, (missed, current_streak, user_id, guild_id))

    conn.commit()

    return "fail"
