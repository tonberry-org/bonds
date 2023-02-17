from dataclasses import dataclass
from typing import Any, Mapping, Union
from slack_bot_client.slack_client import SlackClient, SlackChannel
import boto3
import logging
import bonds.config as config
import newrelic
import json
from datetime import date, datetime, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlencode
from common.ssm import SSM
from decimal import Decimal
from run_log.client import Client as RLClient, RunLogStatus, RunLog
import uuid

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


def fetch_lambda_parameters(event: Mapping[str, Any]) -> LambdaParameters:
    body = json.loads(event["Records"][0]["body"])
    result = LambdaParameters(bond=body["bond"])

    newrelic.agent.add_custom_parameter("bond", result.bond)
    return result


def decimalize(val: Union[str, float]) -> Decimal:
    return Decimal(val).quantize(Decimal("1.001"))


PROCESS_TYPE = "bonds"


def filter_by_date(from_date: date, to_date: date, input_date_str: str) -> bool:
    input_date = date.fromisoformat(input_date_str)
    return input_date > from_date and input_date <= to_date


@newrelic.agent.function_trace()  # type: ignore
def determine_from_date(last_run: RunLog) -> date:
    if (
        last_run is not None
        and last_run.parameters is not None
        and "last" in last_run.parameters
    ):
        result = date.fromisoformat(last_run.parameters["last"])
    else:
        result = date(2016, 1, 1)
    newrelic.agent.add_custom_parameter("from_date", result)
    return result


@newrelic.agent.function_trace()  # type: ignore
def lambda_handler(event: Mapping[str, Any], context: Mapping[str, Any]) -> str:
    s3 = boto3.resource("s3")
    parameters = fetch_lambda_parameters(event)
    to_date = datetime.now(timezone.utc).date()
    try:
        rl_client = RLClient()
        last_run = rl_client.find_last(f"{PROCESS_TYPE}:{parameters.bond}")
        from_date = determine_from_date(last_run)
        run_log = rl_client.start_run(
            PROCESS_TYPE,
            parameters={
                "to_date": to_date.isoformat(),
                "from_date": from_date.isoformat(),
            },
        )

        api_token = SSM().get_parameter("/eod/api_key")

        query_params = urlencode(
            {
                "api_token": api_token,
                "to": to_date.isoformat(),
                "from": from_date.isoformat(),
                "fmt": "json",
            }
        )
        response = session.get(
            f"https://eodhistoricaldata.com/api/eod/{parameters.bond}?{query_params}"
        ).json()

        bonds = list(
            filter(
                lambda x: filter_by_date(from_date, to_date, x["date"]),
                response,
            )
        )

        if len(bonds) > 0:
            max_date = max(
                list(map(lambda row: row["date"], bonds)) + [from_date.isoformat()]
            )
            for row in bonds:
                row["bond"] = parameters.bond
            object = s3.Object(
                config.get_raw_s3_bucket(),
                f"{parameters.bond}-{from_date}-{uuid.uuid4()}.json",
            )
            object.put(Body=json.dumps(bonds))
            run_log.parameters["last"] = max_date
        run_log.status = RunLogStatus.COMPLETED
        rl_client.update_run_log(run_log=run_log)
    except Exception as e:
        logger.error(f"Error processing {parameters.bond}: {e}")
        run_log.status = RunLogStatus.ERROR
        rl_client.update_run_log(run_log=run_log)
        raise e

    SlackClient().send(SlackChannel.MONITORING, "OK")
    return "OK"
