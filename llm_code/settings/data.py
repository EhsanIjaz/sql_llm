from pathlib import Path

SCRIPT_DIR = Path(__file__).parent  # aisight_llm/settings
DATA_DIR = SCRIPT_DIR.parent.joinpath("data")  # aisight_llm/data
LOG_DIR = SCRIPT_DIR.parent.joinpath("logs")

download_dir = DATA_DIR.joinpath(f"downloads")
download_dir.mkdir(parents=True, exist_ok=True)

upload_dir = DATA_DIR.joinpath(f"uploads")
upload_dir.mkdir(parents=True, exist_ok=True)

cached_dir = DATA_DIR.joinpath(f"cached")
cached_dir.mkdir(parents=True, exist_ok=True)

COLUMNS_MAP = {
    # datetime information
    "month": "month",
    "year": "year",
    # product information
    "brand": "brand",
    "sku": "sku",
    "variant": "variant",
    "packtype": "packtype",
    # quantitaive columns
    "sales": "sales",
    "primary sales": "primary sales",
    "target": "target",
    # location specific information
    "region": "region",
    "city": "city",
    "area": "area",
    "territory": "territory",
    "distributor": "distributor",
    "route": "route",
    "customer": "customer",
    # analysis columns
    "mro": "mro",
    "mto": "mto",
    "unproductive_mro": "unproductive_mro",
    "unassorted_mro": "unassorted_mro",
    "stockout_mro": "stockout_mro",
    "productivity": "productivity",
    "stockout": "stockout",
    "assortment": "assortment",
}

DEFAULT_FILL_VALUE = "UNK"
