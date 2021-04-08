from convenience import *

from accounts import Accounts
from songs import Song, Songs
from room import Room
from user import User

from games.coinflip import Coinflip


class Shove:
    def __init__(self, sio):
        Log.trace("Initializing Shove")
        self.sio: socketio.Server = sio
        self.incoming_packets_queue = Queue()  # (User, model, packet, packet_number)
        self.outgoing_packets_queue = Queue()  # ([User], model, packet, skip, is_response)

        self._default_game = Coinflip
        self._next_bot_number = 0
        self._next_packet_number = 0
        self._users: Set[User] = set()
        self._rooms: Set[Room] = set()

        self.accounts = Accounts()
        self.songs = Songs()

        self.reset_rooms(2)
        # self.rooms[0].add_bot(3)
        # for i in range(1):
        #     self.get_rooms()[0].try_to_start_game()

        if PRIVATE_ACCESS:
            Log.trace("Initializing Trello client, fetching card list")
            client = TrelloClient(
                api_key=TRELLO_API_KEY,
                api_secret=TRELLO_API_SECRET,
                token=TRELLO_TOKEN
            )
            board = client.get_board(TRELLO_BOARD_ID)
            self._trello_card_list = board.get_list(TRELLO_LIST_ID)
        else:
            Log.trace("No private access, not initializing Trello client")

        # todo implement non-subprocess version of YT DL
        # youtube_dl_options = {
        #     "verbose": True,
        #     "listformats": True,
        #     "prefer_ffmpeg": True,
        # }
        # self.youtube_dl = youtube_dl.YoutubeDL(youtube_dl_options)
        # self.youtube_dl.download([f"https://youtube.com/watch?v={youtube_id}"])

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

    def get_next_bot_number(self) -> int:
        self._next_bot_number += 1
        return self._next_bot_number

    def get_next_packet_number(self) -> int:
        self._next_packet_number += 1
        return self._next_packet_number

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

        Log.warn(f"No user matched with SID: {sid}")

    def get_user_count(self) -> int:
        return len(self._users)

    def log_out_user(self, user):
        Log.trace(f"Logging out user {user}")

        room = self.get_room_of_user(user)
        if room:
            room.user_leave(user)

        user.log_out()
        Log.trace(f"User {user} logged out")

        self.send_packet_to(user, "log_out", {})

    def on_connect(self, sid: str) -> User:
        user = self.create_new_user_from_sid(sid)
        if not user:
            raise ValueError("No User object provided")

        self.send_packet_to(user, "user_connected", {
            "you": True,
            "users": [user.get_account_data_copy()
                      for user in self.get_all_users() if user.is_logged_in()],
            "user_count": self.get_user_count()
        })

        self.send_packet_to_everyone("user_connected", {
            "you": False,
            "users": [user.get_account_data_copy()
                      for user in self.get_all_users() if user.is_logged_in()],
            "user_count": self.get_user_count()
        }, skip=user)

        return user

    def on_disconnect(self, user: User):  # todo disconnect reasons
        self.log_out_user(user)

        self._users.remove(user)

        self.send_packet_to_everyone("user_disconnected", {
            "username": user.get_username(),
            "users": [user.get_account_data_copy()
                      for user in self.get_all_users() if user.is_logged_in()],
            "user_count": self.get_user_count()
        })

    def reset_rooms(self, n_rooms=5):
        Log.info("Resetting rooms")
        self._rooms = []  # todo handle removing users from room
        for _ in range(n_rooms):
            self._rooms.append(Room(self))

    def send_packet_to(self, users: Union[User, Iterable[User]], model: str, packet: dict, skip: Union[User, List[User]] = None, is_response=False):
        self.outgoing_packets_queue.put((users, model, packet, skip, is_response))

    def send_packet_to_everyone(self, model: str, packet: dict, skip: Union[User, List[User]] = None):
        self.send_packet_to(self.get_all_users(), model, packet, skip)
