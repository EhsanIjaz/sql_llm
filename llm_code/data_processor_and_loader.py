import re
import hashlib
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path
from typing import Tuple


from .aws.funcs import *
from .settings import *
from .settings.data import COLUMNS_MAP
from .common_utils.logging import logger
from .utils.decorators import time_checker

# Configure display options
pd.options.display.float_format = "{:,.2f}".format
pd.options.mode.chained_assignment = None


CLEAN_REGEX = re.compile(r"[\W_-]+")
DEFAULT_FILL_VALUE = "UNK"

# Hierarchy for S3 bucket path
hierarchy: dict = {"company": COMPANY, "country": COUNTRY, "city": CITY}


def clean_column_values(value: str) -> str:
    """Clean and standardize string values in DataFrame columns."""
    if not isinstance(value, str):
        return DEFAULT_FILL_VALUE
    return CLEAN_REGEX.sub(" ", value).strip().lower()


def optimize_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame memory usage by downcasting numeric types."""
    # Downcast numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, downcast="integer")

    # Convert string columns to category type where appropriate
    for col in ["territory", "category", "brand", "sku"]:
        if col in df.columns and df[col].nunique() < 1000:
            df[col] = df[col].astype("category")

    return df


def load_and_process(file_path: Path) -> pd.DataFrame:
    """Load and process raw data from compressed CSV."""
    try:
        df = pd.read_csv(file_path, compression="gzip", low_memory=False)

        # Validate required columns
        missing_cols = [col for col in COLUMNS_MAP if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        df = df[list(COLUMNS_MAP.keys())].rename(columns=COLUMNS_MAP)

        # Clean string columns
        str_cols = df.select_dtypes(include=["object", "category"]).columns
        df[str_cols] = df[str_cols].apply(lambda x: x.map(clean_column_values))
        df[str_cols] = df[str_cols].fillna(DEFAULT_FILL_VALUE)

        # Handle numeric columns
        num_cols = df.select_dtypes(include=np.number).columns
        df[num_cols] = df[num_cols].fillna(0).astype(np.int32)

        df = df.replace({True: 1, False: 0})

        return optimize_data_types(df)

    except Exception as e:
        logger.error(f"Data loading failed: {str(e)}")
        raise


def latest_month_year(df: pd.DataFrame) -> Tuple[int, int]:
    """Get latest available month and year from the data."""
    return df.month.max(), df.year.max()


def upload_from_local(local_file: Path):
    if local_file.exists() and local_file.suffix in [".csv", ".gz", ".gzip"]:
        local_md5 = hashlib.md5(open(local_file, "rb").read()).hexdigest()
        remote_filename = f"{local_md5}{local_file.suffix}"

        if not isin_s3bucket(filename=remote_filename, **hierarchy):
            upload_file_to_s3bucket(
                local_file, remote_filename=remote_filename, **hierarchy
            )
            logger.info(f"File uploaded to S3: {remote_filename}")
            logger.info(f"File uploaded to S3: {remote_filename}")


def enforce_single_file(dir_path: Path):
    files = [file for file in dir_path.iterdir() if file.is_file()]  # List all files
    if len(files) > 1:
        latest = max(files, key=lambda x: x.stat().st_ctime)  # Get latest file
        for file in files:
            if file != latest:
                file.unlink()  # Delete old files
                logger.info(f"Deleted old file: {file}")


def latest_file(path: Path, pattern: str = "*"):
    files = path.glob(pattern)
    return max(files, key=lambda x: x.stat().st_ctime, default=None)


@st.cache_data(show_spinner=False)
@time_checker
def data_loader() -> pd.DataFrame:
    """Load data with caching mechanism using PyArrow format."""
    DATA_FILE = None

    # Step 1: Check cached directory first
    cached_latest = latest_file(cached_dir)
    if cached_latest:
        DATA_FILE = cached_latest
        logger.info(f"Cached file exists: {DATA_FILE}")

    # Step 2: Check from the download directory
    elif download_latest := latest_file(download_dir):
        DATA_FILE = download_latest
        logger.info(f"File exists in Download directory: {DATA_FILE}")

    # Step 3: If no file in download, check S3 and download it
    else:
        downloaded_file = download_file_from_s3bucket(**hierarchy)
        if downloaded_file:
            DATA_FILE = downloaded_file
            logger.info(f"File downloaded from S3: {DATA_FILE}")

    # Step 4: If file not in S3, check upload directory and upload it
    if DATA_FILE is None:
        upload_latest = latest_file(upload_dir)
        if upload_latest:
            upload_from_local(upload_latest)  # Upload to S3
            DATA_FILE = latest_file(download_dir)  # Get the latest downloaded file
            logger.info(f"File uploaded from Upload directory: {DATA_FILE}")

    # Step 5: Processed if the data file
    if DATA_FILE:
        if DATA_FILE.suffix == ".arrow":
            logger.info("Loading cached data from Parquet")
            return pd.read_parquet(DATA_FILE)
        elif DATA_FILE.suffix == ".gz":
            logger.info("Processing and caching new data")
            df = load_and_process(DATA_FILE)
            cache_filename = cached_dir.joinpath(f"{DATA_FILE.stem}.arrow")
            df.to_parquet(cache_filename, compression="snappy")
            return df
    else:
        # Step 6: If still no file, raise an error
        raise FileNotFoundError("No valid file found in any directory!")

    # **Step 7: Cleanup old files to ensure only one file per directory**
    enforce_single_file(cached_dir)
    enforce_single_file(download_dir)
    enforce_single_file(upload_dir)
