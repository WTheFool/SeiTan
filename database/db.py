import sqlite3
import os
from config import DB_PATH

os.makedirs("data", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def init_db():

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        user_id INTEGER PRIMARY KEY,
        total_punishments INTEGER DEFAULT 0,
        global_flag TEXT DEFAULT 'normal'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guild_settings (
        guild_id INTEGER PRIMARY KEY,
        hell_channel_id INTEGER,
        punish_role_id INTEGER,
        global_hell INTEGER DEFAULT 0
    )
    """)
    
    # Migration for global_hell
    try:
        cursor.execute("ALTER TABLE guild_settings ADD COLUMN global_hell INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics (
        guild_id INTEGER PRIMARY KEY,
        total_punishments INTEGER DEFAULT 0,
        appeals INTEGER DEFAULT 0,
        denials INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sentences (
        user_id INTEGER,
        guild_id INTEGER,
        days_left INTEGER,
        original_days INTEGER DEFAULT 0,
        mode TEXT, -- incremental / consecutive / default
        last_check TEXT,
        PRIMARY KEY (user_id, guild_id)
    )
    """)

    # Check if original_days exists, if not alter table (migration)
    try:
        cursor.execute("ALTER TABLE sentences ADD COLUMN original_days INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        cursor.execute("ALTER TABLE sentences ADD COLUMN reason TEXT DEFAULT 'No reason provided.'")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sentence_state (
        user_id INTEGER,
        guild_id INTEGER,
        responded_today INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, guild_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cycle_state (
        user_id INTEGER,
        guild_id INTEGER,
        last_ping TEXT,
        last_response TEXT,
        pending INTEGER DEFAULT 0,
        missed_days INTEGER DEFAULT 0,
        current_streak INTEGER DEFAULT 0,
        max_streak INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, guild_id)
    )
    """)
    
    # Migration for streak tracking
    try:
        cursor.execute("ALTER TABLE cycle_state ADD COLUMN current_streak INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE cycle_state ADD COLUMN max_streak INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS phrases (
        guild_id INTEGER,
        text TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jokes (
        guild_id INTEGER,
        text TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS phrase_rules (
        guild_id INTEGER,
        phrase TEXT,
        created_by INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS global_cooldowns (
        user_id INTEGER PRIMARY KEY,
        last_reduction REAL
    )
    """)

    conn.commit()
