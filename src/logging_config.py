import logging
from pathlib import Path

BASE_DIR= Path(__file__).resolve().parent.parent
LOG_DIR= BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE= LOG_DIR /"app.log"
file_handler= logging.FileHandler(LOG_FILE)

formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[file_handler,console_handler])