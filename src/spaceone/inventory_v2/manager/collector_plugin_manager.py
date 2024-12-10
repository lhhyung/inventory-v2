import logging
from typing import Generator, Union
from spaceone.core.manager import BaseManager

from spaceone.inventory_v2.connector import (
    BaseCollectorPluginConnector as PluginConnector,
)

__ALL__ = ["CollectorPluginManager"]

_LOGGER = logging.getLogger(__name__)


class CollectorPluginManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def init_plugin(endpoint: str, options: dict) -> dict:
        return PluginConnector.init_plugin(endpoint, options)

    def verify_plugin(self, endpoint: str, options: dict, secret_data: dict) -> None:
        self.collector_version = options.get("collector_version", "v1")
        collector_plugin_conn = PluginConnector.get_connector_by_collector_version(
            self.collector_version
        )
        collector_plugin_conn.verify_plugin(endpoint, options, secret_data)

    def get_tasks(self, endpoint: str, secret_data: dict, options: dict) -> dict:
        self.collector_version = options.get("collector_version", "v1")
        collector_plugin_conn: PluginConnector = (
            PluginConnector.get_connector_by_collector_version(self.collector_version)
        )
        return collector_plugin_conn.get_tasks(endpoint, secret_data, options)

    def collect(
        self,
        endpoint: str,
        options: dict,
        secret_data: dict,
        task_options: dict = None,
    ) -> Generator[dict, None, None]:
        self.collector_version = options.get("collector_version", "v1")
        collector_plugin_conn = PluginConnector.get_connector_by_collector_version(
            self.collector_version
        )
        return collector_plugin_conn.collect(
            endpoint, options, secret_data, task_options
        )
