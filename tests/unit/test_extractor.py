import pytest
from unittest.mock import patch
from src.extractor import build_params, generate_trade_flows, extract_data, run_extraction


def test_build_params_with_single_commodity():
    result = build_params(
        "India",
        "France",
        "crude_petroleum",
        "2024",
        "X",
    )

    assert result == {
        "reporterCode": 699,
        "partnerCode": 251,
        "partner2Code": 0,
        "flowCode": "X",
        "period": "2024",
        "cmdCode": "2709",
    }


def test_build_params_with_multiple_commodities():
    result = build_params(
        "India",
        "France",
        ["crude_petroleum", "refined_petroleum"],
        "2024",
        "X",
    )

    assert result == {
        "reporterCode": 699,
        "partnerCode": 251,
        "partner2Code": 0,
        "flowCode": "X",
        "period": "2024",
        "cmdCode": "2709,2710",
    }

def test_build_params_rejects_unknown_country():
    with pytest.raises(ValueError, match="Country not found in configuration"):
        build_params(
            "India",
            "Germany",
            "crude_petroleum",
            "2024",
            "X",
        )

def test_build_params_rejects_unknown_commodity():
    with pytest.raises(ValueError, match="Commodity not found in configuration"):
        build_params(
            "India",
            "France",
            "unknown_commodity",
            "2024",
            "X",
        )

def test_generate_trade_flows_creates_india_export_and_import_flows():
    countries = [
        {"name": "India", "code": 699},
        {"name": "France", "code": 251},
        {"name": "China", "code": 156},
    ]

    result = generate_trade_flows(countries)

    assert len(result) == 4

    assert result == [
        {
            "reporter": {"name": "India", "code": 699},
            "partner": {"name": "France", "code": 251},
            "direction": "export",
        },
        {
            "reporter": {"name": "France", "code": 251},
            "partner": {"name": "India", "code": 699},
            "direction": "import",
        },
        {
            "reporter": {"name": "India", "code": 699},
            "partner": {"name": "China", "code": 156},
            "direction": "export",
        },
        {
            "reporter": {"name": "China", "code": 156},
            "partner": {"name": "India", "code": 699},
            "direction": "import",
        },
    ]

@patch("src.extractor.get_data")
def test_extract_data_returns_api_response(mock_get_data):
    expected_response = {
        "data": [
            {
                "refYear": 2024,
                "reporterCode": 699,
                "partnerCode": 251,
            }
        ]
    }

    mock_get_data.return_value = expected_response

    result = extract_data(
        "India",
        "France",
        "crude_petroleum",
        "2024",
        "X",
    )

    assert result == expected_response
    mock_get_data.assert_called_once()

@patch("src.extractor.get_data")
def test_extract_data_propagates_api_error(mock_get_data):
    error = RuntimeError("API request failed")
    mock_get_data.side_effect = error

    with pytest.raises(RuntimeError, match="API request failed"):
        extract_data(
            "India",
            "France",
            "crude_petroleum",
            "2024",
            "X",
        )

@patch("src.extractor.register_source_object")
@patch("src.extractor.upload_json")
@patch("src.extractor.extract_data")
def test_run_extraction_processes_successful_flow(
    mock_extract_data,
    mock_upload_json,
    mock_register_source_object,
):
    mock_extract_data.return_value = {
        "data": [
            {
                "refYear": 2024,
                "reporterCode": 699,
                "partnerCode": 251,
            }
        ]
    }

    mock_register_source_object.return_value = 123

    flows = [
        {
            "reporter": {"name": "India", "code": 699},
            "partner": {"name": "France", "code": 251},
            "direction": "export",
        }
    ]

    commodities = ["crude_petroleum"]

    results, failures = run_extraction(
        flows,
        commodities,
        "2024",
    )

    assert failures == []
    assert len(results) == 1

    assert results[0]["reporter"] == "India"
    assert results[0]["partner"] == "France"
    assert results[0]["direction"] == "export"
    assert results[0]["source_object_id"] == 123
    assert results[0]["object_key"] == "raw/2024/India_France_X.json"
    assert results[0]["data"] == mock_extract_data.return_value

    mock_extract_data.assert_called_once_with(
        "India",
        "France",
        commodities,
        "2024",
        "X",
    )

    mock_upload_json.assert_called_once()
    mock_register_source_object.assert_called_once()

@patch("src.extractor.register_source_object")
@patch("src.extractor.upload_json")
@patch("src.extractor.extract_data")
def test_run_extraction_continues_after_failed_flow(
    mock_extract_data,
    mock_upload_json,
    mock_register_source_object,
):
    successful_response = {
        "data": [
            {
                "refYear": 2024,
                "reporterCode": 699,
                "partnerCode": 251,
            }
        ]
    }

    mock_extract_data.side_effect = [
        RuntimeError("API request failed"),
        successful_response,
    ]

    mock_register_source_object.return_value = 123

    flows = [
        {
            "reporter": {"name": "India", "code": 699},
            "partner": {"name": "France", "code": 251},
            "direction": "export",
        },
        {
            "reporter": {"name": "France", "code": 251},
            "partner": {"name": "India", "code": 699},
            "direction": "import",
        },
    ]

    results, failures = run_extraction(
        flows,
        ["crude_petroleum"],
        "2024",
    )

    assert len(results) == 1
    assert len(failures) == 1

    assert results[0]["reporter"] == "France"
    assert results[0]["partner"] == "India"
    assert results[0]["direction"] == "import"

    assert failures[0]["reporter"] == "India"
    assert failures[0]["partner"] == "France"
    assert failures[0]["period"] == "2024"
    assert failures[0]["flow_code"] == "X"
    assert failures[0]["error"] == "API request failed"

    assert mock_extract_data.call_count == 2
    mock_upload_json.assert_called_once()
    mock_register_source_object.assert_called_once()

@patch("src.extractor.register_source_object")
@patch("src.extractor.upload_json")
@patch("src.extractor.extract_data")
def test_run_extraction_builds_correct_raw_object(
    mock_extract_data,
    mock_upload_json,
    mock_register_source_object,
):
    mock_extract_data.return_value = {
        "data": [
            {
                "refYear": 2024,
                "reporterCode": 699,
                "partnerCode": 251,
            }
        ]
    }

    mock_register_source_object.return_value = 123

    flows = [
        {
            "reporter": {"name": "India", "code": 699},
            "partner": {"name": "France", "code": 251},
            "direction": "export",
        }
    ]

    commodities = ["crude_petroleum"]

    run_extraction(flows, commodities, "2024")

    mock_upload_json.assert_called_once()

    raw_object = mock_upload_json.call_args.args[0]
    object_key = mock_upload_json.call_args.args[1]

    assert object_key == "raw/2024/India_France_X.json"

    assert raw_object["metadata"]["reporter"] == "India"
    assert raw_object["metadata"]["partner"] == "France"
    assert raw_object["metadata"]["flow"] == "X"
    assert raw_object["metadata"]["direction"] == "export"
    assert raw_object["metadata"]["period"] == "2024"

    assert raw_object["metadata"]["commodities"] == [
        {
            "name": "crude_petroleum",
            "hs_code": "2709",
        }
    ]

    assert raw_object["response"] == mock_extract_data.return_value