from convenience import *


def ping_users_loop(shove):
    """Blocking loop to ping all connected users periodically"""

    set_greenlet_name("UserPinger")
    Log.trace("Ping users loop ready")
    time_since_last_ping = 0

    if not PING_USERS_ENABLED:  # extra check to not ping if not enabled
        Log.warning(f"PING_USERS_ENABLED={PING_USERS_ENABLED}, cancelling")
        return

    while True:
        now = time.time()
        all_users = shove.get_all_users()
        for user in all_users:  # check who needs to get disconnected for ping timeout
            if user.last_pong_received + PONG_DELAY_BEFORE_TIMEOUT <= now:
                Log.warning(f"Disconnecting user {user} (didn't pong)")
                shove.on_disconnect(user)

        if time_since_last_ping == PING_USERS_INTERVAL:
            Log.trace("Pinging all users")
            for user in all_users:
                user.pinged_timestamp = now
            shove.send_packet_to_everyone("ping", {})
            time_since_last_ping = 0

        time.sleep(1)
        time_since_last_ping += 1
