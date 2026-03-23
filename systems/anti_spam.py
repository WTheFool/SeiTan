import time

_last_ping_cache = {}

def can_ping(user_id: int) -> bool:
    """
    Prevents spam or duplicate pings within a short time window.
    """

    now = time.time()

    if user_id in _last_ping_cache:
        if now - _last_ping_cache[user_id] < 10:
            return False

    _last_ping_cache[user_id] = now
    return True