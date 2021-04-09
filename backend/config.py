# SocketIO settings
HOST = "0.0.0.0"
PORT = 777


# Startup
STARTUP_EMPTY_FRONTEND_CACHE = False
STARTUP_CLEANUP_BACKEND_CACHE = True
DELAY_BEFORE_RESTART = 60  # seconds


# User pinging
PING_USERS_ENABLED = False
PING_USERS_INTERVAL = 5  # seconds
PONG_DELAY_BEFORE_TIMEOUT = 5  # todo fix: timeout < interval should be possible


# What to log
LOG_SOCKETIO = False
LOG_ENGINEIO = False
LOG_WSGI = False
LOG_YOUTUBE_DL_VERBOSE = False
LOG_YOUTUBE_DL_WARNINGS = False
FFMPEG_LOGGING_LEVEL = "warning"  # https://ffmpeg.org/ffmpeg.html CTRL+F "loglevel"


# Console logging
CONSOLE_LOGGING_LEVEL = "TRACE"
CONSOLE_LOGGING_LENGTH_CUTOFF = 800


# Data storage
BACKEND_DATA_FOLDER = "backend/data"
FRONTEND_CACHE_FOLDER = "frontend/public/cache"
SONGS_FOLDER = "songs"
AVATARS_FOLDER = "avatars"


# File logging
LOGS_FOLDER = "backend/logs"
LATEST_LOG_FILENAME = ".latest.log"
ENABLE_FILE_LOGGING = True
FILE_LOGGING_LEVEL = "WARN"


# Sound notifications
ERROR_SOUND_FILE_PATH = "backend/logs/error.mp3"
ERROR_SOUND_NOTIFICATION_LEVEL = "WARN"
ERROR_SOUND_IGNORE_LEVELS: list = ["TEST"]


# Songs
SONG_MAX_DURATION = 600  # seconds
LOG_IN_TO_REQUEST_SONG = True  # todo impl check


# Trello
TRELLO_BOARD_ID = "603c469a39b5466c51c3a176"
TRELLO_LIST_ID = "60587b1f02721f0c7b547f5b"


# Account creation
USERNAME_VALID_CHARACTERS = "abcdefghijklmnopqrstuvwxyz0123456789"
USERNAME_MAX_LENGTH = 16
RANDOM_MONEY_MIN = 1e3
RANDOM_MONEY_MAX = 1e6
