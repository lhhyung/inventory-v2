import logging
import copy
import math
import pytz
from typing import Tuple, List
from datetime import datetime

from spaceone.core.model.mongo_model import QuerySet
from spaceone.core.manager import BaseManager
from spaceone.core import utils

from spaceone.inventory_v2.lib.resource_manager import ResourceManager
from spaceone.inventory_v2.manager.identity_manager import IdentityManager
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


class AssetManager(BaseManager, ResourceManager):
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

        params["state"] = "ACTIVE"
        if "asset_id" not in params:
            params["asset_id"] = utils.generate_id("asset")

        asset_vo: Asset = self.asset_model.create(params)
        self.transaction.add_rollback(_rollback, asset_vo)

        return asset_vo

    def update_asset_by_vo(self, params: dict, asset_vo: Asset) -> Asset:
        def _rollback(old_data):
            _LOGGER.info(f'[ROLLBACK] Revert Data : {old_data.get("asset_id")}')
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

    def list_assets(
        self,
        query: dict,
        target: str = None,
        change_filter: bool = False,
        domain_id: str = None,
        reference_filter: dict = None,
    ) -> Tuple[QuerySet, int]:
        if change_filter:
            query = self._change_filter_tags(query)
            query = self._change_only_tags(query)
            query = self._change_sort_tags(query)
            query = self._change_filter_project_group_id(query, domain_id)

            # Append Query for DELETED filter (Temporary Logic)
            query = self._append_state_query(query)

        return self.asset_model.query(
            **query, target=target, reference_filter=reference_filter
        )

    def _change_filter_tags(self, query: dict) -> dict:
        change_filter = []

        for condition in query.get("filter", []):
            key = condition.get("k", condition.get("key"))
            value = condition.get("v", condition.get("value"))
            operator = condition.get("o", condition.get("operator"))

            if key.startswith("tags."):
                hashed_key = self._get_hashed_key(key)

                change_filter.append(
                    {"key": hashed_key, "value": value, "operator": operator}
                )

            else:
                change_filter.append(condition)

        query["filter"] = change_filter
        return query

    def _change_only_tags(self, query: dict) -> dict:
        change_only_tags = []
        if "only" in query:
            for key in query.get("only", []):
                if key.startswith("tags."):
                    hashed_key = self._get_hashed_key(key, only=True)
                    change_only_tags.append(hashed_key)
                else:
                    change_only_tags.append(key)
            query["only"] = change_only_tags

        return query

    def _change_sort_tags(self, query: dict) -> dict:
        if sort_conditions := query.get("sort"):
            change_filter = []
            for condition in sort_conditions:
                sort_key = condition.get("key", "")
                desc = condition.get("desc", False)

                if sort_key.startswith("tags."):
                    hashed_key = self._get_hashed_key(sort_key)
                    change_filter.append({"key": hashed_key, "desc": desc})
                else:
                    change_filter.append({"key": sort_key, "desc": desc})

            query["sort"] = change_filter

        return query

    def _change_filter_project_group_id(self, query: dict, domain_id: str) -> dict:
        change_filter = []
        self.identity_mgr = None

        for condition in query.get("filter", []):
            key = condition.get("k", condition.get("key"))
            value = condition.get("v", condition.get("value"))
            operator = condition.get("o", condition.get("operator"))

            if key == "project_group_id":
                if self.identity_mgr is None:
                    self.identity_mgr = IdentityManager()

                project_groups_info = self.identity_mgr.list_project_groups(
                    {
                        "query": {
                            "only": ["project_group_id"],
                            "filter": [{"k": key, "v": value, "o": operator}],
                        }
                    },
                    domain_id,
                )

                project_group_ids = [
                    project_group_info["project_group_id"]
                    for project_group_info in project_groups_info.get("results", [])
                ]

                project_ids = []

                for project_group_id in project_group_ids:
                    projects_info = self.identity_mgr.get_projects_in_project_group(
                        project_group_id
                    )
                    project_ids.extend(
                        [
                            project_info["project_id"]
                            for project_info in projects_info.get("results", [])
                        ]
                    )

                project_ids = list(set(project_ids))
                change_filter.append({"k": "project_id", "v": project_ids, "o": "in"})

            else:
                change_filter.append(condition)

        query["filter"] = change_filter
        return query

    @staticmethod
    def _get_hashed_key(key: str, only: bool = False) -> str:
        if key.count(".") < 2:
            return key

        prefix, provider, key = key.split(".", 2)
        hash_key = utils.string_to_hash(key)
        if only:
            return f"{prefix}.{provider}.{hash_key}"
        else:
            return f"{prefix}.{provider}.{hash_key}.value"

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

    @staticmethod
    def _append_state_query(query: dict) -> dict:
        state_default_filter = {"key": "state", "value": "ACTIVE", "operator": "eq"}

        show_deleted_resource = False
        for condition in query.get("filter", []):
            key = condition.get("k", condition.get("key"))
            value = condition.get("v", condition.get("value"))
            operator = condition.get("o", condition.get("operator"))

            if key == "state":
                if operator == "eq" and value == "DELETED":
                    show_deleted_resource = True
                elif operator in ["in", "contain_in"] and "DELETED" in value:
                    show_deleted_resource = True

        if not show_deleted_resource:
            query["filter"] = query.get("filter", [])
            query["filter"].append(state_default_filter)

        return query
