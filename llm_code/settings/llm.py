from calendar import month_name

MODEL_NAME = "defog/sqlcoder-7b-2"

MONTH_NAMES = [mn.lower() for mn in month_name[1:]]  # Full month names
MONTH_ABBREVIATIONS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]
ORDINAL_SUFFIXES = ["st", "nd", "rd", "th"]
