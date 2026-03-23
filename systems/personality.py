import random
from database.db import cursor

DEFAULT_PHRASES = ["I'm sorry!"]
DEFAULT_JOKES = ["Even hell is disappointed in you."]

def get_phrases(guild_id):
    cursor.execute("SELECT phrase FROM phrase_rules WHERE guild_id=?", (guild_id,))
    rows = cursor.fetchall()
    phrases = [r[0] for r in rows]
    return DEFAULT_PHRASES + phrases


def get_jokes(guild_id):
    cursor.execute("SELECT text FROM jokes WHERE guild_id=?", (guild_id,))
    rows = cursor.fetchall()
    jokes = [r[0] for r in rows]
    return DEFAULT_JOKES + jokes


def pick_phrase(guild_id):
    return random.choice(get_phrases(guild_id))


def pick_joke(guild_id):
    return random.choice(get_jokes(guild_id))
