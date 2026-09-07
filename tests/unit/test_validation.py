import pytest

from src.validation.validation import validate_records
from src.validation.exceptions import RecordValidationError


def test_validate_record_accepts_valid_record():
    record = {
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

    result = validate_records([record])

    assert result == [record]

def test_validate_records_rejects_missing_required_field():
    record = {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "M",
        "partner_code": 251,
        # commodity_code intentionally missing
        "mot_code": 2100,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_year_before_2020():
    record = {
        "year": 2019,
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

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_invalid_reporter_code():
    record = {
        "year": 2024,
        "reporter_code": 999,
        "flow_code": "M",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 2100,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_invalid_partner_code():
    record = {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "M",
        "partner_code": 999,
        "commodity_code": "2709",
        "mot_code": 2100,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_invalid_flow_code():
    record = {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "Z",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 2100,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_invalid_commodity_code():
    record = {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "M",
        "partner_code": 251,
        "commodity_code": "9999",
        "mot_code": 2100,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_negative_mot_code():
    record = {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "M",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": -1,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_negative_quantity():
    record = {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "M",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 2100,
        "qty": -100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_negative_primary_value():
    record = {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "M",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 2100,
        "qty": 100,
        "primary_value": -5000,
        "is_reported": True,
        "is_aggregate": False,
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_non_boolean_is_reported():
    record = {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "M",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 2100,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": "true",
        "is_aggregate": False,
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])

def test_validate_records_rejects_non_boolean_is_aggregate():
    record = {
        "year": 2024,
        "reporter_code": 699,
        "flow_code": "M",
        "partner_code": 251,
        "commodity_code": "2709",
        "mot_code": 2100,
        "qty": 100,
        "primary_value": 5000,
        "is_reported": True,
        "is_aggregate": "false",
    }

    with pytest.raises(RecordValidationError):
        validate_records([record])