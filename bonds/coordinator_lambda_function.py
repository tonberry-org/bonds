from typing import Any, Mapping
import boto3
import logging
import bonds.config as config
import newrelic
from run_log.client import Client as RLClient, RunLogStatus
from datetime import date
import json

logging.basicConfig(
    level=config.get_logging_level(), format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)


def lambda_handler(event: Mapping[str, Any], context: Mapping[str, Any]) -> str:
    logger.info("hello")
    rl_client = RLClient()
    run_log = rl_client.start_run("bonds")
    config_ddb_table = boto3.resource("dynamodb").Table(config.get_config_ddb_table())
    configs = config_ddb_table.scan()["Items"]

    sqs = boto3.resource("sqs")
    queue = sqs.get_queue_by_name(QueueName=config.get_queue_name())
    for config_entry in configs:
        payload = {"bond": config_entry["bond"]}
        queue.send_message(MessageBody=json.dumps(payload))

    run_log.status = RunLogStatus.COMPLETED
    rl_client.update_run_log(run_log)

    # SlackClient().send(SlackChannel.MONITORING, "OK")
    return "OK"
