import logging

from typing import Generator

from spaceone.core.connector.space_connector import SpaceConnector

from spaceone.inventory_v2.connector.collector_plugin_connector import (
    BaseCollectorPluginConnector,
)

_LOGGER = logging.getLogger(__name__)


class CollectorPluginV1Connector(BaseCollectorPluginConnector):
    collector_version = "v1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def verify_plugin(self, endpoint: str, secret_data: dict, options: dict) -> dict:
        plugin_connector = SpaceConnector(endpoint=endpoint, token="NO_TOKEN")
        params = {"options": options, "secret_data": secret_data}
        return plugin_connector.dispatch("Collect.collect", params)

    def get_tasks(self, endpoint: str, options: dict, secret_data: dict) -> dict:
        try:
            plugin_connector = SpaceConnector(endpoint=endpoint, token="NO_TOKEN")
            params = {"options": options, "secret_data": secret_data}
            return plugin_connector.dispatch("Job.get_tasks", params)
        except Exception as e:
            return {"tasks": []}

    def collect(
        self,
        endpoint: str,
        options: dict,
        secret_data: dict,
        task_options: dict = None,
    ) -> Generator[dict, None, None]:
        plugin_connector = SpaceConnector(endpoint=endpoint, token="NO_TOKEN")

        params = {"options": options, "secret_data": secret_data, "filter": {}}

        if task_options:
            params["task_options"] = task_options

        for resource_data in plugin_connector.dispatch("Collector.collect", params):
            yield self._convert_resource_data(resource_data)

    @staticmethod
    def _convert_resource_data(resource_data: dict) -> dict:
        _LOGGER.debug(
            f"[_convert_resource_data] before convert resource_data: {resource_data}"
        )

        resource_type = resource_data.get("resource_type")

        if resource_type in ["inventory.CloudService", "inventory.CloudServiceType"]:
            if resource_type == "inventory.CloudService":
                resource_data["resource_type"] = "inventory.Asset"
                resource_data["resource"]["asset_type_id"] = resource_data[
                    "resource"
                ].get("asset_type")
                # resource_data["resource"]["asset_group_id"] = resource_data[
                #     "resource"
                # ].get("cloud_service_group")
            elif resource_type == "inventory.CloudServiceType":
                resource_data["resource_type"] = "inventory.AssetType"

            resource_type = resource_data.get("resource_type")

            # convert match rule
            for rule_values in resource_data.get("match_rules", {}).values():
                for index, rule_value in enumerate(rule_values):
                    if rule_value == "cloud_service_id":
                        rule_values[index] = "asset_id"
                    elif rule_value == "cloud_service_type":
                        rule_values[index] = "asset_type_id"
                    elif rule_value == "cloud_service_group":
                        del rule_values[index]
                    elif rule_value == "reference.resource_id":
                        rule_values[index] = "resource_id"
                    elif rule_value == "group":
                        rule_values[index] = "asset_group_id"

            if _resource := resource_data.get("resource"):
                _resource_v1 = {}
                if "instance_size" in _resource:
                    _resource_v1["instance_size"] = _resource.pop("instance_size")
                if "instance_type" in _resource:
                    _resource_v1["instance_type"] = _resource.pop("instance_type")
                del _resource["metadata"]

                if resource_type == "inventory.Asset":
                    asset_type_id = f"{_resource['provider']}.{_resource['cloud_service_group']}.{_resource['cloud_service_type']}"
                    _resource["asset_type_id"] = asset_type_id
                    resource_data["asset_type_id"] = asset_type_id
                elif resource_type == "inventory.AssetType":

                    asset_type_id = f"at-{_resource['provider']}-{_resource['group']}-{_resource['name']}"
                    asset_groups = [
                        f"ag-{_resource['provider']}-{_resource['group']}",
                        f"ag-{_resource['provider']}",
                    ]
                    _resource["asset_type_id"] = asset_type_id
                    resource_data["asset_type_id"] = asset_type_id
                    resource_data["asset_groups"] = asset_groups
                    resource_data["icon"] = _resource.get("tags", {}).get("icon", "")

                resource_data["resource"]["v1"] = _resource_v1

        _LOGGER.debug(f"[_convert_resource_data] resource_data: {resource_data}")

        return resource_data
