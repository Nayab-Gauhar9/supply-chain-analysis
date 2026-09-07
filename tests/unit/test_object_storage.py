import pytest
from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock
from src.object_storage import upload_json, StorageError, object_exists, BUCKET_NAME, download_json, bucket_exists, list_objects, upload_file, download_file

@patch("src.object_storage.s3")
def test_upload_json_uploads_json_object(mock_s3):
    mock_s3.put_object.return_value = {
        "ETag": '"test-etag"'
    }

    mock_s3.head_object.return_value = {}

    data = {
        "metadata": {
            "reporter": "India",
            "partner": "France",
            "flow": "X",
        },
        "response": {
            "data": []
        },
    }

    upload_json(
        data,
        "raw/2024/India_France_X.json",
    )

    mock_s3.put_object.assert_called_once()

    call_kwargs = mock_s3.put_object.call_args.kwargs

    assert call_kwargs["Key"] == "raw/2024/India_France_X.json"
    assert call_kwargs["ContentType"] == "application/json"

    assert call_kwargs["Bucket"] is not None
    assert call_kwargs["Body"] == (
        '{"metadata": {"reporter": "India", "partner": "France", "flow": "X"}, '
        '"response": {"data": []}}'
    ).encode("utf-8")

    mock_s3.head_object.assert_called_once_with(
        Bucket=call_kwargs["Bucket"],
        Key="raw/2024/India_France_X.json",
    )

@patch("src.object_storage.s3")
def test_upload_json_raises_storage_error_on_upload_failure(mock_s3):
    error_response = {
        "Error": {
            "Code": "500",
            "Message": "MinIO upload failed",
        }
    }

    mock_s3.put_object.side_effect = ClientError(
        error_response,
        "PutObject",
    )

    data = {
        "response": {
            "data": []
        }
    }

    with pytest.raises(
        StorageError,
        match="Failed to upload JSON object",
    ):
        upload_json(
            data,
            "raw/2024/India_France_X.json",
        )

    mock_s3.put_object.assert_called_once()
    mock_s3.head_object.assert_not_called()

@patch("src.object_storage.s3")
def test_object_exists_returns_true_when_object_exists(mock_s3):
    mock_s3.head_object.return_value = {}

    result = object_exists(
        "raw/2024/India_France_X.json"
    )

    assert result is True

    mock_s3.head_object.assert_called_once_with(
        Bucket=BUCKET_NAME,
        Key="raw/2024/India_France_X.json",
    )

@patch("src.object_storage.s3")
def test_object_exists_returns_false_when_object_missing(mock_s3):
    error_response = {
        "Error": {
            "Code": "404",
            "Message": "Not Found",
        }
    }

    mock_s3.head_object.side_effect = ClientError(
        error_response,
        "HeadObject",
    )

    result = object_exists(
        "raw/2024/India_France_X.json"
    )

    assert result is False

    mock_s3.head_object.assert_called_once_with(
        Bucket=BUCKET_NAME,
        Key="raw/2024/India_France_X.json",
    )

@patch("src.object_storage.s3")
def test_object_exists_raises_storage_error_on_unexpected_error(mock_s3):
    error_response = {
        "Error": {
            "Code": "500",
            "Message": "Internal server error",
        }
    }

    mock_s3.head_object.side_effect = ClientError(
        error_response,
        "HeadObject",
    )

    with pytest.raises(
        StorageError,
        match="Failed to check object",
    ):
        object_exists(
            "raw/2024/India_France_X.json"
        )

    mock_s3.head_object.assert_called_once_with(
        Bucket=BUCKET_NAME,
        Key="raw/2024/India_France_X.json",
    )

@patch("src.object_storage.s3")
def test_download_json_success(mock_s3):
    mock_body = MagicMock()
    mock_body.read.return_value = b'{"year": 2024, "records": [1, 2, 3]}'

    mock_s3.get_object.return_value = {
        "Body": mock_body
    }

    result = download_json(
        "raw/2024/India_France_X.json"
    )

    assert result == {
        "year": 2024,
        "records": [1, 2, 3],
    }

    mock_s3.get_object.assert_called_once_with(
        Bucket=BUCKET_NAME,
        Key="raw/2024/India_France_X.json",
    )

@patch("src.object_storage.s3")
def test_download_json_client_error(mock_s3):
    mock_s3.get_object.side_effect = ClientError(
        {
            "Error": {
                "Code": "NoSuchKey",
                "Message": "The specified key does not exist."
            }
        },
        "GetObject"
    )

    with pytest.raises(StorageError) as exc_info:
        download_json("raw/2024/missing.json")

    assert "missing.json" in str(exc_info.value)

    mock_s3.get_object.assert_called_once_with(
        Bucket=BUCKET_NAME,
        Key="raw/2024/missing.json",
    )

@patch("src.object_storage.s3")
def test_bucket_exists_success(mock_s3):
    mock_s3.head_bucket.return_value = {}

    result = bucket_exists()

    assert result is True

    mock_s3.head_bucket.assert_called_once_with(
        Bucket=BUCKET_NAME
    )

