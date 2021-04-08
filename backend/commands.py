from convenience import *

from shove import Shove
from user import User
from process_song import process_song_task


COMMANDS = {
    "account": {
        "aliases": [],
        "usage": "/account <create/delete> <username>"
    },
    "error": {
        "aliases": [],
        "usage": "/error"
    },
    "help": {
        "aliases": ["?"],
        "usage": "/help"
    },
    "money": {
        "aliases": ["cash"],
        "usage": "/money"
    },
    "play": {
        "aliases": ["audio", "music", "song"],
        "usage": "/play <url/ID>"
    },
    "trello": {
        "aliases": [],
        "splitter": "...",
        "usage": "/trello <card name> '...' [card description]"
    }
}


def is_command(input_str, match_command):
    return input_str == match_command or input_str in COMMANDS[match_command]


def handle_command(shove: Shove, user: User, message: str) -> Optional[str]:
    Log.trace(f"Handling command message: '{message}'")
    _message_full_real = message[1:].strip()  # [1:] -> ignore the leading "/"
    _message_full = _message_full_real.lower()
    _message_split_real = _message_full_real.split()
    _message_split = _message_full.split()
    command = _message_split[0] if _message_split else None
    command_args = _message_split[1:] if len(_message_split) > 1 else []  # /command [arg0, arg1, ...]
    command_args_real = _message_split_real[1:] if len(_message_split) > 1 else []

    if not command or is_command(command, "help"):
        return f"{[c for c in COMMANDS.keys()]}"

    if is_command(command, "account"):
        if len(command_args_real) == 0:
            raise CommandInvalid(COMMANDS["account"]["usage"])

        if command_args_real[0] == "create":
            if len(command_args_real) == 1:
                if not user.is_logged_in():
                    raise UserNotLoggedIn

                preferred_username = None

            elif len(command_args_real) == 2:
                preferred_username = command_args_real[1]

            else:
                raise CommandInvalid(COMMANDS["account"]["usage"])

            username = shove.accounts.create_random_account(preferred_username)["username"]

            shove.send_packet_to_everyone("account_list", shove.accounts.get_entries_data_sorted(lambda e: e["username"]))

            return f"Created account '{username}'"

        if command_args_real[0] == "delete":
            if len(command_args_real) == 1:
                if not user.is_logged_in():
                    raise UserNotLoggedIn

                delete_username = user.get_username()

            elif len(command_args_real) == 2:
                delete_username = command_args_real[1]

            else:
                raise CommandInvalid(COMMANDS["account"]["usage"])

            found_account = shove.accounts.find_single(raise_if_missing=False, username=delete_username)
            if found_account:
                for user in shove.get_all_users():
                    if user.get_username() == delete_username:
                        shove.log_out_user(user)

                del found_account

            else:
                raise CommandInvalid(f"Account with username '{delete_username}' not found")

            return f"Deleted account '{delete_username}'"

    if is_command(command, "error"):  # raises an error to test error handling and logging
        raise Exception("/error was executed, all good")

    if is_command(command, "money"):
        if not user.is_logged_in():
            raise UserNotLoggedIn

        user.get_account()["money"] += 9e15
        shove.send_packet_to(user, "account_data", user.get_account_data_copy())
        return "Money added"

    if is_command(command, "trello"):
        if not PRIVATE_ACCESS:  # if backend host doesn't have access to the Shove Trello account
            raise NoPrivateAccess

        trello_args = " ".join(command_args_real).split(COMMANDS["trello"]["splitter"])
        if len(trello_args) == 1:
            name, description = trello_args[0], None

        elif len(trello_args) == 2:
            name, description = trello_args

        else:
            raise CommandInvalid(f"Invalid arguments, usage: {COMMANDS['trello']['usage']}")

        if not name:
            raise CommandInvalid(f"No card name, usage: {COMMANDS['trello']['usage']}")

        shove.add_trello_card(name, description)
        return "Card added"

    if is_command(command, "play"):
        if not command_args:
            raise CommandInvalid(f"No link provided, usage: {COMMANDS['play']['usage']}")

        check_for_id_string = command_args_real[0]

        # check if user dropped an 11-char YT id
        if len(check_for_id_string) == 11:
            youtube_id = check_for_id_string

        # regex magic to find the id in some url
        else:
            match = re.search(
                r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?(?P<id>[A-Za-z0-9\-=_]{11})",
                check_for_id_string
            )

            if not match:
                raise CommandInvalid(f"Couldn't find a video ID in the given link, usage: {COMMANDS['play']['usage']}")

            youtube_id = match.group("id")
            Log.trace(f"Found ID using regex")

        Log.trace(f"Got YouTube ID: {youtube_id}")
        eventlet.spawn(process_song_task, shove, youtube_id, user)

        return "Success"

    raise CommandInvalid(f"Unknown command: '{command}'")
