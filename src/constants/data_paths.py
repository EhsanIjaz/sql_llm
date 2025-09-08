from pathlib import Path

FILE_PATH = Path(__file__).parent.parent.parent

COMPANY = "ebm"
COUNTRY = "pakistan"
CITY = "karachi"

DATA_PATH = FILE_PATH.joinpath("data")

LOG_PATH = FILE_PATH.joinpath("logs")


# Downloads , Upliads, Cached
DOWNLOADS_PATH = DATA_PATH.joinpath(f"downloads")
if not DOWNLOADS_PATH.exists():
    DOWNLOADS_PATH.mkdir(parents=True, exist_ok=True)
UPLOADS_PATH = DATA_PATH.joinpath(f"uploads")
CACHED_PATH = DATA_PATH.joinpath(f"cached")
if not CACHED_PATH.exists():
    CACHED_PATH.mkdir(parents=True, exist_ok=True)

# AWS UPLOAD PATH SETTING
REMOTE_DEFAULT_DATA_DIRECTORY = "_data"

