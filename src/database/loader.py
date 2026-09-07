import logging

from src.database.connection import get_pool


logger = logging.getLogger(__name__)


class TradeDataLoadError(Exception):
    pass


def create_ingestion_run(records_extracted):
    pool = get_pool()

    with pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO ingestion_runs (
                        status,
                        records_extracted
                    )
                    VALUES (%s, %s)
                    RETURNING ingestion_run_id
                    """,
                    ("RUNNING", records_extracted),
                )

                return cursor.fetchone()[0]


def update_ingestion_success(
    ingestion_run_id,
    records_loaded,
):
    pool = get_pool()

    with pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE ingestion_runs
                    SET
                        status = 'SUCCESS',
                        completed_at = NOW(),
                        records_loaded = %s
                    WHERE ingestion_run_id = %s
                    """,
                    (
                        records_loaded,
                        ingestion_run_id,
                    ),
                )


def update_ingestion_failure(
    ingestion_run_id,
    error_message,
):
    pool = get_pool()

    with pool.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE ingestion_runs
                    SET
                        status = 'FAILED',
                        completed_at = NOW(),
                        error_message = %s
                    WHERE ingestion_run_id = %s
                    """,
                    (
                        error_message,
                        ingestion_run_id,
                    ),
                )


def load_trade_records(
    records,
    source_object_id,
    batch_size=500,
):
    if not isinstance(records, list):
        raise TradeDataLoadError(
            f"Expected records to be a list, got {type(records).__name__}"
        )

    if not isinstance(source_object_id, int):
        raise TradeDataLoadError(
            "source_object_id must be an integer"
        )

    if not isinstance(batch_size, int) or batch_size <= 0:
        raise TradeDataLoadError(
            "batch_size must be a positive integer"
        )

    if not records:
        logger.info("No records to load")
        return {
            "records_received": 0,
            "records_inserted": 0,
            "records_skipped": 0,
        }

    records_received = len(records)

    insert_sql = """
        INSERT INTO trade_data (
            source_object_id,
            ingestion_run_id,
            year,
            reporter_code,
            flow_code,
            partner_code,
            commodity_code,
            mot_code,
            qty,
            primary_value,
            is_reported,
            is_aggregate
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (
            year,
            reporter_code,
            flow_code,
            partner_code,
            commodity_code,
            mot_code
        )
        DO NOTHING
    """

    records_inserted = 0

    # Create the ingestion run BEFORE the trade-data transaction.
    # This allows us to preserve a FAILED run if loading fails.
    ingestion_run_id = create_ingestion_run(records_received)

    logger.info(
        "Ingestion run started: run_id=%s records=%s",
        ingestion_run_id,
        records_received,
    )

    pool = get_pool()

    try:
        with pool.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cursor:
                    for start in range(
                        0,
                        records_received,
                        batch_size,
                    ):
                        batch = records[
                            start:start + batch_size
                        ]

                        values = [
                            (
                                source_object_id,
                                ingestion_run_id,
                                record["year"],
                                record["reporter_code"],
                                record["flow_code"],
                                record["partner_code"],
                                record["commodity_code"],
                                record["mot_code"],
                                record["qty"],
                                record["primary_value"],
                                record["is_reported"],
                                record["is_aggregate"],
                            )
                            for record in batch
                        ]

                        cursor.executemany(
                            insert_sql,
                            values,
                        )

                        records_inserted += cursor.rowcount

                        logger.info(
                            "Trade data batch loaded: "
                            "run_id=%s batch_start=%s "
                            "batch_size=%s inserted=%s",
                            ingestion_run_id,
                            start,
                            len(batch),
                            cursor.rowcount,
                        )

        records_skipped = (
            records_received - records_inserted
        )

        # Loading succeeded, so mark the ingestion run SUCCESS.
        update_ingestion_success(
            ingestion_run_id,
            records_inserted,
        )

        logger.info(
            "Trade data loading completed: "
            "run_id=%s received=%s inserted=%s skipped=%s",
            ingestion_run_id,
            records_received,
            records_inserted,
            records_skipped,
        )

        return {
            "records_received": records_received,
            "records_inserted": records_inserted,
            "records_skipped": records_skipped,
            "ingestion_run_id": ingestion_run_id,
        }

    except Exception as exc:

        logger.exception(
            "Trade data loading failed: "
            "run_id=%s received=%s",
            ingestion_run_id,
            records_received,
        )

        # The trade-data transaction has rolled back.
        # Record the failure in a separate transaction.
        try:
            update_ingestion_failure(
                ingestion_run_id,
                str(exc),
            )
        except Exception:
            logger.exception(
                "Failed to update ingestion run as FAILED: "
                "run_id=%s",
                ingestion_run_id,
            )

        raise TradeDataLoadError(
            "Failed to load trade records"
        ) from exc


if __name__ == "__main__":
    from src.validation.readers import read_yearly_records
    from src.validation.normaliser import normalize_records
    from src.validation.validation import validate_records

    records, missing_years = read_yearly_records(
        "China_India_M.json",
        2020,
        2025,
    )

    normalized_records = normalize_records(records)

    validated_records = validate_records(
        normalized_records
    )

    print(
        "VALIDATED RECORDS:",
        len(validated_records),
    )

    result = load_trade_records(
        validated_records,
        source_object_id=1,
    )

    print(
        "LOAD RESULT:",
        result,
    )