import pytest
from src.database.connection import get_pool
from src.database.source_objects import register_source_object, get_source_object_id
from src.database.loader import create_ingestion_run, update_ingestion_success, update_ingestion_failure, load_trade_records, TradeDataLoadError

@pytest.fixture(autouse=True)
def clean_test_data():
    pool = get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM trade_data
                WHERE source_object_id IN (
                    SELECT source_object_id
                    FROM source_objects
                    WHERE bucket_name = 'test-bucket'
                      AND object_key LIKE 'integration-test/%'
                )
            """)

            cur.execute("""
                DELETE FROM source_objects
                WHERE bucket_name = 'test-bucket'
                  AND object_key LIKE 'integration-test/%'
            """)

        conn.commit()

    yield

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM trade_data
                WHERE source_object_id IN (
                    SELECT source_object_id
                    FROM source_objects
                    WHERE bucket_name = 'test-bucket'
                      AND object_key LIKE 'integration-test/%'
                )
            """)

            cur.execute("""
                DELETE FROM source_objects
                WHERE bucket_name = 'test-bucket'
                  AND object_key LIKE 'integration-test/%'
            """)

        conn.commit()

def test_reference_data_is_loaded():
    pool = get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM countries")
            countries_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM commodities")
            commodities_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM transport_modes")
            mot_count = cursor.fetchone()[0]

    assert countries_count == 5
    assert commodities_count == 10
    assert mot_count == 8

from src.database.source_objects import register_source_object


def test_register_source_object():
    bucket_name = "test-bucket"
    object_key = "integration-test/source-object.json"

    source_object_id = register_source_object(
        bucket_name,
        object_key,
        "source-object.json",
    )

    assert source_object_id is not None
    assert isinstance(source_object_id, int)

def test_register_source_object_is_idempotent():
    bucket_name = "test-bucket"
    object_key = "integration-test/source-object.json"

    first_id = register_source_object(
        bucket_name,
        object_key,
        "source-object.json",
    )

    second_id = register_source_object(
        bucket_name,
        object_key,
        "source-object.json",
    )

    assert second_id == first_id

def test_get_source_object_id():
    bucket_name = "test-bucket"
    object_key = "integration-test/source-object.json"

    registered_id = register_source_object(
        bucket_name,
        object_key,
        "source-object.json",
    )

    found_id = get_source_object_id(
        bucket_name,
        object_key,
    )

    assert found_id == registered_id

def test_get_source_object_id_missing():
    result = get_source_object_id(
        "test-bucket",
        "integration-test/does-not-exist.json",
    )

    assert result is None

def test_create_ingestion_run():
    records_extracted = 25

    ingestion_run_id = create_ingestion_run(records_extracted)

    assert ingestion_run_id is not None
    assert isinstance(ingestion_run_id, int)

def test_create_ingestion_run_starts_running():
    records_extracted = 25

    ingestion_run_id = create_ingestion_run(records_extracted)

    pool = get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT status, records_extracted, records_loaded,
                       records_rejected, completed_at
                FROM ingestion_runs
                WHERE ingestion_run_id = %s
                """,
                (ingestion_run_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    status, records_extracted_db, records_loaded, records_rejected, completed_at = row

    assert status == "RUNNING"
    assert records_extracted_db == 25
    assert records_loaded == 0
    assert records_rejected == 0
    assert completed_at is None

def test_update_ingestion_success():
    ingestion_run_id = create_ingestion_run(25)

    update_ingestion_success(
        ingestion_run_id,
        records_loaded=20,
    )

    pool = get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT status, records_loaded, completed_at
                FROM ingestion_runs
                WHERE ingestion_run_id = %s
                """,
                (ingestion_run_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    status, records_loaded, completed_at = row

    assert status == "SUCCESS"
    assert records_loaded == 20
    assert completed_at is not None

def test_update_ingestion_failure():
    ingestion_run_id = create_ingestion_run(25)

    update_ingestion_failure(
        ingestion_run_id,
        "Test database failure",
    )

    pool = get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT status, error_message, completed_at
                FROM ingestion_runs
                WHERE ingestion_run_id = %s
                """,
                (ingestion_run_id,),
            )

            row = cursor.fetchone()

    assert row is not None

    status, error_message, completed_at = row

    assert status == "FAILED"
    assert error_message == "Test database failure"
    assert completed_at is not None

def test_load_trade_record_success():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/trade-record.json",
        "trade-record.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9900,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        }
    ]

    result = load_trade_records(
        records,
        source_object_id,
    )

    assert result["records_received"] == 1
    assert result["records_inserted"] == 1
    assert result["records_skipped"] == 0

def test_loaded_trade_record_is_persisted():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/persisted-trade.json",
        "persisted-trade.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9200,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        }
    ]

    result = load_trade_records(
        records,
        source_object_id,
    )

    ingestion_run_id = result["ingestion_run_id"]

    pool = get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
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
                FROM trade_data
                WHERE year = %s
                  AND reporter_code = %s
                  AND flow_code = %s
                  AND partner_code = %s
                  AND commodity_code = %s
                  AND mot_code = %s
                """,
                (
                    2099,
                    699,
                    "X",
                    251,
                    "2709",
                    9200,
                ),
            )

            row = cursor.fetchone()

    assert row is not None

    (
        db_source_object_id,
        db_ingestion_run_id,
        year,
        reporter_code,
        flow_code,
        partner_code,
        commodity_code,
        mot_code,
        qty,
        primary_value,
        is_reported,
        is_aggregate,
    ) = row

    assert db_source_object_id == source_object_id
    assert db_ingestion_run_id == ingestion_run_id
    assert year == 2099
    assert reporter_code == 699
    assert flow_code == "X"
    assert partner_code == 251
    assert commodity_code == "2709"
    assert mot_code == 9200
    assert qty == 100
    assert primary_value == 5000
    assert is_reported is True
    assert is_aggregate is False

