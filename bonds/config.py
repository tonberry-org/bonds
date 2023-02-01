import os
import logging
from typing import Union


class ConfigException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def get_or_throw(key: str) -> str:
    value = os.environ.get(key)
    if value is None:
        raise ConfigException(f"Missing config for [{key}]")
    return value


def get_logging_level() -> Union[str, int]:
    return os.environ.get("LOG_LEVEL") or logging.INFO


def get_config_ddb_table() -> str:
    return get_or_throw("CONFIG_DDB_TABLE")


def get_ddb_table() -> str:
    return get_or_throw("DDB_TABLE")


def get_ddb_constituents_table() -> str:
    return get_or_throw("CONSTITUENTS_DDB_TABLE")


def get_queue_name() -> str:
    return get_or_throw("QUEUE_NAME")
