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
LATEST_LOG_FILENAME = ".latest.txt"
ENABLE_FILE_LOGGING = True
FILE_LOGGING_LEVEL = "WARN"


# Sound notifications
ERROR_SOUND_ENABLED = True
ERROR_SOUND_FILE_PATH = "backend/error.mp3"
ERROR_SOUND_NOTIFICATION_LEVEL = "WARN"
ERROR_SOUND_IGNORE_LEVELS: list = ["TEST"]


# Songs
POPULAR_SONGS_RATIO_MIN = 0.5
SONG_MAX_DURATION = 1200  # seconds
LOG_IN_TO_REQUEST_SONG = True  # todo impl check
YOUTUBE_ID_CHARACTERS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
YOUTUBE_ID_LENGTH = 11
YOUTUBE_ID_REGEX_PATTERN = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?(?P<id>[A-Za-z0-9\-=_]{11})"


# Trello
TRELLO_BOARD_ID = "603c469a39b5466c51c3a176"
TRELLO_LIST_ID = "60587b1f02721f0c7b547f5b"


# Account creation
USERNAME_VALID_CHARACTERS = "0123456789abcdefghijklmnopqrstuvwxyz"
USERNAME_MAX_LENGTH = 16
RANDOM_MONEY_MIN = 1e3
RANDOM_MONEY_MAX = 1e6