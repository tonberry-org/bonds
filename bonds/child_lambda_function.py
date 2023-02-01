from dataclasses import dataclass
from typing import Any, Mapping, Union
from slack_bot_client.slack_client import SlackClient, SlackChannel
import boto3
import logging
import bonds.config as config
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
    bond: str
    from_date: date
    to_date: date


def fetch_lambda_parameters(event: Mapping[str, Any]) -> LambdaParameters:
    body = json.loads(event["Records"][0]["body"])
    result = LambdaParameters(
        bond=body["bond"],
        from_date=date.fromisoformat(body["from_date"]),
        to_date=date.fromisoformat(body["to_date"]),
    )

    newrelic.agent.add_custom_parameter("bond", result.bond)
    newrelic.agent.add_custom_parameter("from_date", result.from_date.isoformat())
    newrelic.agent.add_custom_parameter("to_date", result.to_date.isoformat())
    return result


def decimalize(val: Union[str, float]) -> Decimal:
    return Decimal(val).quantize(Decimal("1.001"))


@newrelic.agent.function_trace()  # type: ignore
def lambda_handler(event: Mapping[str, Any], context: Mapping[str, Any]) -> str:
    parameters = fetch_lambda_parameters(event)
    try:

        api_token = SSM().get_parameter("/eod/api_key")

        query_params = urlencode(
            {
                "api_token": api_token,
                "to": parameters.to_date,
                "from": parameters.from_date,
                "fmt": "json",
            }
        )
        response = session.get(
            f"https://eodhistoricaldata.com/api/eod/{parameters.bond}?{query_params}"
        ).json()

        ddb_table = boto3.resource("dynamodb").Table(config.get_ddb_table())
        with ddb_table.batch_writer() as batch:
            for record in response:
                item = {
                    "bond": parameters.bond,
                    "date": record["date"],
                    "open": decimalize(record["open"]),
                    "high": decimalize(record["high"]),
                    "low": decimalize(record["low"]),
                    "close": decimalize(record["close"]),
                    "adjusted_close": decimalize(record["adjusted_close"]),
                    "volume": int(record["volume"]),
                }
                batch.put_item(Item=item)
    except Exception as e:
        logger.error(f"Error processing {parameters.bond}: {e}")
        newrelic.agent.record_custom_event("error", e)
        raise e

    SlackClient().send(SlackChannel.MONITORING, "OK")
    return "OK"
