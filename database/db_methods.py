from database.db import cursor, conn
import time

class SettingsDB:
    @staticmethod
    def is_global_hell(guild_id: int) -> bool:
        cursor.execute("SELECT global_hell FROM guild_settings WHERE guild_id=?", (guild_id,))
        row = cursor.fetchone()
        return row and row[0] == 1

    @staticmethod
    def set_global_hell(guild_id: int, state: int):
        cursor.execute("""
        INSERT INTO guild_settings (guild_id, global_hell)
        VALUES (?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET global_hell=?
        """, (guild_id, state, state))
        conn.commit()


class SentencesDB:
    @staticmethod
    def get_sentence(user_id: int, guild_id: int):
        cursor.execute("SELECT days_left, original_days, mode FROM sentences WHERE user_id=? AND guild_id=?", (user_id, guild_id))
        return cursor.fetchone()

    @staticmethod
    def get_all_active_sentences():
        cursor.execute("SELECT user_id, guild_id, mode FROM sentences WHERE days_left > 0")
        return cursor.fetchall()
        
    @staticmethod
    def update_days(user_id: int, guild_id: int, days: int, global_update: bool = False):
        if global_update:
            cursor.execute("UPDATE sentences SET days_left=? WHERE user_id=? AND guild_id IN (SELECT guild_id FROM guild_settings WHERE global_hell=1)", (days, user_id))
        else:
            cursor.execute("UPDATE sentences SET days_left=? WHERE user_id=? AND guild_id=?", (days, user_id, guild_id))
        conn.commit()

    @staticmethod
    def delete_sentence(user_id: int, guild_id: int, global_update: bool = False):
        if global_update:
            cursor.execute("DELETE FROM sentences WHERE user_id=? AND guild_id IN (SELECT guild_id FROM guild_settings WHERE global_hell=1)", (user_id,))
        else:
            cursor.execute("DELETE FROM sentences WHERE user_id=? AND guild_id=?", (user_id, guild_id))
        conn.commit()


class CooldownDB:
    @staticmethod
    def get_appeal_cooldown(user_id: int):
        cursor.execute("SELECT last_appeal FROM appeal_cooldowns WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    @staticmethod
    def set_appeal_cooldown(user_id: int, current_time: float):
        try:
            cursor.execute("""
            INSERT OR REPLACE INTO appeal_cooldowns (user_id, last_appeal)
            VALUES (?, ?)
            """, (user_id, current_time))
        except:
            pass # Ignore old schema errors gracefully
        conn.commit()
        
    @staticmethod
    def reset_appeal_cooldown(user_id: int):
        cursor.execute("DELETE FROM appeal_cooldowns WHERE user_id=?", (user_id,))
        conn.commit()
        
    @staticmethod
    def get_global_reduction_cooldown(user_id: int):
        cursor.execute("SELECT last_reduction FROM global_cooldowns WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None
        
    @staticmethod
    def set_global_reduction_cooldown(user_id: int, current_time: float):
        cursor.execute("""
        INSERT OR REPLACE INTO global_cooldowns (user_id, last_reduction)
        VALUES (?, ?)
        """, (user_id, current_time))
        conn.commit()
