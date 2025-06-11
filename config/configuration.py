from dotenv import load_dotenv
import os
from pathlib import Path

from constants import DEFAULT_ENV_VARS_PATH


class EnvConfig:
    def __init__(self, env_path : Path = DEFAULT_ENV_VARS_PATH):
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            raise FileNotFoundError(f"Couldn't find env file at {env_path}")

    def get(self, key, default=None, cast=str):
        val = os.getenv(key, default)
        try:
            return cast(val)
        except (ValueError, TypeError):
            return default
