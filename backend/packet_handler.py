from convenience import *

from shove import Shove
from user import User
from commands import handle_command


def handle_packets_loop(shove):
    """Blocking loop for handling packets (that were added to the queue)"""

    set_greenthread_name("PacketHandler")
    Log.trace("Handle packets loop ready")

    while True:
        user, model, packet, packet_number = shove.incoming_packets_queue.get()
        set_greenthread_name(f"PacketHandler/#{packet_number}")
        Log.trace(f"Handling packet #{packet_number}")

        try:
            response = handle_packet(shove, user, model, packet)

        except CommandInvalid as ex:
            Log.trace(f"Command invalid: {ex.description}")
            response = "error", {
                "description": ex.description
            }

        except PacketHandlingFailed as ex:
            Log.trace(f"Packet handling failed: {type(ex).__name__}: {ex.description}")  # ex.__name__ as PacketHandlingFailed has children
            response = "error", {
                "description": ex.description
            }

        except NotImplementedError as ex:
            Log.error("Not implemented", ex)
            response = "error", {
                "description": "Not implemented (yet)"
            }

        except Exception as ex:
            Log.fatal(f"UNHANDLED {type(ex).__name__} on handle_packet", ex)
            response = "error", error_packet(description="Unhandled exception on handling packet (very bad)")

        if response:
            response_model, response_packet = response
            Log.trace(f"Handled packet #{packet_number}, response model: '{response_model}'")
            shove.send_packet_to(user, response_model, response_packet, is_response=True)

        else:
            Log.trace(f"Handled packet #{packet_number}, no direct response")


def handle_packet(shove: Shove, user: User, model: str, packet: dict) -> Optional[Tuple[str, dict]]:
    """Handles the packet and returns an optional response model + packet"""

    if not model:
        raise PacketInvalid("No model provided")

    if type(packet) != dict:
        raise PacketInvalid(f"Invalid packet type: {type(packet).__name__}")

    if model == "error":
        Log.error(f"User received an error: {packet['description']}")
        return

    # special game packet, should be handled by game's packet handler
    if model == "game_action":  # currently the only model for game packets
        if not user.is_logged_in():
            raise UserNotLoggedIn

        room = shove.get_room_of_user(user)

        if not room:
            raise PacketInvalid("Not in a room")

        if not room.game:
            raise GameNotSet

        response = room.game.handle_packet(user, model, packet)  # can return a response (model, packet) tuple
        return response

    if model == "get_account_data":
        if "username" in packet:
            username = packet["username"].strip().lower()
            account = shove.accounts.find_single(username=username)

        elif user.is_logged_in():
            account = user.get_account()

        else:
            raise PacketInvalid("Not logged in and no username provided")

        return "account_data", account.get_data_copy()

    if model == "get_account_list":
        return "account_list", shove.accounts.get_entries_data_sorted(key=lambda e: e["username"])

    if model == "get_song":
        Log.trace(f"Song count: {shove.songs.get_song_count()}")

        try:
            song = random.choice(list(shove.songs.get_entries()))
        except IndexError:
            raise NoSongsAvailable

        Log.trace(f"Random song: {song}")
        song.play(shove, user)
        return

    if model == "get_game_data":
        room = shove.get_room_of_user(user)

        if not room:
            raise PacketInvalid("Not in a room")

        if not room.game:
            raise GameNotSet

        return "game_data", room.game.get_data()

    if model == "get_room_data":
        raise NotImplementedError

    if model == "get_room_list":  # send a list of dicts with each room's data
        return "room_list", {  # todo make this a list not an object/dict
            "room_list": [room.get_data() for room in shove.get_rooms()]
        }

    if model == "join_room":
        if shove.get_room_of_user(user):
            raise UserAlreadyInRoom

        room = shove.get_room(packet["room_name"])

        if not room:
            raise RoomNotFound

        room.user_tries_to_join(user)  # this throws an exception if user can't join room

        if room.game:
            game_data = room.game.get_data()
        else:
            game_data = None

        return "join_room", {
            "room_data": room.get_data(),
            "game_data": game_data
        }

    if model == "leave_room":
        if not user.is_logged_in():
            raise UserNotLoggedIn

        room = shove.get_room_of_user(user)

        if not room:
            raise UserNotInRoom

        room.user_leave(user)

        return "leave_room", {
            "room_name": room.name
        }

    if model == "log_in":
        username = packet["username"].strip().lower()
        password = packet["password"]
        account = shove.accounts.find_single(username=username)

        if account["password"] != password:
            # raise PasswordInvalid  # comment out to disable password checking
            pass

        user.log_in_as(account)

        return "log_in", {
            "account_data": user.get_account_data_copy()
        }

    if model == "log_out":
        if not user.is_logged_in():
            raise UserNotLoggedIn

        shove.log_out_user(user)

        return

    if model == "pong":
        now = time.time()
        user.latency = now - user.pinged_timestamp
        user.last_pong_received = now
        Log.trace(f"Pong received from {user} ({user.pinged_timestamp}), latency: {round(user.latency * 1000)} ms")

        return "latency", {
            "latency": user.latency
        }

    if model == "rate_song":
        if not user.is_logged_in():
            raise UserNotLoggedIn

        song = shove.latest_song
        if not song:
            raise PacketInvalid("No song is currently playing, can't rate")

        username = user.get_username()
        action = packet["action"]

        if action == "toggle_dislike":
            song.toggle_dislike(username)
        elif action == "toggle_like":
            song.toggle_like(username)
        else:
            raise PacketInvalid("Invalid rate song action")

        song.broadcast_rating(shove)

        return

    if model == "register":
        raise NotImplementedError

    if model == "send_message":
        message: str = packet["message"].strip()

        if not message:
            Log.trace("Empty message provided, ignoring")
            return

        # check if message is a command first, as some commands don't require user to be logged in
        if message.startswith("/"):
            response_message = handle_command(shove, user, message)  # returns optional response message to user
            return "command_success", {
                "response": response_message
            }

        # not a command, so it is a chat message
        if not user.is_logged_in():
            raise UserNotLoggedIn

        username = user.get_username()
        Log.trace(f"Message from {username}: '{message}'")
        shove.send_packet_to_everyone("message", {
            "author": username,
            "text": message
        })
        return

    if model == "song_rating":
        if not shove.latest_song:
            Log.trace("No song playing, not sending rating")
            return

        return "song_rating", shove.latest_song.get_rating(user)

    raise PacketInvalid(f"Unknown packet model: '{model}'")

