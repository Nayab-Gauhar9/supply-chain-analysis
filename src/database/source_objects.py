import logging
import src.logging_config
from pathlib import PurePosixPath

from src.database.connection import get_pool

logger = logging.getLogger(__name__)


def register_source_object(bucket_name, object_key, file_name=None):

    if not bucket_name:
        raise ValueError("bucket_name is required")

    if not object_key:
        raise ValueError("object_key is required")

    if file_name is None:
        file_name = PurePosixPath(object_key).name

    pool = get_pool()

    try:
        with pool.connection() as conn:
            row = conn.execute(
                """
                INSERT INTO source_objects (
                    bucket_name,
                    object_key,
                    file_name
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (bucket_name, object_key)
                DO UPDATE SET
                    file_name = EXCLUDED.file_name
                RETURNING source_object_id;
                """,
                (
                    bucket_name,
                    object_key,
                    file_name,
                ),
            ).fetchone()

            source_object_id = row[0]

            logger.info(
                "Source object registered: "
                "source_object_id=%s bucket=%s object_key=%s",
                source_object_id,
                bucket_name,
                object_key,
            )

            return source_object_id

    except Exception:
        logger.exception(
            "Failed to register source object: "
            "bucket=%s object_key=%s",
            bucket_name,
            object_key,
        )
        raise

def get_source_object_id(bucket_name, object_key):
    if not bucket_name or not object_key:
        raise ValueError("bucket_name and object_key are required")

    pool = get_pool()

    try:
        with pool.connection() as conn:
            row = conn.execute(
                """
                SELECT source_object_id
                FROM source_objects
                WHERE bucket_name = %s
                  AND object_key = %s
                """,
                (bucket_name, object_key),
            ).fetchone()

            if row is None:
                return None

            return row[0]

    except Exception:
        logger.exception(
            "Failed to retrieve source object",
            extra={
                "bucket_name": bucket_name,
                "object_key": object_key,
            },
        )
        raise