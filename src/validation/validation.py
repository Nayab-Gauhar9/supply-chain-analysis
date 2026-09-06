import logging

from src.validation.exceptions import RecordValidationError


logger = logging.getLogger(__name__)


def validate_records(records):

    if not isinstance(records, list):
        raise RecordValidationError(
            f"Expected records to be a list, got {type(records).__name__}"
        )

    logger.info(
        "Starting batch validation: records=%s",
        len(records)
    )

    invalid_records = 0

    for index, record in enumerate(records):
        try:
            if not isinstance(record, dict):
                raise RecordValidationError(
                    f"Record at index {index} must be a dict, "
                    f"got {type(record).__name__}"
                )

            logger.debug(
                "Record accepted for validation: index=%s",
                index
            )

        except RecordValidationError:
            invalid_records += 1

            logger.exception(
                "Record validation failed: index=%s",
                index
            )

    logger.info(
        "Batch validation completed: records=%s invalid=%s",
        len(records),
        invalid_records
    )

    return records

if __name__ == "__main__":
    from src.validation.readers import read_yearly_records
    from src.validation.normaliser import normalize_records

    records, missing_years = read_yearly_records(
        "China_India_M.json",
        2020,
        2025,
    )

    print("RAW RECORDS:", len(records))
    print("MISSING YEARS:", missing_years)

    normalized_records = normalize_records(records)

    print("NORMALIZED RECORDS:", len(normalized_records))

    validated_records = validate_records(normalized_records)

    print("VALIDATED RECORDS:", len(validated_records))