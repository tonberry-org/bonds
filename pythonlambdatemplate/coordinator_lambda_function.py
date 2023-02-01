from typing import Any, Mapping
from slack_bot_client.slack_client import SlackClient, SlackChannel
import boto3
from boto3.dynamodb.conditions import Key
import logging
import pytonlambdatemplate.config as config
import newrelic
from run_log.client import Client as RLClient, RunLogStatus
from datetime import date
import json

logging.basicConfig(
    level=config.get_logging_level(), format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_constituents() -> list[dict[str, str]]:
    ddb_constituents_table = boto3.resource("dynamodb").Table(
        config.get_ddb_constituents_table()
    )
    constituents = ddb_constituents_table.scan(
        FilterExpression=Key("is_active_now").eq(1)
    )["Items"]
    return constituents  # type: ignore


@newrelic.agent.function_trace()  # type: ignore
def lambda_handler(event: Mapping[str, Any], context: Mapping[str, Any]) -> str:
    newrelic.agent.add_custom_parameter("test", 1234)
    logger.info("hello")
    rl_client = RLClient()
    run_log = rl_client.start_run("pytonlambdatemplate")
    indiactor_ddb_table = boto3.resource("dynamodb").Table(
        config.get_config_ddb_table()
    )
    indicators = indiactor_ddb_table.scan()["Items"]

    previous_run_log = rl_client.find_last(
        "pytonlambdatemplate", RunLogStatus.COMPLETED
    )
    from_date = (
        previous_run_log.start_datetime().date()
        if previous_run_log is not None
        else date.fromisoformat("2023-01-01")
    )
    to_date = date.today()

    sqs = boto3.resource("sqs")
    queue = sqs.get_queue_by_name(QueueName=config.get_queue_name())
    for indicator in indicators:
        payload = {"indicator": indicator, to_date: to_date, from_date: from_date}
        queue.send_message(MessageBody=json.dumps(payload))

    rl_client.update_run_log(run_log, RunLogStatus.COMPLETED)
    run_log.status = RunLogStatus.COMPLETED
    SlackClient().send(SlackChannel.MONITORING, "OK")
    return "OK"
