from dataclasses import dataclass
from typing import Any, Mapping
from slack_bot_client.slack_client import SlackClient, SlackChannel
import boto3
import logging
import pythonlambdatemplate.config as config
import newrelic
import json
from datetime import date
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlencode
from common.ssm import SSM
from decimal import Decimal

logging.basicConfig(
    level=config.get_logging_level(), format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

session = requests.Session()
retry_strategy = Retry(
    total=10, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=2
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)


@dataclass
class LambdaParameters:
    indicator: str
    date_from: date
    date_to: date


def fetch_lambda_parameters(event: Mapping[str, Any]) -> LambdaParameters:
    body = json.loads(event["Records"][0]["body"])
    result = LambdaParameters(
        indicator=body["indicator"],
        date_from=date.fromisoformat(body["date_from"]),
        date_to=date.fromisoformat(body["date_to"]),
    )

    newrelic.agent.add_custom_parameter("indicator", result.indicator)
    return result


@newrelic.agent.function_trace()  # type: ignore
def lambda_handler(event: Mapping[str, Any], context: Mapping[str, Any]) -> str:
    parameters = fetch_lambda_parameters(event)
    try:

        api_token = SSM().get_parameter("/eod/api_key")

        query_params = urlencode(
            {
                "api_token": api_token,
                "indicator": parameters.indicator,
                "to": parameters.date_to,
                "from": parameters.date_from,
            }
        )
        response = session.get(
            f"https://eodhistoricaldata.com/api/macro-indicator/USA?{query_params}"
        ).json()

        ddb_table = boto3.resource("dynamodb").Table(config.get_ddb_table())
        with ddb_table.batch_writer() as batch:
            for record in response:
                item = {
                    "country_code": record["CountryCode"],
                    "country_name": record["CountryName"],
                    "indicator": parameters.indicator,
                    "date": record["Date"],
                    "period": record["Period"],
                    "value": Decimal(record["Value"]).quantize(Decimal("0.0001")),
                    "description": record["Indicator"],
                }
                batch.put_item(Item=item)
    except Exception as e:
        logger.error(f"Error processing {parameters.indicator}: {e}")
        newrelic.agent.record_custom_event("error", e)

    SlackClient().send(SlackChannel.MONITORING, "OK")
    return "OK"
