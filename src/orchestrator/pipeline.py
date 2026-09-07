import time
import logging
import src.logging_config
logger = logging.getLogger(__name__)
from src.config_loader import load_datasets, load_settings
from src.database.source_objects import get_source_object_id
from src.validation.readers import read_records
from src.validation.normaliser import normalize_records
from src.validation.validation import validate_records
from src.object_storage import download_json, get_bucket_name
from src.database.loader import load_trade_records

bucket = get_bucket_name()
settings = load_settings()
START_YEAR = settings["pipeline"]["start_year"]
END_YEAR = settings["pipeline"]["end_year"]

def run_pipeline():
    logger.info("Starting ETL pipeline")
    datasets = load_datasets()
    logger.info(f"Loaded {len(datasets)} datasets")

    for dataset in datasets:
        logger.info(f"Processing dataset : {dataset}")
        for year in range(START_YEAR,END_YEAR + 1):
            object_key = f"raw/{year}/{dataset}"
            dataset_start = time.perf_counter()
            logger.info(f"Processing dataset = {dataset}, year = {year}, object_key = {object_key}")
            source_object_id = get_source_object_id(bucket, object_key)
            logger.info(f"Resolved source_object_id = {source_object_id}")
            records = read_records(object_key)
            logger.info(f"Raw JSON loaded successfully: dataset = {dataset}, year = {year}, records = {len(records)}")
            normalized_records = normalize_records(records)
            logger.info(f"Records normalized successfully: dataset = {dataset}, year = {year}, records = {len(normalized_records)}")
            validated_records = validate_records(normalized_records)
            logger.info(f"Records validated successfully: dataset = {dataset}, year = {year}, records = {len(validated_records)}")
            load_result = load_trade_records(validated_records, source_object_id)
            logger.info(f"Records loaded successfully: dataset = {dataset}, year = {year}, received = {load_result['records_received']}, inserted = {load_result['records_inserted']}, skipped = {load_result['records_skipped']}")
            dataset_duration_ms = (time.perf_counter() - dataset_start) * 1000
            logger.info(f"Dataset ETL completed: dataset = {dataset}, year = {year}, duration_ms = {dataset_duration_ms:.2f}")

if __name__ == "__main__":
    run_pipeline()