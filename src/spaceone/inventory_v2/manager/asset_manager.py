import logging
import copy
import math
import pytz
from typing import Tuple, List
from datetime import datetime

from spaceone.core.model.mongo_model import QuerySet
from spaceone.core.manager import BaseManager
from spaceone.core import utils

from spaceone.inventory_v2.model.asset.database import Asset

_LOGGER = logging.getLogger(__name__)

MERGE_KEYS = [
    "name",
    "ip_addresses",
    "account",
    "instance_type",
    "instance_size",
    "reference",
    "region_code",
    "ref_region",
    "project_id",
    "data",
]

SIZE_MAP = {
    "KB": 1024,
    "MB": 1024 * 1024,
    "GB": 1024 * 1024 * 1024,
    "TB": 1024 * 1024 * 1024 * 1024,
    "PB": 1024 * 1024 * 1024 * 1024 * 1024,
    "EB": 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
    "ZB": 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
    "YB": 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024,
}


class AssetManager(BaseManager):
    resource_keys = ["asset_id"]
    query_method = "list_assets"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset_model = Asset

    def create_asset(self, params: dict) -> Asset:
        def _rollback(vo: Asset):
            _LOGGER.info(
                f"[ROLLBACK] Delete asset : {vo.provider} ({vo.asset_type_id})"
            )
            vo.terminate()

        asset_vo: Asset = self.asset_model.create(params)
        self.transaction.add_rollback(_rollback, asset_vo)

        return asset_vo

    def update_asset_by_vo(self, params: dict, asset_vo: Asset) -> Asset:
        def _rollback(old_data):
            _LOGGER.info(f'[ROLLBACK] Revert Data : {old_data.get("cloud_service_id")}')
            asset_vo.update(old_data)

        self.transaction.add_rollback(_rollback, asset_vo.to_dict())
        asset_vo: Asset = asset_vo.update(params)

        return asset_vo

    @staticmethod
    def delete_cloud_service_by_vo(asset_vo: Asset) -> None:
        asset_vo.delete()

    def get_asset(
        self,
        asset_id: str,
        domain_id: str,
        workspace_id: str = None,
        user_projects: list = None,
    ):
        conditions = {"asset_id": asset_id, "domain_id": domain_id}

        if workspace_id:
            conditions["workspace_id"] = workspace_id

        if user_projects:
            conditions["project_id"] = user_projects

        return self.asset_model.get(**conditions)

    @staticmethod
    def merge_data(new_data: dict, old_data: dict) -> dict:
        for key in MERGE_KEYS:
            if key in new_data:
                new_value = new_data[key]
                old_value = old_data.get(key)
                if key in ["data", "tags"]:
                    is_changed = False
                    for sub_key, sub_value in new_value.items():
                        if sub_value != old_value.get(sub_key):
                            is_changed = True
                            break

                    if is_changed:
                        merged_value = copy.deepcopy(old_value)
                        merged_value.update(new_value)
                        new_data[key] = merged_value
                    else:
                        del new_data[key]
                else:
                    if new_value == old_value:
                        del new_data[key]

        return new_data
