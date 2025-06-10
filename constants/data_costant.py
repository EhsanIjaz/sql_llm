from pathlib import Path

SCRIPT_DIR = Path(__file__).parent  # aisight_llm/settings


DATA_DIR = SCRIPT_DIR.parent.joinpath("data")  # sql_llm/data
LOG_DIR = SCRIPT_DIR.parent.joinpath("logs")

DOWNLOAD_DIR = DATA_DIR.joinpath(f"downloads")
CACHED_DIR = DATA_DIR.joinpath(f"cached")
# download_dir = DATA_DIR.joinpath(f"downloads")

# /home/ehsan/Documents/Ehsan/sql_llm/data/downloads/llm_dataset_v9_2_2.gz