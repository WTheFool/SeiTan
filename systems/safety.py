import time

# prevents spam commands (user_id -> timestamp)
command_cooldowns = {}

def check_cooldown(user_id, seconds=10):
    now = time.time()

    last = command_cooldowns.get(user_id, 0)

    if now - last < seconds:
        return False

    command_cooldowns[user_id] = now
    return True