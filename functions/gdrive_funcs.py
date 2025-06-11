import os
import io

from config.configuration import GoogleDriveAuth
from constants import DEFAULT_SHEET_NAME, G_FILES_FIELDS
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from common_utils.logging import logger

def get_sheet(sheet_key : str , sheet_name : str = "" ):
    
    gdrive = GoogleDriveAuth.get_client()
    try:
        sheet = gdrive.client.open_by_key(sheet_key)
    
        worksheet = sheet.worksheet(sheet_name) # With sheet name
        worksheet = sheet.worksheet(sheet_name or DEFAULT_SHEET_NAME) # default sheet
        return worksheet.get_all_records()
    except Exception as e:
        logger.error(f"Failed to fetch Google Sheet: {e}")
        raise ValueError(f"Sheet key or name not found: {e}")
    

def get_latest_file(folder_key: str, download_path: str):

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
            fields=G_FILES_FIELDS,  # <- add this
        )
        .execute()
    )

    files = response.get("files", [])
    if not files:
        logger.warning("No files found in the specified folder.")
        raise FileNotFoundError("No file found in the Google Drive folder.")

    file = files[0]
    mime_type = file["mimeType"]
    file_id = file["id"]
    file_name = file["name"]
    file_path = os.path.join(download_path, file_name)

    if os.path.exists(file_path):
        logger.info(f"File already exists: {file_name}. Skipping download.")
        return file_path

    if mime_type.startswith("application/vnd.google-apps"):
        logger.error(f"Google Docs file cannot be downloaded directly: {file_name}")
        raise ValueError(f"Cannot download Google Docs file: {file_name}")
    
    request = service.files().get_media(fileId=file_id)
    with open(file_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        print(downloader)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.info(f"Download progress: {int(status.progress() * 100)}%")
    
    logger.info(f"Download completed: {file_path}")
    return file_path
