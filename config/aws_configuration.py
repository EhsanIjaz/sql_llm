import os
from pathlib import Path
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

from common_utils.logging import logger
from config.configuration import EnvConfig
from constants import DEFAULT_ENV_VARS_PATH


class AWSConfig:

    _client = None #for singleton
    _bucket_name = None #for singleton

    def __init__(self, env_path : Path = DEFAULT_ENV_VARS_PATH):
        self.env = EnvConfig(env_path)
        self._bucket_name = self.env.get("AWS_LLM_BUCKET")

    @classmethod
    def get_client(cls, env_path: Path = DEFAULT_ENV_VARS_PATH):
        if cls._client is None:
            env = EnvConfig(env_path)
            access_key = env.get("AWS_SERVER_PUBLIC_KEY")
            secret_key = env.get("AWS_SERVER_SECRET_KEY")
            region_name = env.get("AWS_REGION")

            if not access_key or not secret_key or not region_name:
                raise ValueError("AWS credentials are missing.")
            
            try:
                cls._client = boto3.client(
                    "s3",
                    aws_access_key_id = access_key,
                    aws_secret_access_key = secret_key,
                    region_name = region_name
                )
                cls._bucket_name = env.get("AWS_LLM_BUCKET")

            except ClientError as e:
                raise ClientError(f"Failed to create S3 client: {str(e)}", operation_name="create_s3_client")
        return cls._client


    @property
    def bucket_name(self)-> str:
        if not self._bucket_name:
            raise ValueError("AWS_LLM_BUCKET is not set in environment variables.")
        return self._bucket_name



    def upload_file(self, local_path: Path, remote_path: Path) -> bool:
        if not local_path.exists():
            logger.error(f"File not found: {local_path}")
            return False

        try:
            self.get_client().upload_file(
                local_path.as_posix(), self.bucket_name, remote_path.as_posix()
            )
            return True
        except ClientError as e:
            logger.error(e)
            return False


    def download_file(self, remote_path: Path, local_path: Path) -> bool:
        if not local_path.parent.exists():
            logger.error(f"Target directory does not exist: {local_path.parent}")
            return False

        try:
            config = TransferConfig(
                multipart_threshold=33_554_432,
                max_concurrency=10,
                multipart_chunksize=33_554_432,
                use_threads=True,
            )
            with open(local_path.as_posix(), "wb") as data:
                self.get_client().download_fileobj(
                    Bucket=self.bucket_name,
                    Key=remote_path.as_posix(),
                    Fileobj=data,
                    Config=config,
                )
            return True
        except ClientError as e:
            logger.error(e)
            return False

    def delete_file(self, remote_path: Path) -> bool:
        try:
            self.get_client().delete_object(
                Bucket=self.bucket_name, Key=remote_path.as_posix()
            )
            return True
        except ClientError as e:
            logger.error(e)
            return False

    def delete_files(self, remote_path: Path) -> bool:
        try:
            response = self.get_client().list_objects_v2(
                Bucket=self.bucket_name, Prefix=remote_path.as_posix()
            )
            if response.get("Contents"):
                objs = [{"Key": o["Key"]} for o in response["Contents"]]
                self.get_client().delete_objects(
                    Bucket=self.bucket_name, Delete={"Objects": objs, "Quiet": False}
                )
                return True
            return False
        except ClientError as e:
            logger.error(e)
            return False

    def list_files(self, remote_path: Path) -> list[dict]:
        get_last_modified = lambda obj: int(obj["LastModified"].timestamp())
        try:
            response = self.get_client().list_objects_v2(
                Bucket=self.bucket_name, Prefix=remote_path.as_posix()
            )
            if response.get("Contents"):
                objs = response["Contents"]
                return sorted(
                    [
                        {"filename": f["Key"], "last_modified": f["LastModified"]}
                        for f in objs
                    ],
                    key=get_last_modified,
                )
            return []
        except ClientError as e:
            raise RuntimeError(f"Error while listing files: {e}")

    def get_last_added_remote_file(self, remote_path: Path):
        get_last_modified = lambda obj: int(obj["LastModified"].timestamp())

        try:
            response = self.get_client().list_objects_v2(
                Bucket=self.bucket_name, Prefix=remote_path.as_posix()
            )
            if response.get("Contents"):
                objs = response["Contents"]
                last_added_obj = sorted(objs, key=get_last_modified)[-1].get("Key", None)
                return last_added_obj
            return None
        except ClientError as e:
            logger.error(e)
            return None