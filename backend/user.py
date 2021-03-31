from convenience import *
from account import Account


class User:
    def __init__(self, sid: str):
        self.sid = sid
        self._account: Union[Account, None] = None  # Union for editor type hints
        self._game_data: Union[dict, None] = None
        self.pinged_timestamp = 0
        self.latency = 0
        Log.trace(f"Created new User object for SID '{sid}'")

    def __repr__(self):
        return f"<User {self}, account: {self._account}>"

    def __str__(self):
        if self._account:
            return f"'{self._account['username']}/{self.sid}'"

        else:
            return f"'{self.sid}'"

    def clear_game_data(self):
        self._game_data = None

    def get_account(self):
        return self._account

    def get_account_data_copy(self, filter_sensitive=True) -> dict:
        if self._account:
            return self._account.get_data_copy(filter_sensitive=filter_sensitive)

    def get_game_data_copy(self, filter_sensitive=True) -> dict:
        if self._game_data:
            game_data = self._game_data.copy()
            if filter_sensitive:
                for key in []:
                    game_data[key] = "<filtered>"

            return game_data

    def get_username(self) -> str:
        """Returns None if user is not logged in"""

        if self._account:
            return self._account["username"]

    def has_game_data(self) -> bool:  # todo use this to prevent TypeError because it's None
        if self._game_data:
            return True

        return False

    def is_logged_in(self) -> bool:
        if self._account:
            return True

        return False

    def log_in(self, account: Account):
        self._account = account
        Log.info(f"{self} logged in")
        return

    def log_out(self):
        self._account = None
        Log.info(f"{self} logged out")
        return

    def set_game_data(self, data: dict):
        self._game_data = data


class FakeUser(User):
    def __init__(self, sid=""):
        super().__init__(sid)
        Log.trace("Fake user created")
