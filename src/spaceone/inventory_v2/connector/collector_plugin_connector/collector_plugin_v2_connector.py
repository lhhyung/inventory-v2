from spaceone.inventory_v2.connector import BaseCollectorPluginConnector


class CollectorPluginV2Connector(BaseCollectorPluginConnector):
    collector_version = "v1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def verify_plugin(self, endpoint, secret_data, options):
        pass

    def get_tasks(self, params):
        pass

    def collect(self, params):
        pass
