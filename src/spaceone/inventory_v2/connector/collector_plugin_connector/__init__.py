from spaceone.core.connector import BaseConnector
from spaceone.core.connector.space_connector import SpaceConnector


class BaseCollectorPluginConnector(BaseConnector):
    collector_version = None

    @classmethod
    def init_plugin(cls, endpoint: str, options: dict) -> dict:
        plugin_connector = SpaceConnector(endpoint=endpoint, token="NO_TOKEN")
        return plugin_connector.dispatch("Collector.init", {"options": options})

    def verify_plugin(self, *args, **kwargs):
        raise NotImplementedError()

    def get_tasks(self, *args, **kwargs):
        raise NotImplementedError()

    def collect(self, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def get_connector_by_collector_version(cls, collector_version: str):
        for subclass in cls.__subclasses__():
            if subclass.collector_version == collector_version:
                return subclass()
        raise Exception(f"Not found collector plugin connector: {collector_version}")
