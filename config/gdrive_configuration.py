from dotenv import load_dotenv
import os
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials


from config.configuration import EnvConfig
from src.constants import DRIVE_AUTH_ACCESS, SPREADSHEET_ACCESS, FILE_ACCESS


class GoogleDriveAuth:
    def __init__(self, creds_path : Path):
        self.creds_path = creds_path
        self.scopes = [DRIVE_AUTH_ACCESS, SPREADSHEET_ACCESS, FILE_ACCESS]
        self.scopes = [DRIVE_AUTH_ACCESS, SPREADSHEET_ACCESS]
        self.credentials = Credentials.from_service_account_file(
            creds_path,
            scopes=self.scopes
        )
        self.client = gspread.authorize(self.credentials)


    @classmethod
    def get_client(cls):
        env = EnvConfig()
        return cls(env.get("GDRIVE_CREDS_PATH", cast= Path))