def test_load_trade_record_is_idempotent():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/idempotency.json",
        "idempotency.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 1000,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        }
    ]

    first_result = load_trade_records(
        records,
        source_object_id,
    )

    second_result = load_trade_records(
        records,
        source_object_id,
    )

    assert first_result["records_received"] == 1
    assert first_result["records_inserted"] == 1
    assert first_result["records_skipped"] == 0

    assert second_result["records_received"] == 1
    assert second_result["records_inserted"] == 0
    assert second_result["records_skipped"] == 1

def test_different_mot_values_are_distinct_records():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/different-mot.json",
        "different-mot.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 1000,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        },
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 2100,
            "qty": 200,
            "primary_value": 8000,
            "is_reported": True,
            "is_aggregate": False,
        },
    ]

    result = load_trade_records(
        records,
        source_object_id,
    )

    assert result["records_received"] == 2
    assert result["records_inserted"] == 2
    assert result["records_skipped"] == 0

def test_load_trade_record_invalid_source_object_fails():
    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 1000,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        }
    ]

    pool = get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(source_object_id), 0) + 100000
                FROM source_objects
                """
            )
            invalid_source_object_id = cursor.fetchone()[0]

    with pytest.raises(TradeDataLoadError):
        load_trade_records(
            records,
            invalid_source_object_id,
        )

def test_failed_load_rolls_back_and_marks_run_failed():
    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 1000,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        }
    ]

    pool = get_pool()

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COALESCE(MAX(ingestion_run_id), 0)
                FROM ingestion_runs
                """
            )
            previous_max_run_id = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT
                    COALESCE(MAX(source_object_id), 0) + 100000
                FROM source_objects
                """
            )
            invalid_source_object_id = cursor.fetchone()[0]

    with pytest.raises(TradeDataLoadError):
        load_trade_records(
            records,
            invalid_source_object_id,
        )

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    ingestion_run_id,
                    status,
                    records_extracted,
                    records_loaded,
                    records_rejected,
                    error_message,
                    completed_at
                FROM ingestion_runs
                WHERE ingestion_run_id > %s
                ORDER BY ingestion_run_id DESC
                LIMIT 1
                """,
                (previous_max_run_id,),
            )

            run = cursor.fetchone()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM trade_data
                WHERE year = %s
                  AND reporter_code = %s
                  AND flow_code = %s
                  AND partner_code = %s
                  AND commodity_code = %s
                  AND mot_code = %s
                """,
                (
                    2099,
                    699,
                    "X",
                    251,
                    "2709",
                    1000,
                ),
            )

            trade_count = cursor.fetchone()[0]

    assert run is not None

    (
        ingestion_run_id,
        status,
        records_extracted,
        records_loaded,
        records_rejected,
        error_message,
        completed_at,
    ) = run

    assert ingestion_run_id > previous_max_run_id
    assert status == "FAILED"
    assert records_extracted == 1
    assert records_loaded == 0
    assert records_rejected == 0
    assert error_message is not None
    assert completed_at is not None

    assert trade_count == 0

def test_load_trade_record_invalid_reporter_fails():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-reporter.json",
        "invalid-reporter.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 999999,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 1000,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        }
    ]

    with pytest.raises(TradeDataLoadError):
        load_trade_records(
            records,
            source_object_id,
        )

def test_load_trade_record_invalid_partner_fails():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-partner.json",
        "invalid-partner.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 999999,
            "commodity_code": "2709",
            "mot_code": 1000,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        }
    ]

    with pytest.raises(TradeDataLoadError):
        load_trade_records(
            records,
            source_object_id,
        )

def test_load_trade_record_invalid_commodity_fails():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-commodity.json",
        "invalid-commodity.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "999999",
            "mot_code": 1000,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        }
    ]

    with pytest.raises(TradeDataLoadError):
        load_trade_records(
            records,
            source_object_id,
        )

def test_load_trade_record_invalid_mot_fk():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-mot.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 999999,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(TradeDataLoadError):
        load_trade_records([record], source_object_id)

def test_invalid_mot_fk_rolls_back_trade_data():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/rollback-mot.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 999999,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(TradeDataLoadError):
        load_trade_records([record], source_object_id)

    pool = get_pool()

    with pool.connection() as conn:
        trade_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM trade_data
            WHERE year = 2099
              AND reporter_code = 699
              AND flow_code = 'X'
              AND partner_code = 251
              AND commodity_code = '2709'
              AND mot_code = 999999
            """
        ).fetchone()[0]

        failed_run = conn.execute(
            """
            SELECT status
            FROM ingestion_runs
            WHERE records_extracted = 1
              AND status = 'FAILED'
            ORDER BY ingestion_run_id DESC
            LIMIT 1
            """
        ).fetchone()

    assert trade_count == 0
    assert failed_run is not None
    assert failed_run[0] == "FAILED"

