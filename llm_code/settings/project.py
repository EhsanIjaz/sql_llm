from pathlib import Path

FILE_PATH = Path(__file__)

COMPANY = "ebm"
COUNTRY = "pakistan"
CITY = "karachi"

# UPLOAD PATH SETTING
REMOTE_DEFAULT_DATA_DIRECTORY = "_data"

MAX_HISTORY_LENGTH = 10

# sql_gen_and_exec
MODEL_CHACHED_DIR = "/workspace"

# querry_runner
LETTER_LIMIT = 22

# DOWNLOAD PATH SETTING
AWS_DOWNLOAD_PATH = FILE_PATH.parent.parent.joinpath("data/downloads")
if not AWS_DOWNLOAD_PATH.exists():
    AWS_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)


# UPLOAD PATH SETTING
LOCAL_DOWNLOAD_PATH = FILE_PATH.parent.parent.joinpath("data/uploads")
if not LOCAL_DOWNLOAD_PATH.exists():
    LOCAL_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
