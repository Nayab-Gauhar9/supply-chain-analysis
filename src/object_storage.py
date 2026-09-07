import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
import json

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")

class StorageError(Exception):
    pass
class ObjectNotFoundError(StorageError):
    pass

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")
if not BUCKET_NAME:
    raise StorageError("MINIO_BUCKET_NAME is not configured")

def bucket_exists():
    try:
        s3.head_bucket(Bucket = BUCKET_NAME)
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchBucket"):
            return False

        raise StorageError("Failed to check bucket") from e
        


def upload_file(file_path, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        s3.upload_file(
            file_path,
            BUCKET_NAME,
            object_name
       )
    except ClientError as e:
        raise StorageError(f"Failed to upload object: {object_name}") from e

def list_objects():
    try:
        response = s3.list_objects_v2(Bucket = BUCKET_NAME)
        return response.get("Contents", [])
    except ClientError as e:
        raise StorageError(f"Failed to list objects in bucket: {BUCKET_NAME}") from e

def download_file(object_name, file_path):
    try:
        s3.download_file(
            BUCKET_NAME,
            object_name,
            file_path
        )
    except ClientError as e:
        raise StorageError(f"Failed to download object: {object_name}") from e

def delete_object(object_name):
    try:
        s3.delete_object(
            Bucket = BUCKET_NAME,
            Key = object_name
        )
    except ClientError as e:
        raise StorageError(f"Failed to delete object: {object_name}") from e

def upload_json(data, object_name):
    try:
        body = json.dumps(data, ensure_ascii= False).encode("utf-8")
        response = s3.put_object(
            Bucket=BUCKET_NAME,
            Key=object_name,
            Body=body,
            ContentType="application/json"
        )

        print("MINIO UPLOAD SUCCESS")
        print("BUCKET:", BUCKET_NAME)
        print("KEY:", object_name)
        print("ETAG:", response.get("ETag"))

        s3.head_object(
            Bucket=BUCKET_NAME,
            Key=object_name
        )

        print("MINIO OBJECT VERIFIED")
    except ClientError as e:
        raise StorageError(f"Failed to upload JSON object: {object_name}") from e

def object_exists(object_name):
    try:
        s3.head_object(
            Bucket=BUCKET_NAME,
            Key=object_name
        )
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")

        if error_code == "404":
            return False

        raise StorageError(
            f"Failed to check object: {object_name}"
        ) from e

def download_json(object_name):
    try:
        response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=object_name
        )

        body = response["Body"].read()
        return json.loads(body.decode("utf-8"))

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchKey", "NotFound"):
            raise ObjectNotFoundError(f"Object not found: {object_name}") from e
        raise StorageError(
            f"Failed to download JSON object: {object_name}"
        ) from e

def get_bucket_name():
    return BUCKET_NAME