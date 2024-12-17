import logging
import os
from typing import List

from spaceone.core import utils
from spaceone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)
CURRENT_DIR = os.path.dirname(__file__)
_NAMESPACE_GROUP_DIR = os.path.join(CURRENT_DIR, "../managed_resource/namespace_group/")
_NAMESPACE_DIR = os.path.join(CURRENT_DIR, "../managed_resource/namespace/")
_METRIC_DIR = os.path.join(CURRENT_DIR, "../managed_resource/metric/")


class ManagedResourceManager(BaseManager):
    
    def get_managed_namespace_groups(self) -> dict:
        namespace_group_map = {}
        for namespace_group_info in self._load_managed_resources(_NAMESPACE_GROUP_DIR):
            namespace_group_map[namespace_group_info["namespace_group_id"]] = namespace_group_info

        return namespace_group_map
    
    def get_managed_namespaces(self) -> dict:
        namespace_map = {}
        for namespace_info in self._load_managed_resources(_NAMESPACE_DIR):
            namespace_map[namespace_info["namespace_id"]] = namespace_info

        return namespace_map

    def get_managed_metrics(self) -> dict:
        metric_map = {}
        for metric_info in self._load_managed_resources(_METRIC_DIR):
            metric_map[metric_info["metric_id"]] = metric_info

        return metric_map

    @staticmethod
    def _load_managed_resources(dir_path: str) -> List[dict]:
        managed_resources = []
        for filename in os.listdir(dir_path):
            if filename.endswith(".yaml"):
                file_path = os.path.join(dir_path, filename)
                managed_resource_info = utils.load_yaml_from_file(file_path)
                managed_resources.append(managed_resource_info)
        return managed_resources
