from unittest.mock import Mock, patch
import requests
import pytest
from src.api_client import get_data, API_Error


@patch("src.api_client.requests.get")
def test_get_data_returns_json_on_success(mock_get):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "data": [
            {"refYear": 2024, "reporterCode": 699}
        ]
    }

    mock_get.return_value = response

    params = {"reporterCode": 699}
    headers = {"Accept": "application/json"}

    result = get_data(params, headers)

    assert result == {
        "data": [
            {"refYear": 2024, "reporterCode": 699}
        ]
    }

    mock_get.assert_called_once_with(
        mock_get.call_args.args[0],
        params=params,
        headers=headers,
        timeout=mock_get.call_args.kwargs["timeout"],
    )

@patch("src.api_client.request_interval", 0)
@patch("src.api_client.time.sleep")
@patch("src.api_client.requests.get")
def test_get_data_retries_on_429(mock_get, mock_sleep):
    failed_response = Mock()
    failed_response.status_code = 429

    successful_response = Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "data": [{"refYear": 2024}]
    }

    mock_get.side_effect = [
        failed_response,
        successful_response,
    ]

    result = get_data({}, {})

    assert result == {
        "data": [{"refYear": 2024}]
    }

    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()

@patch("src.api_client.request_interval", 0)
@patch("src.api_client.time.sleep")
@patch("src.api_client.requests.get")
def test_get_data_retries_on_timeout(mock_get, mock_sleep):
    successful_response = Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "data": [{"refYear": 2024}]
    }

    mock_get.side_effect = [
        requests.Timeout("Request timed out"),
        successful_response,
    ]

    result = get_data({}, {})

    assert result == {
        "data": [{"refYear": 2024}]
    }

    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()

@patch("src.api_client.request_interval", 0)
@patch("src.api_client.max_retries", 2)
@patch("src.api_client.time.sleep")
@patch("src.api_client.requests.get")
def test_get_data_raises_api_error_after_retries_exhausted(
    mock_get,
    mock_sleep,
):
    mock_get.side_effect = requests.Timeout("Request timed out")

    with pytest.raises(API_Error) as exc_info:
        get_data({}, {})

    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2
    assert isinstance(exc_info.value.__cause__, requests.Timeout)

@patch("src.api_client.request_interval", 0)
@patch("src.api_client.time.sleep")
@patch("src.api_client.requests.get")
def test_get_data_retries_on_connection_error(mock_get, mock_sleep):
    successful_response = Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "data": [{"refYear": 2024}]
    }

    mock_get.side_effect = [
        requests.ConnectionError("Connection failed"),
        successful_response,
    ]

    result = get_data({}, {})

    assert result == {
        "data": [{"refYear": 2024}]
    }

    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()

@patch("src.api_client.request_interval", 0)
@patch("src.api_client.time.sleep")
@patch("src.api_client.requests.get")
def test_get_data_retries_on_500(mock_get, mock_sleep):
    failed_response = Mock()
    failed_response.status_code = 500

    successful_response = Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "data": [{"refYear": 2024}]
    }

    mock_get.side_effect = [
        failed_response,
        successful_response,
    ]

    result = get_data({}, {})

    assert result == {
        "data": [{"refYear": 2024}]
    }

    assert mock_get.call_count == 2
    mock_sleep.assert_called_once()