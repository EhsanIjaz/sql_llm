from calendar import month_name

MODEL_NAME = "defog/sqlcoder-7b-2"

MONTH_NAMES = [mn.lower() for mn in month_name[1:]]  # Full month names
MONTH_ABBREVIATIONS = [ "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
ORDINAL_SUFFIXES = ["st", "nd", "rd", "th"]


# Configuration constants
CONFIG_ROOT = 'config'
DEFAULT_ENV_VARS_PATH = f'{CONFIG_ROOT}/config.env'
DEFAULT_CONFIG_PATH = f'{CONFIG_ROOT}/config.yaml'


# Google Drive Authentication
DRIVE_AUTH = 'https://www.googleapis.com/auth/'
DRIVE_AUTH_ACCESS = f'{DRIVE_AUTH}drive'
SPREADSHEET_ACCESS = f'{DRIVE_AUTH}spreadsheets'
FILE_ACCESS = f'{DRIVE_AUTH}drive.file'


# Google Keys change according to requirment
SHEET_KEY = "1nXfeo4T0tYvkI27PULbuZo9efzvGNRQv38efiK-d0go"
FOLDER_KEY = "1X4LJMxPokd0wmU1AojmrlhmVpWRV7Ywh"
DEFAULT_SHEET_NAME = "Sheet1"

G_FILES_FIELDS = "files(id, name, mimeType, size)"


# Streamlit stetting 
MAX_HISTORY_LENGTH = 10
MAX_CONTENT_LENGTH = 5
LETTER_LIMIT = 22

# sql_gen_and_exec
MODEL_CHACHED_DIR = "/workspace"

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


MODE_DISPLAY = {
    "Single Query Mode": "Single Query",
    "Contextual Conversation": "Contextual Query"
}