import os
import logging
import src.logging_config
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("database_url_missing")
    raise RuntimeError("DATABASE_URL is not configured")
try:
    pool = ConnectionPool(conninfo = DATABASE_URL, min_size = 1, max_size = 10,)
    logger.info("connection_pool_initialized", extra= {"min_size": 1, "max_size": 10,},)
except Exception:
    logger.exception("connection_pool_initialization_failed")
    raise
def get_pool():
    logger.info("connection_pool_requested")
    return pool