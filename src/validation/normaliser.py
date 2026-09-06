import logging

from src.validation.exceptions import RecordValidationError


logger = logging.getLogger(__name__)


def normalize_record(record):
    if not isinstance(record, dict):
        raise RecordValidationError(
            f"Expected record to be a dict, got {type(record).__name__}"
        )

    normalized = {
        "year": record.get("refYear"),
        "flow_code": record.get("flowCode"),
        "partner_code": record.get("partnerCode"),
        "commodity_code": record.get("cmdCode"),
        "primary_value": record.get("primaryValue"),
    }

    logger.debug(
        "Record normalized successfully: year=%s",
        normalized["year"],
    )

    return normalized

def normalize_records(records):
    if not isinstance(records, list):
        raise RecordValidationError(
            f"Expected records to be a list, got {type(records).__name__}"
        )

    logger.info(
        "Starting record normalization: records=%s",
        len(records),
    )

    normalized_records = []

    for index, record in enumerate(records):
        try:
            normalized = normalize_record(record)
            normalized_records.append(normalized)

        except RecordValidationError:
            logger.exception(
                "Record normalization failed: index=%s",
                index,
            )
            raise

    logger.info(
        "Record normalization completed: records=%s",
        len(normalized_records),
    )

    return normalized_records

if __name__ == "__main__":
    from src.validation.readers import read_yearly_records

    records, missing_years = read_yearly_records(
        "China_India_M.json",
        2020,
        2025,
    )

    print("TOTAL RECORDS:", len(records))
    print("MISSING YEARS:", missing_years)

    if records:
        normalized_records = normalize_records(records)

        print("\nNORMALIZED RECORDS:")
        print(len(normalized_records))
        print("\nFIRST NORMALIZED RECORD:")
        print(normalized_records[0])