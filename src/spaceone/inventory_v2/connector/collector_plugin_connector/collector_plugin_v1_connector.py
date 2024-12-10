import logging

from typing import Generator

from spaceone.core.connector.space_connector import SpaceConnector
from spaceone.core.error import ERROR_BASE

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
    def _convert_match_rule(resource_data: dict, resource_type: str) -> dict:
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
                elif rule_value == "name":
                    if resource_type == "inventory.AssetType":
                        rule_values[index] = "asset_type_id"
        return resource_data

    def _convert_resource_data(self, resource_data: dict) -> dict:

        if "resource" in resource_data and "metadata" in resource_data["resource"]:
            del resource_data["resource"]["metadata"]

        _LOGGER.debug(
            f"[_convert_resource_data] before convert resource_data: {resource_data}"
        )

        resource_type = resource_data.get("resource_type")
        if resource_type == "inventory.Region":
            pass

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
            resource_data = self._convert_match_rule(resource_data, resource_type)

            # convert keywords [instance_size, instance_type, ]
            if _resource := resource_data.get("resource"):
                # del _resource["metadata"]

                if "instance_size" in _resource:
                    _resource["data"]["instance_size"] = _resource.pop("instance_size")
                if "instance_type" in _resource:
                    _resource["data"]["instance_type"] = _resource.pop("instance_type")

                if "region_code" in _resource:
                    _resource["region_id"] = (
                        f"{_resource['provider']}-{_resource['region_code']}"
                    )

                if resource_type == "inventory.Asset":
                    asset_type_id = f"{_resource['provider']}-{_resource['cloud_service_group']}-{_resource['cloud_service_type']}"
                    _resource["asset_type_id"] = asset_type_id
                    resource_data["asset_type_id"] = asset_type_id

                    if "reference" in _resource:
                        _resource["resource_id"] = _resource["reference"].get(
                            "resource_id"
                        )
                        _resource["external_link"] = _resource["reference"].get(
                            "external_link"
                        )

                elif resource_type == "inventory.AssetType":

                    asset_type_id = f"at-{_resource['provider']}-{_resource['group']}-{_resource['name']}"
                    asset_groups = [
                        f"ag-{_resource['provider']}-{_resource['group']}",
                        f"ag-{_resource['provider']}",
                    ]
                    _resource["asset_type_id"] = asset_type_id
                    resource_data["asset_type_id"] = asset_type_id
                    resource_data["asset_groups"] = asset_groups

                    resource_data["icon"] = resource_data.get("tags", {}).get(
                        "spaceone:icon", ""
                    )

        _LOGGER.debug(f"[_convert_resource_data] resource_data: {resource_data}")

        return resource_data
