from src.validation.normaliser import normalize_record, normalize_records
from src.validation.exceptions import RecordValidationError
import pytest

def test_normalize_record_maps_fields():
    raw_record = {
        "refYear": 2024,
        "reporterCode": 699,
        "flowCode": "M",
        "partnerCode": 251,
        "cmdCode": "2709",
        "motCode": 2100,
        "qty": 100,
        "primaryValue": 5000,
        "isReported": True,
        "isAggregate": False,
    }

    result = normalize_record(raw_record)

    assert result == {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "M",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 2100,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

def test_normalize_records_processes_multiple_records():
    raw_records = [
        {
            "refYear": 2024,
            "reporterCode": 699,
            "flowCode": "M",
            "partnerCode": 251,
            "cmdCode": "2709",
            "motCode": 2100,
            "qty": 100,
            "primaryValue": 5000,
            "isReported": True,
            "isAggregate": False,
        },
        {
            "refYear": 2025,
            "reporterCode": 251,
            "flowCode": "X",
            "partnerCode": 699,
            "cmdCode": "2710",
            "motCode": 1000,
            "qty": 200,
            "primaryValue": 8000,
            "isReported": True,
            "isAggregate": False,
        },
    ]

    result = normalize_records(raw_records)

    assert len(result) == 2
    assert result[0]["year"] == 2024
    assert result[0]["commodity_code"] == "2709"
    assert result[1]["year"] == 2025
    assert result[1]["commodity_code"] == "2710"

def test_normalize_records_rejects_non_list_input():
    invalid_records = {
        "refYear": 2024,
        "reporterCode": 699,
    }

    with pytest.raises(RecordValidationError):
        normalize_records(invalid_records)