import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
from ..settings import LOG_DIR


os.makedirs(LOG_DIR, exist_ok=True)
log_filepath = os.path.join(LOG_DIR, "llm_running_logs.log")
logging_format = "%(asctime)s: %(levelname)s: %(module)s: %(message)s"
formatter = logging.Formatter(logging_format)

logger = logging.getLogger("aisight_llm")
logger.setLevel(logging.DEBUG)

# Configure TimedRotatingFileHandler
file_handler = TimedRotatingFileHandler(
    filename=log_filepath, when="midnight", interval=1
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def cleanup_old_logs(directory, keep_days=2):

    cutoff_date = datetime.now() - timedelta(days=keep_days)
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_modified_time < cutoff_date:
                os.remove(file_path)
                logger.info(f"Deleted old log file: {file_path}")


cleanup_old_logs(LOG_DIR, keep_days=2)
