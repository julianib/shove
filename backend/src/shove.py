from convenience import *

from database import Accounts
from database import Song, Songs
from room import Room
from user import User

from games.coinflip import Coinflip
# from games.qwerty import Qwerty


class Shove:
    def __init__(self, sio):
        Log.trace("Initializing Shove")
        self.sio: socketio.Server = sio
        self.incoming_packets_queue = Queue()  # (User, model, packet, packet_number)
        self.outgoing_packets_queue = Queue()  # ([User], model, packet, skip, packet_number)

        self._default_game = Coinflip
        self._last_bot_id = 0
        self._last_packet_id = 0
        self._last_room_id = 0
        self._users: Set[User] = set()  # todo implement as DB with DB entries?
        self._rooms: Set[Room] = set()  # todo implement as DB with DB entries?

        self.accounts = Accounts()
        self.songs = Songs(self)

        self.reset_rooms(3)
        # self.rooms[0].add_bot(3)

        if PRIVATE_KEYS_IMPORTED:
            Log.trace("Initializing Trello client, fetching card list")
            client = trello.TrelloClient(
                api_key=TRELLO_API_KEY,
                api_secret=TRELLO_API_SECRET,
                token=TRELLO_TOKEN
            )
            board = client.get_board(TRELLO_BOARD_ID)
            self._trello_card_list = board.get_list(TRELLO_LIST_ID)
        else:
            Log.trace("No private access, not initializing Trello client")

        self.latest_song: Union[Song, None] = None
        self.latest_song_author: Union[User, None] = None

        Log.trace("Shove initialized")

    def add_trello_card(self, name, description=None):
        name = name.strip()
        if description is not None:
            description = description.strip()

        Log.trace(f"Adding card to Trello card list, name = '{name}', description = '{description}'")
        self._trello_card_list.add_card(name=name, desc=description, position="top")
        Log.trace(f"Added card")

    def create_new_user_from_sid(self, sid: str):
        sids = [user.sid for user in self._users]
        if sid in sids:
            raise ValueError(f"SID already exists: {sid}")  # shouldn't ever happen

        user = User(sid)
        self._users.add(user)
        return user

    def get_room_names(self) -> List[str]:
        return [room.name for room in self.get_rooms()]

    def get_rooms(self) -> Set[Room]:
        return self._rooms.copy()

    def get_all_users(self) -> Set[User]:
        return self._users.copy()

    def get_default_game(self):
        return self._default_game

    def get_next_bot_id(self) -> int:
        self._last_bot_id += 1
        return self._last_bot_id

    def get_next_packet_id(self) -> int:
        self._last_packet_id += 1
        return self._last_packet_id

    def get_next_room_id(self) -> int:
        self._last_room_id += 1
        return self._last_room_id

    def get_room(self, room_name: str) -> Room:
        Log.trace(f"Getting room with name: '{room_name}'")
        room_name_formatted = room_name.lower().strip()
        for room in self.get_rooms():
            if room.name.lower() == room_name_formatted:
                Log.trace(f"Found room with matching name: {room}")
                return room

        Log.trace("Room with matching name not found")

    def get_room_count(self) -> int:
        return len(self.get_rooms())

    def get_room_of_user(self, user: User) -> Room:
        Log.trace(f"Getting room of user {user}")

        for room in self.get_rooms():
            if user in room.get_users():
                Log.trace(f"User is in room: {room}")
                return room

        Log.trace("User is not in a room")

    def get_user_by_sid(self, sid) -> User:
        for user in self.get_all_users():
            if user.sid == sid:
                return user

        raise ValueError(f"No user matched with SID: {sid}")

    def get_user_count(self) -> int:
        return len(self._users)

    def log_out_user(self, user, disconnected=False):
        Log.trace(f"Logging out user {user}")

        room = self.get_room_of_user(user)
        if room:
            room.user_leaves(user)

        user.log_out()

        if not disconnected:
            self.send_packet_to(user, "log_out", {})

    def on_connect(self, sid: str) -> User:
        user = self.create_new_user_from_sid(sid)
        if not user:
            raise ValueError("No User object provided")

        self.send_packet_to(user, "user_connected", {
            "you": True,
            "users_logged_in": [user.get_account_jsonable()
                                for user in self.get_all_users() if user.is_logged_in()],
            "user_count": self.get_user_count()
        })

        account_list = []
        for account in self.accounts.get_entries_sorted(key=lambda e: e["username"]):
            jsonable = account.get_jsonable()
            jsonable["avatar_bytes"] = account.get_avatar_bytes()  # bytes are not actually jsonable
            account_list.append(jsonable)
        self.send_packet_to(user, "account_list", account_list)
        self.send_packet_to(user, "room_list", [room.get_data() for room in self.get_rooms()])

        self.send_packet_to_everyone("user_connected", {
            "you": False,
            "users_logged_in": [user.get_account_jsonable()
                                for user in self.get_all_users() if user.is_logged_in()],
            "user_count": self.get_user_count()
        }, skip=user)

        return user

    def on_disconnect(self, user: User):
        self.log_out_user(user, disconnected=True)

        self._users.remove(user)

        self.send_packet_to_everyone("user_disconnected", {
            "username": user.get_username(),
            "users_logged_in": [user.get_account_jsonable()
                                for user in self.get_all_users() if user.is_logged_in()],
            "user_count": self.get_user_count()
        })

    def reset_rooms(self, n_rooms=5):
        Log.info("Resetting rooms")
        for room in self._rooms:
            Log.trace(f"Dropping users out of room {room}")
            for user in room.get_users():
                room.user_leaves(user, skip_list_packet=True, skip_game_event=True)
                self.send_packet_to(user, "leave_room", {
                    "room_name": room.name
                })

        self.send_packet_to_everyone("room_list", [])

        self._rooms = []
        for _ in range(n_rooms):
            self._rooms.append(Room(self))

        self.send_packet_to_everyone("room_list", [room.get_data() for room in self.get_rooms()])

    def send_packet_to(self, users: Union[User, Set[User]], model: str, packet: Union[dict, list], skip: Union[User, Set[User]] = None):
        self.outgoing_packets_queue.put((users, model, packet, skip, self.get_next_packet_id()))

    def send_packet_to_everyone(self, model: str, packet: Union[dict, list], skip: Union[User, Set[User]] = None):
        self.send_packet_to(self.get_all_users(), model, packet, skip)
