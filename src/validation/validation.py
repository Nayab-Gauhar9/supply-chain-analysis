import logging
from src.config_loader import load_commodities, load_countries
from src.validation.exceptions import RecordValidationError


logger = logging.getLogger(__name__)

countries = load_countries()
commodities = load_commodities()

valid_country_codes = {
    country["code"] for country in countries
}

valid_commodity_codes = {
    commodity["hs_code"] for commodity in commodities
}

def validate_records(records):

    if not isinstance(records, list):
        raise RecordValidationError(
            f"Expected records to be a list, got {type(records).__name__}"
        )

    logger.info(
        "Starting batch validation: records=%s",
        len(records)
    )
    required_fields = [
    "year",
    "reporter_code",
    "flow_code",
    "partner_code",
    "commodity_code",
    "mot_code",
    "is_reported",
    "is_aggregate",
    ]

    invalid_records = 0

    for index, record in enumerate(records):
        try:
            if not isinstance(record, dict):
                raise RecordValidationError(
                    f"Record at index {index} must be a dict, "
                    f"got {type(record).__name__}"
                )
            missing_fields = [field for field in required_fields if field not in record]
            if missing_fields:
                raise RecordValidationError(f"Record at index {index} is missing required fields: {missing_fields}")

            if not isinstance(record["year"], int):
                raise RecordValidationError(
                    f"Record at index {index}: year must be an integer"
                )
            if record["year"] < 2020:
                raise RecordValidationError(
                    f"Record at index {index}: year must be >= 2020"
                )

            if not isinstance(record["reporter_code"], int):
                raise RecordValidationError(
                    f"Record at index {index}: reporter_code must be an integer"
                )
            if record["reporter_code"] not in valid_country_codes:
                raise RecordValidationError(
                    f"Record at index {index}: invalid reporter_code "
                    f"{record['reporter_code']}"
                )

            if not isinstance(record["flow_code"], str):
                raise RecordValidationError(
                    f"Record at index {index}: flow_code must be a string"
                )
            if record["flow_code"] not in ("M", "X"):
                raise RecordValidationError(
                    f"Record at index {index}: invalid flow_code "
                    f"{record['flow_code']!r}; expected 'M' or 'X'"
                )

            if not isinstance(record["partner_code"], int):
                raise RecordValidationError(
                    f"Record at index {index}: partner_code must be an integer"
                )
            if record["partner_code"] not in valid_country_codes:
                raise RecordValidationError(
                    f"Record at index {index}: invalid partner_code "
                    f"{record['partner_code']}"
                )

            if not isinstance(record["commodity_code"], str):
                raise RecordValidationError(
                    f"Record at index {index}: commodity_code must be a string"
                )
            if record["commodity_code"] not in valid_commodity_codes:
                raise RecordValidationError(
                    f"Record at index {index}: invalid commodity_code "
                    f"{record['commodity_code']}"
                )

            if not isinstance(record["mot_code"], int):
                raise RecordValidationError(
                    f"Record at index {index}: mot_code must be an integer"
                )
            if record["mot_code"] < 0:
                raise RecordValidationError(
                    f"Record at index {index}: mot_code must be greater than or equal to 0"
                )

            if not isinstance(record["qty"], (int, float)):
                raise RecordValidationError(
                    f"Record at index {index}: qty must be numeric"
                )
            if record["qty"] < 0:
                raise RecordValidationError(
                    f"Record at index {index}: qty cannot be negative"
                )

            if not isinstance(record["primary_value"], (int, float)):
                raise RecordValidationError(
                    f"Record at index {index}: primary_value must be numeric"
                )
            if record["primary_value"] < 0:
                raise RecordValidationError(
                    f"Record at index {index}: primary_value cannot be negative"
                )

            if not isinstance(record["is_reported"], bool):
                raise RecordValidationError(
                    f"Record at index {index}: is_reported must be a boolean"
                )

            if not isinstance(record["is_aggregate"], bool):
                raise RecordValidationError(
                    f"Record at index {index}: is_aggregate must be a boolean"
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
            raise

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