from unittest.mock import patch
import pytest
from src.validation.readers import read_records
from src.validation.exceptions import RecordValidationError, ReaderError, SourceNotFoundError


@patch("src.validation.readers.read_json_object")
def test_read_records_returns_data_records(mock_read_json_object):
    mock_read_json_object.return_value = {
        "response": {
            "data": [
                {
                    "refYear": 2024,
                    "reporterCode": 699,
                    "partnerCode": 251,
                },
                {
                    "refYear": 2024,
                    "reporterCode": 251,
                    "partnerCode": 699,
                },
            ]
        }
    }

    result = read_records("raw/2024/India_France_X.json")

    assert result == [
        {
            "refYear": 2024,
            "reporterCode": 699,
            "partnerCode": 251,
        },
        {
            "refYear": 2024,
            "reporterCode": 251,
            "partnerCode": 699,
        },
    ]

    mock_read_json_object.assert_called_once_with(
        "raw/2024/India_France_X.json"
    )

@patch("src.validation.readers.read_json_object")
def test_read_records_rejects_non_list_data(mock_read_json_object):
    mock_read_json_object.return_value = {
        "response": {
            "data": {
                "refYear": 2024,
                "reporterCode": 699,
            }
        }
    }

    with pytest.raises(RecordValidationError, match="Expected response data to be a list"):
        read_records("raw/2024/India_France_X.json")

@patch("src.validation.readers.download_json")
def test_read_json_object_wraps_download_error(mock_download_json):
    mock_download_json.side_effect = Exception("MinIO unavailable")

    with pytest.raises(
        ReaderError,
        match="Failed to read source object",
    ):
        from src.validation.readers import read_json_object

        read_json_object("raw/2024/India_France_X.json")

@patch("src.validation.readers.read_records")
def test_read_yearly_records_combines_records_from_all_years(mock_read_records):
    mock_read_records.side_effect = [
        [{"refYear": 2024, "reporterCode": 699}],
        [{"refYear": 2025, "reporterCode": 699}],
    ]

    from src.validation.readers import read_yearly_records

    records, missing_years = read_yearly_records(
        "India_France_X.json",
        2024,
        2025,
    )

    assert records == [
        {"refYear": 2024, "reporterCode": 699},
        {"refYear": 2025, "reporterCode": 699},
    ]

    assert missing_years == []

    assert mock_read_records.call_args_list == [
        (("raw/2024/India_France_X.json",),),
        (("raw/2025/India_France_X.json",),),
    ]

@patch("src.validation.readers.read_records")
def test_read_yearly_records_tracks_missing_year(
    mock_read_records,
):
    mock_read_records.side_effect = [
        [{"refYear": 2024, "reporterCode": 699}],
        SourceNotFoundError("Source object not found"),
    ]

    from src.validation.readers import read_yearly_records

    records, missing_years = read_yearly_records(
        "India_France_X.json",
        2024,
        2025,
    )

    assert records == [
        {"refYear": 2024, "reporterCode": 699},
    ]

    assert missing_years == [2025]

    assert mock_read_records.call_args_list == [
        (("raw/2024/India_France_X.json",),),
        (("raw/2025/India_France_X.json",),),
    ]

@patch("src.validation.readers.read_records")
def test_read_yearly_records_handles_empty_year(
    mock_read_records,
):
    mock_read_records.side_effect = [
        [],
        [{"refYear": 2025, "reporterCode": 699}],
    ]

    from src.validation.readers import read_yearly_records

    records, missing_years = read_yearly_records(
        "India_France_X.json",
        2024,
        2025,
    )

    assert records == [
        {"refYear": 2025, "reporterCode": 699},
    ]

    assert missing_years == []

    assert mock_read_records.call_count == 2