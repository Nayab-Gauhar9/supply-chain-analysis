import logging
import time
import requests
from .config_loader import load_settings

logger= logging.getLogger(__name__)

class API_Error(Exception):
    pass
class RetryableAPIError(API_Error):
    pass


settings = load_settings()
api_settings= settings["api"]

base_url= api_settings["base_url"]
timeout= api_settings["timeout_seconds"]
max_retries= api_settings["max_retries"]
backoff_factor= api_settings["backoff_factor"]
rate_limit= api_settings["rate_limit_per_second"]
request_interval= 1/rate_limit
last_request_time=0

retryable_codes= {429, 500, 502, 503, 504}

def get_data(params, headers):
    global last_request_time

    for attempt in range(max_retries + 1):

        elapsed = time.monotonic() - last_request_time
        if elapsed < request_interval:
            time.sleep(request_interval - elapsed)
        last_request_time= time.monotonic()

        try:
            response = requests.get(
                base_url,
                params=params,
                headers= headers,
                timeout=timeout
            )
            if response.status_code in retryable_codes:
                raise RetryableAPIError(f"Retryable HTTP Status: {response.status_code}")

            response.raise_for_status()

            data = response.json()

            return data

        except (requests.Timeout, requests.ConnectionError, RetryableAPIError) as e:
            if attempt == max_retries:
                logger.error(
                    f"API request failed after {max_retries + 1} attempts: {e}"
                )
                raise API_Error(
                    f"API request failed after retries: {e}"
                ) from e

            delay = backoff_factor ** attempt

            logger.warning(
                f"Temporary API failure: {e}. "
                f"Retrying in {delay} seconds "
                f"(attempt {attempt + 1}/{max_retries + 1})"
            )

            time.sleep(delay)