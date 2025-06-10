import os
import io

from config.configuration import GoogleDriveAuth
from constants import DEFAULT_SHEET_NAME, G_FILES_FIELDS

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload



def get_sheet(sheet_key : str , sheet_name : str ):
    gdrive = GoogleDriveAuth.get_client()
    try:
        sheet = gdrive.client.open_by_key(sheet_key)
    except Exception as e:
        raise ValueError (f"Sheet name not found: {e}")
    #need the sheet key check
    if sheet_name:
        worksheet = sheet.worksheet(sheet_name) # With sheet name
    else:
        print("yes")
        sheet_name = DEFAULT_SHEET_NAME
        worksheet = sheet.worksheet(sheet_name) # default sheet
    return worksheet.get_all_records()

def get_folder(folder_key: str, download_path: str):

    gdrive = GoogleDriveAuth.get_client()
    creds = gdrive.credentials
    os.makedirs(download_path, exist_ok=True)
    service = build("drive","v3", credentials=creds)
    query = f"'{folder_key}' in parents and trashed = false"
    response = service.files().list(q=query,fields=G_FILES_FIELDS).execute()
    files = response.get("files", [])
    file_name = files[-1]['name']
    file_path = f"{download_path}/{file_name}"
    if not os.path.exists(file_path):
        request = service.files().get_media(fileId=folder_key)
        with open(file_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            print(downloader)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download progress: {int(status.progress() * 100)}%")
    else:
        print(f"{file_name} already exists. Skipping download.")
        print(f"{file_name} already exists. Skipping download.")
def get_sheet(sheet_key: str, sheet_name: str):
    gdrive = GoogleDriveAuth.get_client()
    try:
        sheet = gdrive.client.open_by_key(sheet_key)
        if sheet_name:
            worksheet = sheet.worksheet(sheet_name)  # With sheet name
        else:
            print("yes")
            sheet_name = DEFAULT_SHEET_NAME
            worksheet = sheet.worksheet(sheet_name)  # default sheet
        return worksheet.get_all_records()
    except Exception as e:
        raise ValueError(f"Sheet key not found: {e}")


def get_files(folder_key: str, download_path: str):

    gdrive = GoogleDriveAuth.get_client()
    creds = gdrive.credentials

    os.makedirs(download_path, exist_ok=True)

    service = build("drive", "v3", credentials=creds)
    query = f"'{folder_key}' in parents and trashed = false"
    response = (
        service.files()
        .list(
            q=query,
            orderBy="modifiedTime desc",
            pageSize=1,
            fields="files(id, name, mimeType)",  # <- add this
        )
        .execute()
    )

    files = response.get("files", [])
    if not files:
        raise FileNotFoundError(f"No file found in the gdrive folder")

    file = files[0]
    mime_type = file["mimeType"]
    file_id = file["id"]
    file_name = file["name"]
    file_path = os.path.join(download_path, file_name)

    if os.path.exists(file_path):
        print("FILE EXISTS")
        return file_path

    if mime_type.startswith("application/vnd.google-apps"):
        raise ValueError(f"Cannot download Google Docs file: {file_name} — must use export.")
    else:
        request = service.files().get_media(fileId=file_id)
    with open(file_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        print(downloader)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")
    return file_path