from pathlib import Path
import logging
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
import os
import glob
from dotenv import load_dotenv
from constants import DEFAULT_ENV_VARS_PATH

from ..settings.aws import *


load_dotenv(DEFAULT_ENV_VARS_PATH)
AWS_LLM_BUCKET = os.getenv("AWS_LLM_BUCKET")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_SERVER_PUBLIC_KEY"),
    aws_secret_access_key=os.getenv("AWS_SERVER_SECRET_KEY"),
)


def upload_file(
    local_path: Path, remote_path: Path, bucket_name: str = AWS_LLM_BUCKET
) -> bool:
    """Upload a file to an S3 bucket

    :param local_file: File to upload
    :param bucket_name: Bucket to upload to
    :param remote_path: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    if not local_path.exists():
        e = f"The file you are trying to upload can't be found on this path {local_path.as_posix()}."
        logging.error(e)
        return False

    try:
        response = s3_client.upload_file(
            local_path.as_posix(), bucket_name, remote_path.as_posix()
        )
    except ClientError as e:
        logging.error(e)
        return False
    return True


def downlaod_file(
    remote_path: Path, local_path: Path, bucket_name: str = AWS_LLM_BUCKET
):
    """Upload a file to an S3 bucket

    :param remote_path: File path on s3  bucket
    :param bucket_name: bucket to download from
    :param local_path: where to download the file, this will not create directory we have to do our selve
    :return: True if file was uploaded, else False
    """

    if not local_path.parent.exists():
        e = f"The path where you are trying to download this file doesn't exist {local_path.parent.as_posix()}."
        logging.error(e)
        return False

    try:
        chunk_size = 33_554_432
        tc = TransferConfig(
            multipart_threshold=chunk_size,
            max_concurrency=10,
            multipart_chunksize=chunk_size,
            use_threads=True,
        )
        with open(local_path.as_posix(), "wb") as data:
            s3_client.download_fileobj(
                Bucket=bucket_name, Key=remote_path.as_posix(), Fileobj=data, Config=tc
            )
            return True
    except ClientError as e:
        raise (e)


def delete_file(remote_path: Path, bucket_name: str = AWS_LLM_BUCKET):
    """Upload a file to an S3 bucket

    :param remote_path: File path on s3  bucket
    :param bucket_name: bucket to download from
    :param local_path: where to download the file, this will not create directory we have to do our selve
    :return: True if file was uploaded, else False
    """
    try:
        response = s3_client.delete_object(
            Bucket=bucket_name, Key=remote_path.as_posix()
        )
        return True
    except ClientError as e:
        logging.error(e)
        return False


def delete_files(remote_path: Path, bucket_name: str = AWS_LLM_BUCKET):
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name, Prefix=remote_path.as_posix()
        )
        if response.get("Contents"):
            # objects to delete
            objs = [{"Key": o["Key"]} for o in response["Contents"]]
            response = s3_client.delete_objects(
                Bucket=bucket_name, Delete={"Objects": objs, "Quiet": False}
            )

            return True
    except Exception as ex:
        e = f"Unable to delete files from remote directory {remote_path.as_posix()}"
        logging.error(e)
        return False


def list_files(remote_path: Path, bucket_name: str = AWS_LLM_BUCKET) -> list[dict]:
    get_last_modified = lambda obj: int(obj["LastModified"].strftime("%s"))
    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name, Prefix=remote_path.as_posix()
        )
        if response.get("Contents"):
            objs = response["Contents"]
            return [
                {"filename": f["Key"], "last_modified": f["LastModified"]}
                for f in sorted(objs, key=get_last_modified)
            ]
    except Exception as e:
        raise Exception(f"Error while listing files of bucket under path {remote_path}")


def get_last_added_remote_file(remote_path: Path, bucket_name: str = AWS_LLM_BUCKET):
    """Upload a file to an S3 bucket

    :param remote_path: File path on s3  bucket
    :param bucket_name: bucket to download from
    :param local_path: where to download the file, this will not create directory we have to do our selve
    :return: True if file was uploaded, else False
    """

    get_last_modified = lambda obj: int(obj["LastModified"].strftime("%s"))

    try:
        response = s3_client.list_objects_v2(
            Bucket=bucket_name, Prefix=remote_path.as_posix()
        )
        if response.get("Contents"):
            objs = response["Contents"]
            last_added_obj = sorted(objs, key=get_last_modified)[0].get("Key", None)
            return last_added_obj
        else:
            return False
    except ClientError as e:
        logging.error(e)
        return False
