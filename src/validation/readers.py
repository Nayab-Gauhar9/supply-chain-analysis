import logging
from src.object_storage import download_json, ObjectNotFoundError
import src.logging_config
from src.validation.exceptions import ReaderError,SourceNotFoundError,RecordValidationError

logger = logging.getLogger(__name__)

def read_json_object(object_name):
    logger.info("Reading source object: %s", object_name)

    try:
        data = download_json(object_name)

    except ObjectNotFoundError as e:
        logger.warning(
            "Source object not found: %s",
            object_name,
        )

        raise SourceNotFoundError(
            f"Source object not found: {object_name}"
        ) from e

    except Exception as e:
        logger.exception(
            "Failed to download source object: %s",
            object_name,
        )

        raise ReaderError(
            f"Failed to read source object: {object_name}"
        ) from e

    logger.info(
        "Successfully read source object: %s",
        object_name,
    )

    return data

def read_records(object_name):
    logger.info(
        "Reading records from object: %s",
        object_name,
    )

    data = read_json_object(object_name)

    if not isinstance(data, dict):
        logger.error(
            "Invalid root structure: object=%s expected=dict got=%s",
            object_name,
            type(data).__name__,
        )

        raise RecordValidationError(
            f"Expected root JSON object to be a dict, "
            f"got {type(data).__name__}: {object_name}"
        )

    response = data.get("response")

    if not isinstance(response, dict):
        logger.error(
            "Invalid response structure: object=%s expected=dict got=%s",
            object_name,
            type(response).__name__,
        )

        raise RecordValidationError(
            f"Expected 'response' to be a dict: {object_name}"
        )

    records = response.get("data")

    if not isinstance(records, list):
        logger.error(
            "Invalid records structure: object=%s expected=list got=%s",
            object_name,
            type(records).__name__,
        )

        raise RecordValidationError(
            f"Expected response data to be a list, "
            f"got {type(records).__name__}: {object_name}"
        )

    logger.info(
        "Records successfully validated: object=%s records=%d",
        object_name,
        len(records),
    )

    return records

def read_yearly_records(file_name, start_year, end_year):
    if start_year > end_year:
        raise ValueError(
            f"Invalid year range: start_year={start_year}, "
            f"end_year={end_year}"
        )

    logger.info(
        "Starting yearly record read: file=%s start_year=%s end_year=%s",
        file_name,
        start_year,
        end_year,
    )

    all_records = []
    missing_years = []

    for year in range(start_year, end_year + 1):
        object_name = f"raw/{year}/{file_name}"

        logger.info(
            "Processing year: year=%s object=%s",
            year,
            object_name,
        )

        try:
            records = read_records(object_name)

            all_records.extend(records)

            logger.info(
                "Year processed successfully: year=%s records=%s",
                year,
                len(records),
            )

        except SourceNotFoundError as e:
            missing_years.append(year)

            logger.warning(
                "Source object missing: year=%s object=%s error=%s",
                year,
                object_name,
                str(e),
            )

    logger.info(
        "Yearly record read completed: total_records=%s missing_years=%s",
        len(all_records),
        missing_years,
    )

    return all_records, missing_years

if __name__ == "__main__":
    yearly_records, missing_years = read_yearly_records("China_India_M.json", 2020,2020)
    print("TOTAL YEARLY RECORDS:", len(yearly_records))
    print("MISSING YEARS:", missing_years)