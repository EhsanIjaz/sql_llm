# import pandas as pd
# from pathlib import Path
# # import glob
# import streamlit as st
# import os


# from constants.data_costant import *
# # import str


# def get_latest_file(path: Path, pattern: str = "*"):
#     files_list = list(path.glob(pattern))

#     if not files_list:
#         raise FileNotFoundError(f"No File Avaliable for Data")
#     sorted_file_list = sorted(files_list, key=os.path.getmtime, reverse=True)

#     return sorted_file_list


# def clean_and_rename_file(path: Path):

#     sorted_file_list = get_latest_file(path)

#     for index, file_path in enumerate(sorted_file_list):
#         file_ext = os.path.splitext(file_path)[1]
#         if index == 0:
#             new_name = os.path.splitext(file_path)[0].split("/")[-1] + file_ext
#         else:
#             new_name = f"old_{index}" + file_ext

#         new_path = os.path.join(path, new_name)
#         os.rename(file_path, new_path)


# def keep_latest_5_files(path: Path):

#     sorted_file_list = get_latest_file(path)

#     if len(sorted_file_list) <= 5:
#         return
#     files_to_del = sorted_file_list[5:]
#     for file_path in files_to_del:
#         os.remove(file_path)
#         print(f"Deleted: {os.path.basename(file_path)}")


# def latest_file(path: Path, pattern: str = "*"):
#     print(type(path))
#     files = path.glob(pattern)
#     return max(files, key=lambda x: x.stat().st_mtime, default=None)

# @st.cache_data(show_spinner=False)
# def data_loader() -> pd.DataFrame:
#     """Load data with caching mechanism using PyArrow format."""
#     DATA_FILE = None

#     # Step 1: Check cached directory first
#     cached_latest = latest_file(CACHED_DIR)
#     if cached_latest:
#         DATA_FILE = cached_latest
#         logger.info(f"Cached file exists: {DATA_FILE}")

#     # Step 2: Check from the download directory
#     elif download_latest := latest_file(download_dir):
#         DATA_FILE = download_latest
#         logger.info(f"File exists in Download directory: {DATA_FILE}")

#     # Step 3: If no file in download, check S3 and download it
#     else:
#         downloaded_file = download_file_from_s3bucket(**hierarchy)
#         if downloaded_file:
#             DATA_FILE = downloaded_file
#             logger.info(f"File downloaded from S3: {DATA_FILE}")

#     # Step 4: If file not in S3, check upload directory and upload it
#     if DATA_FILE is None:
#         upload_latest = latest_file(upload_dir)
#         if upload_latest:
#             upload_from_local(upload_latest)  # Upload to S3
#             DATA_FILE = latest_file(download_dir)  # Get the latest downloaded file
#             logger.info(f"File uploaded from Upload directory: {DATA_FILE}")

#     # Step 5: Processed if the data file
#     if DATA_FILE:
#         if DATA_FILE.suffix == ".arrow":
#             logger.info("Loading cached data from Parquet")
#             return pd.read_parquet(DATA_FILE)
#         elif DATA_FILE.suffix == ".gz":
#             logger.info("Processing and caching new data")
#             df = load_and_process(DATA_FILE)
#             cache_filename = cached_dir.joinpath(f"{DATA_FILE.stem}.arrow")
#             df.to_parquet(cache_filename, compression="snappy")
#             return df
#     else:
#         # Step 6: If still no file, raise an error
#         raise FileNotFoundError("No valid file found in any directory!")




