import logging
from .config_loader import load_commodities, load_countries, load_settings
from .api_client import get_data
from .object_storage import upload_json
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

load_dotenv()
token = os.getenv("API_TOKEN")

settings = load_settings()
countries = load_countries()
commodities = load_commodities()

def get_commodity_config(commodity_name):
    for commodity in commodities:
        if commodity["name"].lower() == commodity_name.lower():
            return commodity

    raise ValueError(
        f"Commodity not found in configuration: {commodity_name}"
    )

def get_country_config(country_name):
    for country in countries:
        if country["name"].lower() == country_name.lower():
            return country

    raise ValueError(f"Country not found in configuration: {country_name}")

def build_params(country, partner_country, commodity, period, flow_code):
    country_config = get_country_config(country)
    partner_config = get_country_config(partner_country)

    if isinstance(commodity, list):
        cmd_codes = ",".join(
            get_commodity_config(item)["hs_code"]
            for item in commodity
        )
    else:
        cmd_codes = get_commodity_config(commodity)["hs_code"]

    params = {
        "reporterCode": country_config["code"],
        "partnerCode": partner_config["code"],
        "partner2Code": 0,
        "flowCode": flow_code,
        "period": period,
        "cmdCode": cmd_codes,
    }

    return params

def extract_data(country, partner_country, commodity, period, flow_code):
    params = build_params(
        country,
        partner_country,
        commodity,
        period,
        flow_code
    )

    logger.info(
        f"Extracting data: "
        f"{country} -> {partner_country}, "
        f"{commodity}, {period}, {flow_code}"
    )

    headers = {
    "User-Agent" : "SupplyChainAmalysis/1.0",
    'Cache-Control': 'no-cache',
    'Ocp-Apim-Subscription-Key': f'{token}',
    }
    
    try:
        data = get_data(params, headers)

        logger.info(
            f"Data extraction successful: "
            f"{country} → {partner_country}, "
            f"{commodity}, {period}, {flow_code}"
        )

        return data

    except Exception as e:
        logger.error(
            f"Data extraction failed: "
            f"{country} → {partner_country}, "
            f"{commodity}, {period}, {flow_code}: {e}"
            )
        raise

def generate_trade_flows(countries):
    india = next(
        country for country in countries
        if country["name"].lower() == "india"
    )

    flows = []

    for country in countries:
        if country["name"].lower() == "india":
            continue

        flows.append({
            "reporter": india,
            "partner": country,
            "direction": "export"
        })

        flows.append({
            "reporter": country,
            "partner": india,
            "direction": "import"
        })

    return flows

def run_extraction(flows, commodities, period):
    results = []
    failed_extraction = []

    for flow in flows:
        reporter = flow["reporter"]["name"]
        partner = flow["partner"]["name"]
        direction = flow["direction"]

        if direction == "export":
            flow_code = "X"
        else:
            flow_code = "M"

        logger.info(
            f"Running extraction: "
            f"{reporter} -> {partner} | "
            f"{direction} | flow_code={flow_code}"
        )
        try:
            data = extract_data(
                reporter,
                partner,
                commodities,
                period,
                flow_code
            )

            raw_object = {
                "metadata": {
                    "reporter": reporter,
                    "partner": partner,
                    "flow": flow_code,
                    "direction": direction,
                    "period": period,
                    "commodities": [
                        {
                            "name": get_commodity_config(commodity)["name"],
                            "hs_code": get_commodity_config(commodity)["hs_code"]
                        }
                        for commodity in commodities
                    ]
                },
                "response": data
            }

            object_name = (
                f"raw/{period}/"
                f"{reporter}_{partner}_{flow_code}.json"
            )

            logger.info(
                f"Uploading object: {object_name}"
            )

            upload_json(
                raw_object,
                object_name
            )

            results.append({
                "reporter": reporter,
                "partner": partner,
                "direction": direction,
                "data": data
            })
        except Exception as e:
            logger.error(
                f"Extraction Failed:"
                f"{reporter} -> {partner} | "
                f"{period} | {flow_code} | {e}"
            )
            failed_extraction.append({
                "reporter" : reporter,
                "partner" : partner,
                "period" : period,
                "flow_code" : flow_code,
                "error" : str(e)
            })
            continue
            

    return results, failed_extraction

if __name__ == "__main__":
    countries = load_countries()

    flows = generate_trade_flows(countries)

    commodity_names = [commodity["name"] for commodity in commodities]

    years = ["2022","2024"]

    total_extractions = 0
    all_failures = []

    for year in years:
        logger.info(f"Starting extraction for {year}")

        results, failures = run_extraction(
            flows,
            commodity_names,
            year
        )

        total_extractions += len(results)
        all_failures.extend(failures)

    print(f"Total successful extractions: {total_extractions}")
    print(f"Total failed extractions: {len(all_failures)}")

    print("\nFailed extractions:")

    for failure in all_failures:
        print(
            f"{failure['reporter']} -> "
            f"{failure['partner']} | "
            f"{failure['period']} | "
            f"{failure['flow_code']} | "
            f"{failure['error']}"
        )
