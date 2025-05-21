from pathlib import Path

from .repository import *
from ..settings.project import *
from aisight_llm.common_utils.logging import logger


def upload_file_to_s3bucket(
    local_file: Path, company: str, country: str, city: str, remote_filename: str = ""
):
    if local_file.exists():
        if not remote_filename:
            local_filename = local_file.name
            remote_filepath: Path = (
                Path(company.lower())
                .joinpath(country.lower())
                .joinpath(city.lower())
                .joinpath(REMOTE_DEFAULT_DATA_DIRECTORY)
                .joinpath(local_filename)
            )
        else:
            remote_filepath: Path = (
                Path(company.lower())
                .joinpath(country.lower())
                .joinpath(city.lower())
                .joinpath(REMOTE_DEFAULT_DATA_DIRECTORY)
                .joinpath(remote_filename)
            )

        logger.info(f"Local File Path: {local_file.as_posix()}")
        logger.info(f"Remote File Path: {remote_filepath.as_posix()}")

        if upload_file(remote_path=remote_filepath, local_path=local_file):
            logger.info("File Upload Status: SUCCESS")
        else:
            logger.info("File Upload Status: FAILED")


def download_file_from_s3bucket(
    company: str,
    country: str,
    city: str,
    remote_path: Path | None = None,
    save_path: Path = AWS_DOWNLOAD_PATH,
):
    if not save_path.exists():
        # create save directory as per the path mentioned
        save_path.mkdir(parents=True, exist_ok=True)

    if not remote_path:
        remote_directory: Path = (
            Path(company.lower())
            .joinpath(country.lower())
            .joinpath(city.lower())
            .joinpath(REMOTE_DEFAULT_DATA_DIRECTORY)
        )

        # last added remote path is considered as path to remote file
        if last_added_remote_file := get_last_added_remote_file(
            remote_path=remote_directory
        ):
            last_added_remote_file: Path = Path(last_added_remote_file)
            save_path = save_path.joinpath(last_added_remote_file.name)

            logger.info(f"Remote File Path: {last_added_remote_file.as_posix()}")
            logger.info(f"Local File Path: {save_path.as_posix()}")

            if downlaod_file(local_path=save_path, remote_path=last_added_remote_file):
                logger.info("File Download Status: SUCCESS")
                return save_path
            else:
                logger.info("File Download Status: FAILED")
                return None


def list_files_in_s3bucket(
    company: str, country: str, city: str, remote_path: Path | None = None
):
    if remote_path:
        remote_directory = remote_path
    else:
        remote_directory: Path = (
            Path(company.lower())
            .joinpath(country.lower())
            .joinpath(city.lower())
            .joinpath(REMOTE_DEFAULT_DATA_DIRECTORY)
        )

    return list_files(remote_path=remote_directory)


def isin_s3bucket(filename: Path, company: str, country: str, city: str):
    s3_files = list_files_in_s3bucket(company=company, country=country, city=city)
    if s3_files:
        for s3_file in s3_files:
            if s3_filename := s3_file.get("Key"):
                if Path(s3_filename).stem == filename.stem:
                    return True
        return False