def test_load_trade_record_invalid_flow_code():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-flow.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "Z",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 9900,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(TradeDataLoadError):
        load_trade_records([record], source_object_id)

def test_load_trade_record_invalid_year():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-year.json",
    )

    record = {
        "year": 2019,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 9900,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    result = load_trade_records([record], source_object_id)

    assert result["records_received"] == 1
    assert result["records_inserted"] == 1

def test_load_trade_record_allows_null_optional_values():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/null-values.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 9900,
        "qty": None,
        "primary_value": None,
        "is_reported": True,
        "is_aggregate": False,
    }

    result = load_trade_records([record], source_object_id)

    assert result["records_received"] == 1
    assert result["records_inserted"] == 1

def test_load_trade_record_null_is_reported():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/null-is-reported.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 9900,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": None,
        "is_aggregate": False,
    }

    with pytest.raises(TradeDataLoadError):
        load_trade_records([record], source_object_id)

def test_load_trade_record_null_is_aggregate():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/null-is-aggregate.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 9900,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": None,
    }

    with pytest.raises(TradeDataLoadError):
        load_trade_records([record], source_object_id)

def test_load_trade_record_invalid_is_reported_type():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-is-reported.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 9900,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": "definitely_not_yes",
        "is_aggregate": False,
    }

    with pytest.raises(TradeDataLoadError):
        load_trade_records([record], source_object_id)

def test_load_trade_record_invalid_is_aggregate_type():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-is-aggregate.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 9900,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": "definitely_not_boolean",
    }

    with pytest.raises(TradeDataLoadError):
        load_trade_records([record], source_object_id)

def test_load_trade_record_invalid_qty_type():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-qty.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 9900,
        "qty": "not-a-number",
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(TradeDataLoadError):
        load_trade_records([record], source_object_id)

def test_load_trade_record_invalid_primary_value_type():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/invalid-primary-value.json",
    )

    record = {
        "year": 2099,
        "reporter_code": 699,
        "flow_code": "X",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 9900,
        "qty": 100,
        "primary_value": "not-a-number",
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(TradeDataLoadError):
        load_trade_records([record], source_object_id)

def test_batch_failure_rolls_back_entire_transaction():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/batch-rollback.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9900,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        },
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 999999,
            "qty": 200,
            "primary_value": 6000,
            "is_reported": True,
            "is_aggregate": False,
        },
    ]

    with pytest.raises(TradeDataLoadError):
        load_trade_records(records, source_object_id, batch_size=500)

    pool = get_pool()

    with pool.connection() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM trade_data
            WHERE source_object_id = %s
            """,
            (source_object_id,),
        ).fetchone()[0]

    assert count == 0

def test_batch_success_loads_all_records():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/batch-success.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9900,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        },
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9200,
            "qty": 200,
            "primary_value": 6000,
            "is_reported": True,
            "is_aggregate": False,
        },
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "M",
            "partner_code": 251,
            "commodity_code": "2710",
            "mot_code": 9900,
            "qty": 300,
            "primary_value": 7000,
            "is_reported": True,
            "is_aggregate": False,
        },
    ]

    result = load_trade_records(
        records,
        source_object_id,
        batch_size=2,
    )

    assert result["records_received"] == 3
    assert result["records_inserted"] == 3
    assert result["records_skipped"] == 0

    pool = get_pool()

    with pool.connection() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM trade_data
            WHERE source_object_id = %s
            """,
            (source_object_id,),
        ).fetchone()[0]

    assert count == 3

