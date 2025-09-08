import os
import io
from pathlib import Path
from  typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

from config.gdrive_configuration import GoogleDriveAuth
from src.constants import DEFAULT_SHEET_NAME, G_FILES_FIELDS, FOLDER_KEY
from src.utils.logging import logger


def get_sheet(sheet_key : str , sheet_name : Optional[str] = None ):
    
    gdrive = GoogleDriveAuth.get_client()
    try:
        sheet = gdrive.client.open_by_key(sheet_key)
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
            fields=G_FILES_FIELDS,
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
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.info(f"Download progress: {int(status.progress() * 100)}%")
    
    logger.info(f"Download completed: {file_path}")
    return file_path


def upload_file_to_gdrive(local_file : Path ,folder_id = FOLDER_KEY, file_name: Optional[str] = None):
    if not local_file.exists:
        logger.error(f"File Not found {local_file.as_posix()}")
        raise FileNotFoundError (f"File Not found {local_file.as_posix()}")
    
    gdrive = GoogleDriveAuth.get_client()
    creds = gdrive.credentials
    service = build("drive", "v3", credentials=creds)

    try:
        file_metadata = {
            "name" : file_name or local_file.name,
            "parent": folder_id
        }
        media = MediaFileUpload (local_file.as_posix)
        response = (
            service.files().create(
                body =  file_metadata,
                mediabody = media,
                fields="id"
            ).execute()
        )

        logger.info(f"Uploaded file {local_file.name} to Google Drive folder {folder_id}")
        return True

    except Exception as e:
        logger.info(f"Failed to upload file to Google Drive: {str(e)}")
        return False
    