@patch("src.object_storage.s3")
def test_bucket_exists_not_found(mock_s3):
    mock_s3.head_bucket.side_effect = ClientError(
        {
            "Error": {
                "Code": "404",
                "Message": "Not Found",
            }
        },
        "HeadBucket",
    )

    result = bucket_exists()

    assert result is False

    mock_s3.head_bucket.assert_called_once_with(
        Bucket=BUCKET_NAME
    )

@patch("src.object_storage.s3")
def test_bucket_exists_unexpected_error(mock_s3):
    mock_s3.head_bucket.side_effect = ClientError(
        {
            "Error": {
                "Code": "500",
                "Message": "Internal Server Error",
            }
        },
        "HeadBucket",
    )

    with pytest.raises(StorageError):
        bucket_exists()

    mock_s3.head_bucket.assert_called_once_with(
        Bucket=BUCKET_NAME
    )

@patch("src.object_storage.s3")
def test_list_objects_success(mock_s3):
    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {"Key": "raw/2024/India_France_X.json"},
            {"Key": "raw/2024/India_USA_M.json"},
        ]
    }

    result = list_objects()

    assert result == [
    {"Key": "raw/2024/India_France_X.json"},
    {"Key": "raw/2024/India_USA_M.json"},
    ]

    mock_s3.list_objects_v2.assert_called_once_with(
        Bucket=BUCKET_NAME,
    )

@patch("src.object_storage.s3")
def test_list_objects_empty(mock_s3):
    mock_s3.list_objects_v2.return_value = {}

    result = list_objects()

    assert result == []

    mock_s3.list_objects_v2.assert_called_once_with(
        Bucket=BUCKET_NAME
    )

@patch("src.object_storage.s3")
def test_list_objects_client_error(mock_s3):
    mock_s3.list_objects_v2.side_effect = ClientError(
        {
            "Error": {
                "Code": "500",
                "Message": "Internal Server Error",
            }
        },
        "ListObjectsV2",
    )

    with pytest.raises(StorageError):
        list_objects()

    mock_s3.list_objects_v2.assert_called_once_with(
        Bucket=BUCKET_NAME
    )

@patch("src.object_storage.s3")
def test_upload_file_success(mock_s3):
    upload_file(
        "/tmp/test.json",
        "raw/2024/test.json",
    )

    mock_s3.upload_file.assert_called_once_with(
        "/tmp/test.json",
        BUCKET_NAME,
        "raw/2024/test.json",
    )

@patch("src.object_storage.s3")
def test_upload_file_client_error(mock_s3):
    mock_s3.upload_file.side_effect = ClientError(
        {
            "Error": {
                "Code": "500",
                "Message": "Internal Server Error",
            }
        },
        "UploadFile",
    )

    with pytest.raises(StorageError):
        upload_file(
            "/tmp/test.json",
            "raw/2024/test.json",
        )

    mock_s3.upload_file.assert_called_once_with(
        "/tmp/test.json",
        BUCKET_NAME,
        "raw/2024/test.json",
    )

@patch("src.object_storage.s3")
def test_upload_file_unexpected_error(mock_s3):
    mock_s3.upload_file.side_effect = RuntimeError("unexpected failure")

    with pytest.raises(RuntimeError):
        upload_file(
            "/tmp/test.json",
            "raw/2024/test.json",
        )

    mock_s3.upload_file.assert_called_once_with(
        "/tmp/test.json",
        BUCKET_NAME,
        "raw/2024/test.json",
    )

@patch("src.object_storage.s3")
def test_download_file_success(mock_s3):
    download_file(
        "raw/2024/test.json",
        "/tmp/test.json",
    )

    mock_s3.download_file.assert_called_once_with(
        BUCKET_NAME,
        "raw/2024/test.json",
        "/tmp/test.json",
    )

@patch("src.object_storage.s3")
def test_download_file_client_error(mock_s3):
    mock_s3.download_file.side_effect = ClientError(
        {
            "Error": {
                "Code": "404",
                "Message": "Not Found",
            }
        },
        "DownloadFile",
    )

    with pytest.raises(StorageError):
        download_file(
            "raw/2024/missing.json",
            "/tmp/missing.json",
        )

    mock_s3.download_file.assert_called_once_with(
        BUCKET_NAME,
        "raw/2024/missing.json",
        "/tmp/missing.json",
    )

@patch("src.object_storage.s3")
def test_download_file_unexpected_error(mock_s3):
    mock_s3.download_file.side_effect = RuntimeError(
        "unexpected failure"
    )

    with pytest.raises(RuntimeError):
        download_file(
            "raw/2024/test.json",
            "/tmp/test.json",
        )

    mock_s3.download_file.assert_called_once_with(
        BUCKET_NAME,
        "raw/2024/test.json",
        "/tmp/test.json",
    )