def test_batch_idempotency():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/batch-idempotency.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9900,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        },
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9200,
            "qty": 200,
            "primary_value": 6000,
            "is_reported": True,
            "is_aggregate": False,
        },
    ]

    first_result = load_trade_records(
        records,
        source_object_id,
        batch_size=2,
    )

    second_result = load_trade_records(
        records,
        source_object_id,
        batch_size=2,
    )

    assert first_result["records_received"] == 2
    assert first_result["records_inserted"] == 2
    assert first_result["records_skipped"] == 0

    assert second_result["records_received"] == 2
    assert second_result["records_inserted"] == 0
    assert second_result["records_skipped"] == 2

    pool = get_pool()

    with pool.connection() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM trade_data
            WHERE source_object_id = %s
            """,
            (source_object_id,),
        ).fetchone()[0]

    assert count == 2

def test_batch_size_smaller_than_records():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/batch-size.json",
    )

    records = []

    for mot_code in [0, 1000, 2100, 3100, 3200]:
        records.append({
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": mot_code,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        })

    result = load_trade_records(
        records,
        source_object_id,
        batch_size=2,
    )

    assert result["records_received"] == 5
    assert result["records_inserted"] == 5
    assert result["records_skipped"] == 0

    pool = get_pool()

    with pool.connection() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM trade_data
            WHERE source_object_id = %s
            """,
            (source_object_id,),
        ).fetchone()[0]

    assert count == 5

def test_load_empty_records():
    result = load_trade_records(
        [],
        source_object_id=1,
    )

    assert result["records_received"] == 0
    assert result["records_inserted"] == 0
    assert result["records_skipped"] == 0
    assert "ingestion_run_id" not in result

def test_load_trade_records_rejects_non_list_records():
    with pytest.raises(TradeDataLoadError):
        load_trade_records(
            {"year": 2099},
            1,
        )

def test_load_trade_records_rejects_invalid_batch_size():
    with pytest.raises(TradeDataLoadError):
        load_trade_records(
            [],
            1,
            batch_size=0,
        )

def test_trade_records_link_to_ingestion_run():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/ingestion-link.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9900,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        },
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9200,
            "qty": 200,
            "primary_value": 6000,
            "is_reported": True,
            "is_aggregate": False,
        },
    ]

    result = load_trade_records(records, source_object_id)

    assert result["records_inserted"] == 2
    assert "ingestion_run_id" in result

    ingestion_run_id = result["ingestion_run_id"]

    pool = get_pool()

    with pool.connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT ingestion_run_id
            FROM trade_data
            WHERE source_object_id = %s
            """,
            (source_object_id,),
        ).fetchall()

    assert rows == [(ingestion_run_id,)]

def test_load_trade_records_completes_ingestion_run():
    source_object_id = register_source_object(
        "test-bucket",
        "integration-test/run-completion.json",
    )

    records = [
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9900,
            "qty": 100,
            "primary_value": 5000,
            "is_reported": True,
            "is_aggregate": False,
        },
        {
            "year": 2099,
            "reporter_code": 699,
            "flow_code": "X",
            "partner_code": 251,
            "commodity_code": "2709",
            "mot_code": 9200,
            "qty": 200,
            "primary_value": 6000,
            "is_reported": True,
            "is_aggregate": False,
        },
    ]

    result = load_trade_records(records, source_object_id)

    ingestion_run_id = result["ingestion_run_id"]

    pool = get_pool()

    with pool.connection() as conn:
        row = conn.execute(
            """
            SELECT status,
                   records_extracted,
                   records_loaded,
                   completed_at
            FROM ingestion_runs
            WHERE ingestion_run_id = %s
            """,
            (ingestion_run_id,),
        ).fetchone()

    assert row is not None
    assert row[0] == "SUCCESS"
    assert row[1] == 2
    assert row[2] == 2
    assert row[3] is not None