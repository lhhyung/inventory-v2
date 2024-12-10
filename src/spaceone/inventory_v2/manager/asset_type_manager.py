import copy
import logging
from typing import Tuple

from spaceone.core.model.mongo_model import QuerySet
from spaceone.core import utils
from spaceone.core.manager import BaseManager
from spaceone.inventory_v2.model.asset_type.database import AssetType
from spaceone.inventory_v2.lib.resource_manager import ResourceManager

_LOGGER = logging.getLogger(__name__)


class AssetTypeManager(BaseManager, ResourceManager):
    resource_keys = ["asset_type_id"]
    query_method = "list_asset_types"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset_type_model = AssetType

    def create_asset_type(self, params: dict) -> AssetType:
        def _rollback(vo: AssetType):
            _LOGGER.info(
                f"[ROLLBACK] Delete Asset Type : {vo.name} ({vo.asset_type_id})"
            )
            vo.delete()

        if "asset_type_id" not in params:
            params["asset_type_id"] = utils.generate_id("asset-type")
        if is_managed := params.get("is_managed", False):
            params["is_managed"] = is_managed

        asset_type_vo: AssetType = self.asset_type_model.create(params)
        self.transaction.add_rollback(_rollback, asset_type_vo)

        return asset_type_vo

    def update_asset_type_by_vo(self, params: dict, asset_type_vo: AssetType):
        def _rollback(old_data):
            _LOGGER.info(f'[ROLLBACK] Revert Data : {old_data.get("asset_Type_id")}')
            asset_type_vo.update(old_data)

        self.transaction.add_rollback(_rollback, asset_type_vo.to_dict())

        return asset_type_vo.update(params)

    @staticmethod
    def delete_asset_type_by_vo(asset_type_vo: AssetType) -> None:
        asset_type_vo.delete()

    def get_asset_type(
        self,
        asset_type_id: str,
        domain_id: str,
        workspace_id: str = None,
    ) -> AssetType:
        conditions = {
            "asset_type_id": asset_type_id,
            "domain_id": domain_id,
        }

        if workspace_id:
            conditions.update({"workspace_id": workspace_id})

        return self.asset_type_model.get(**conditions)

    def filter_asset_types(self, **conditions) -> QuerySet:
        return self.asset_type_model.filter(**conditions)

    def list_asset_types(self, query: dict) -> Tuple[QuerySet, int]:
        asset_type_vos, total_count = self.asset_type_model.query(**query)
        return asset_type_vos, total_count

    def stat_asset_types(self, query: dict) -> dict:
        return self.asset_type_model.stat(**query)
