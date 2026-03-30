import random
from database.db import cursor, conn


DEFAULT_PHRASES = ["I'm sorry!"]


def add_phrase(guild_id, phrase, creator_id):
    cursor.execute("""
    INSERT INTO phrase_rules (guild_id, phrase, created_by)
    VALUES (?, ?, ?)
    """, (guild_id, phrase, creator_id))

    conn.commit()


def remove_phrase(guild_id, phrase):
    cursor.execute("""
    DELETE FROM phrase_rules
    WHERE guild_id=? AND phrase=?
    """, (guild_id, phrase))

    conn.commit()


def get_phrases(guild_id):

    cursor.execute("""
    SELECT phrase FROM phrase_rules
    WHERE guild_id=?
    """, (guild_id,))

    rows = cursor.fetchall()

    phrases = [r[0] for r in rows]
    
    # We always include default phrases, plus whatever custom ones the server has added
    return DEFAULT_PHRASES + phrases


def get_random_phrase(guild_id):
    phrases = get_phrases(guild_id)
    return random.choice(phrases)


def validate_phrase(guild_id, message_content):

    valid = get_phrases(guild_id)

    msg = message_content.lower().strip()

    for phrase in valid:
        if msg == phrase.lower():
            return True

    return False


def get_incorrect_messages(guild_id):
    cursor.execute("SELECT text FROM incorrect_messages WHERE guild_id=?", (guild_id,))
    rows = cursor.fetchall()
    return [r[0] for r in rows] if rows else ["❌ Incorrect phrase."]


def pick_incorrect_message(guild_id):
    messages = get_incorrect_messages(guild_id)
    return random.choice(messages)
