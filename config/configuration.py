from dotenv import load_dotenv
import os
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials


from constants import DEFAULT_ENV_VARS_PATH, DRIVE_AUTH_ACCESS, SPREADSHEET_ACCESS, FILE_ACCESS


class EnvConfig:
    def __init__(self, env_path = DEFAULT_ENV_VARS_PATH):
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

class GoogleDriveAuth:
    def __init__(self, creds_path : Path):
        self.creds_path = creds_path
        self.scopes = [DRIVE_AUTH_ACCESS, SPREADSHEET_ACCESS, FILE_ACCESS]
        self.credentials = Credentials.from_service_account_file(
            creds_path,
            scopes=self.scopes
        )
        self.client = gspread.authorize(self.credentials)


    @classmethod
    def get_client(cls):
        env = EnvConfig()
        return cls(env.get("GDRIVE_CREDS_PATH", cast= Path))
    
# class GDriveAuthClient:
    # def __init__(self):
    #     self.env = EnvConfig()
    #     self.gdrive_auth = GoogleDriveAuth(env.get("GDRIVE_CREDS_PATH", cast= Path))