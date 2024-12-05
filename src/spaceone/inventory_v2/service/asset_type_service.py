import logging
import copy
import pytz
from datetime import datetime
from typing import List, Union, Tuple

from mongoengine import QuerySet
from spaceone.core.service import *
from spaceone.core import utils

from spaceone.inventory_v2.manager import AssetTypeManager
from spaceone.inventory_v2.manager.asset_manager import AssetManager
from spaceone.inventory_v2.manager.collection_state_manager import (
    CollectionStateManager,
)
from spaceone.inventory_v2.manager.collector_rule_manager import CollectorRuleManager
from spaceone.inventory_v2.manager.identity_manager import IdentityManager
from spaceone.inventory_v2.model.asset.database import Asset
from spaceone.inventory_v2.model.asset.request import *
from spaceone.inventory_v2.model.asset.response import *
from spaceone.inventory_v2.error import *
from spaceone.inventory_v2.model.asset_type.database import AssetType
from spaceone.inventory_v2.model.asset_type.response import AssetTypeResponse

_KEYWORD_FILTER = [
    "asset_id",
    "name",
    "ip_addresses",
    "cloud_service_group",
    "cloud_service_type",
    "reference.resource_id",
]

_LOGGER = logging.getLogger(__name__)

_KEYWORD_FILTER = ["asset_type_id", "name", "asset_group_id", "service_code"]


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class AssetTypeService(BaseService):
    resource = "AssetType"

    def __init__(self, metadata):
        super().__init__(metadata)
        self.asset_type_mgr = AssetTypeManager()

    @transaction(
        permission="inventory-v2:CloudServiceType.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def create(self, params: AssetGetRequest) -> AssetTypeResponse:
        """
        Args:
            params (dict): {
                'name': 'str',              # required
                'group': 'str',             # required
                'provider': 'str',          # required
                'service_code': 'str',
                'is_primary': 'bool',
                'is_major': 'bool',
                'resource_type': 'str',
                'json_metadata': 'str',
                'metadata': 'dict',
                'labels': 'list,
                'tags': 'dict',
                'workspace_id': 'str',      # injected from auth (required)
                'domain_id': 'str'          # injected from auth (required)
            }

        Returns:
            asset_type_vo (object)
        """

        asset_type_vo = self.create_resource(params.dict())
        return AssetTypeResponse(**asset_type_vo.to_dict())

    @check_required(["name", "provider", "resource_group", "domain_id"])
    def create_resource(self, params: dict) -> AssetType:
        if json_metadata := params.get("json_metadata"):
            params["metadata"] = utils.load_json(json_metadata)
            if not isinstance(params["metadata"], dict):
                raise ERROR_INVALID_PARAMETER_TYPE(
                    key="json_metadata", type=type(params["metadata"])
                )

            del params["json_metadata"]

        if "tags" in params:
            if isinstance(params["tags"], list):
                params["tags"] = utils.tags_to_dict(params["tags"])

        params["updated_by"] = self.transaction.get_meta("collector_id") or "manual"

        provider = params.get("provider", self.transaction.get_meta("secret.provider"))

        if provider:
            params["provider"] = provider

        params["resource_type"] = params.get("resource_type", "inventory.Asset")

        return self.asset_type_mgr.create_asset_type(params)

    @transaction(
        permission="inventory:CloudServiceType.write",
        role_types=["WORKSPACE_OWNER"],
    )
    def update(self, params: dict) -> AssetType:
        """
        Args:
            params (dict): {
                'cloud_service_type_id': 'str',     # required
                'service_code': 'str',
                'is_primary': 'bool',
                'is_major': 'bool',
                'resource_type': 'str',
                'json_metadata': 'str',
                'metadata': 'dict',
                'labels': 'list',
                'tags': 'dict',
                'workspace_id': 'str',              # injected from auth (required)
                'domain_id': 'str'                  # injected from auth (required)
            }

        Returns:
            cloud_service_type_vo (object)
        """

        return self.update_resource(params)

    @check_required(["cloud_service_type_id", "workspace_id", "domain_id"])
    def update_resource(self, params: dict) -> AssetType:
        if json_metadata := params.get("json_metadata"):
            params["metadata"] = utils.load_json(json_metadata)
            if not isinstance(params["metadata"], dict):
                raise ERROR_INVALID_PARAMETER_TYPE(
                    key="json_metadata", type=type(params["metadata"])
                )

            del params["json_metadata"]

        if "tags" in params:
            if isinstance(params["tags"], list):
                params["tags"] = utils.tags_to_dict(params["tags"])

        params["updated_by"] = self.transaction.get_meta("collector_id") or "manual"
        domain_id = params["domain_id"]

        cloud_svc_type_vo = self.asset_type_mgr.get_asset_type(
            params["asset_type_id"], domain_id
        )

        return self.asset_type_mgr.update_asset_type_by_vo(params, cloud_svc_type_vo)

    @transaction(
        permission="inventory:AssetType.write",
        role_types=["WORKSPACE_OWNER"],
    )
    def delete(self, params: dict) -> None:
        """
        Args:
        params (dict): {
            'cloud_service_type_id': 'str',     # required
            'workspace_id': 'str',              # injected from auth (required)
            'domain_id': 'str'                  # injected from auth (required)
        }
        Returns:
            None
        """

        self.delete_resource(params)

    @check_required(["cloud_service_type_id", "workspace_id", "domain_id"])
    def delete_resource(self, params: dict) -> None:
        asset_type_vo = self.asset_type_mgr.get_asset_type(
            params["cloud_service_type_id"], params["domain_id"], params["workspace_id"]
        )

        self.asset_type_mgr.delete_asset_type_by_vo(asset_type_vo)

    @transaction(
        permission="inventory:AssetType.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["cloud_service_type_id", "domain_id"])
    def get(self, params: dict) -> AssetType:
        """
        Args:
            params (dict): {
                'cloud_service_type_id': 'str',     # required
                'workspace_id': 'str',              # injected from auth
                'domain_id': 'str',                 # injected from auth (required)
            }

        Returns:
            cloud_service_type_vo (object)

        """

        return self.asset_type_mgr.get_asset_type(
            params["asset_type_id"],
            params["domain_id"],
            params.get("workspace_id"),
        )

    @transaction(
        permission="inventory:AssetType.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["domain_id"])
    @append_query_filter(
        [
            "cloud_service_type_id",
            "name",
            "provider",
            "group",
            "cloud_service_type_key",
            "service_code",
            "is_primary",
            "is_major",
            "resource_type",
            "workspace_id",
            "domain_id",
        ]
    )
    @append_keyword_filter(_KEYWORD_FILTER)
    def list(self, params: dict) -> Tuple[QuerySet, int]:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'cloud_service_type_id': 'str',
                'name': 'str',
                'group': 'str',
                'provider': 'str',
                'cloud_service_type_key': 'str',
                'service_code': 'str',
                'is_primary': 'str',
                'is_major': 'str',
                'resource_type': 'str',
                'workspace_id': 'str',              # injected from auth
                'domain_id': 'str',                 # injected from auth (required)
            }

        Returns:
            results (list)
            total_count (int)

        """

        return self.asset_type_mgr.list_asset_types(params.get("query", {}))

    @transaction(
        permission="inventory:AssetType.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["query", "domain_id"])
    @append_query_filter(["workspace_id", "domain_id"])
    @append_keyword_filter(_KEYWORD_FILTER)
    def stat(self, params: dict) -> dict:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'workspace_id': 'str',              # injected from auth
                'domain_id': 'str',                 # injected from auth (required)
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.asset_type_mgr.stat_asset_types(query)
