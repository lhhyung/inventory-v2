import logging
import copy
import pytz
from datetime import datetime
from typing import List, Union, Tuple

from spaceone.core.service import *
from spaceone.core import utils

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

_KEYWORD_FILTER = [
    "asset_id",
    "name",
    "ip_addresses",
    "cloud_service_group",
    "cloud_service_type",
    "reference.resource_id",
]

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class AssetService(BaseService):
    resource = "AssetType"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asset_mgr = AssetManager()
        self.collector_rule_mgr = CollectorRuleManager()
        self.state_mgr = CollectionStateManager()

        self.identity_mgr = IdentityManager()
        self.collector_id = self.transaction.get_meta("collector_id")
        self.job_id = self.transaction.get_meta("job_id")
        self.plugin_id = self.transaction.get_meta("plugin_id")
        self.service_account_id = self.transaction.get_meta("secret.service_account_id")

    @transaction(
        permission="inventory:CloudService.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @convert_model
    def create(self, params: AssetCreateRequest) -> Union[AssetResponse, dict]:
        """
        Args:
            params (dict): {
                'cloud_service_type': 'str',        # required
                'cloud_service_group': 'str',       # required
                'provider': 'str',                  # required
                'name': 'str',
                'account': 'str',
                'instance_type': 'str',
                'instance_size': 'float',
                'ip_addresses': 'list',
                'data': 'dict',                     # required
                'json_data': 'dict',
                'metadata': 'dict',
                'reference': 'dict',
                'tags': 'list or dict',
                'region_code': 'str',
                'project_id': 'str',                # required
                'workspace_id': 'str',              # injected from auth (required)
                'domain_id': 'str'                  # injected from auth (required)
            }

        Returns:
            cloud_service_vo (object)

        """
        # check if asset type is last
        asset_vo = self.create_resource(params.dict())
        return AssetResponse(**asset_vo.to_dict())

    def create_resource(self, params: dict) -> Asset:
        # ch_mgr: ChangeHistoryManager = self.locator.get_manager("ChangeHistoryManager")

        if json_data := params.get("json_data"):
            params["data"] = utils.load_json(json_data)
            if not isinstance(params["data"], dict):
                raise ERROR_INVALID_PARAMETER_TYPE(
                    key="json_data", type=type(params["data"])
                )

            del params["json_data"]
        elif "data" not in params:
            raise ERROR_REQUIRED_PARAMETER(key="data")

        if json_metadata := params.get("json_metadata"):
            params["metadata"] = utils.load_json(json_metadata)
            if not isinstance(params["metadata"], dict):
                raise ERROR_INVALID_PARAMETER_TYPE(
                    key="json_metadata", type=type(params["metadata"])
                )

            del params["json_metadata"]

        domain_id = params["domain_id"]
        workspace_id = params["workspace_id"]
        secret_project_id = self.transaction.get_meta("secret.project_id")
        provider = params["provider"]

        if instance_size := params.get("instance_size"):
            if not isinstance(instance_size, float):
                raise ERROR_INVALID_PARAMETER_TYPE(key="instance_size", type="float")

        if "tags" in params:
            params["tags"] = self._convert_tags_to_dict(params["tags"])

        # Change data through Collector Rule
        if self._is_created_by_collector():
            params = self.collector_rule_mgr.change_asset_data(
                self.collector_id, domain_id, params
            )

        if "tags" in params:
            params["tags"], params["tag_keys"] = self._convert_tags_to_hash(
                params["tags"], provider
            )

        if "project_id" in params:
            self.identity_mgr.get_project(params["project_id"], domain_id)
        elif secret_project_id:
            params["project_id"] = secret_project_id

        # params["ref_cloud_service_type"] = self._make_cloud_service_type_key(params)

        if "region_id" in params:
            params["ref_region"] = self._make_region_key(
                domain_id, provider, params["region_code"]
            )

        if "metadata" in params:
            params["metadata"] = self._convert_metadata(params["metadata"], provider)

        params["collection_info"] = self._get_collection_info()

        asset_vo = self.asset_mgr.create_asset(params)

        # todo: Create New History
        # Create New History
        # ch_mgr.add_new_history(asset_vo, params)

        # Create Collection State
        self.state_mgr.create_collection_state(asset_vo.asset_id, domain_id)

        return asset_vo

    @transaction(
        permission="inventory-v2:CloudService.write",
        role_types=["WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @convert_model
    def update(self, params: AssetUpdateRequest) -> Union[AssetResponse, dict]:
        """
        Args:
            params (dict): {
                'asset_id': 'str',      # required
                'name': 'str',
                'account': 'str',
                'instance_type': 'str',
                'instance_size': 'float',
                'ip_addresses': 'list',
                'data': 'dict',
                'json_data': 'dict',
                'metadata': 'dict',
                # 'reference': 'dict',
                'tags': 'list or dict',
                'region_code': 'str',
                'project_id': 'str',
                'workspace_id': 'str',              # injected from auth (required)
                'domain_id': 'str',                 # injected from auth (required)
                'user_projects': 'list'             # injected from auth
            }

        Returns:
            cloud_service_vo (object)
        """
        # check if asset type is last
        asset_vo = self.update_resource(params.dict())
        return AssetResponse(**asset_vo.to_dict())

    @check_required(["asset_id", "workspace_id", "domain_id"])
    def update_resource(self, params: dict) -> Asset:
        # ch_mgr: ChangeHistoryManager = self.locator.get_manager("ChangeHistoryManager")

        if json_data := params.get("json_data"):
            params["data"] = utils.load_json(json_data)
            if not isinstance(params["data"], dict):
                raise ERROR_INVALID_PARAMETER_TYPE(
                    key="json_data", type=type(params["data"])
                )

            del params["json_data"]

        if json_metadata := params.get("json_metadata"):
            params["metadata"] = utils.load_json(json_metadata)
            if not isinstance(params["metadata"], dict):
                raise ERROR_INVALID_PARAMETER_TYPE(
                    key="json_metadata", type=type(params["metadata"])
                )

            del params["json_metadata"]

        secret_project_id = self.transaction.get_meta("secret.project_id")

        asset_id = params["asset_id"]
        workspace_id = params["workspace_id"]
        user_projects = params.get("user_projects")
        domain_id = params["domain_id"]
        provider = self._get_provider_from_meta()

        if "ip_addresses" in params and params["ip_addresses"] is None:
            del params["ip_addresses"]

        if instance_size := params.get("instance_size"):
            if not isinstance(instance_size, float):
                raise ERROR_INVALID_PARAMETER_TYPE(key="instance_size", type="float")

        if "tags" in params:
            params["tags"] = self._convert_tags_to_dict(params["tags"])

        # Change data through Collector Rule
        if self._is_created_by_collector():
            params = self.collector_rule_mgr.change_asset_data(
                self.collector_id, domain_id, params
            )

        asset_vo: Asset = self.asset_mgr.get_asset(
            asset_id, domain_id, workspace_id, user_projects
        )

        if "project_id" in params:
            self.identity_mgr.get_project(params["project_id"], domain_id)
        elif secret_project_id and secret_project_id != asset_vo.project_id:
            params["project_id"] = secret_project_id

        if "region_code" in params:
            params["ref_region"] = self._make_region_key(
                asset_vo.domain_id,
                asset_vo.provider,
                params["region_code"],
            )

        old_asset_data = dict(asset_vo.to_dict())

        if "tags" in params:
            old_tags = old_asset_data.get("tags", {})
            old_tag_keys = old_asset_data.get("tag_keys", {})
            new_tags, new_tag_keys = self._convert_tags_to_hash(
                params["tags"], provider
            )

            if self._is_different_data(new_tags, old_tags, provider):
                old_tags.update(new_tags)
                old_tag_keys.update(new_tag_keys)
                params["tags"] = old_tags
                params["tag_keys"] = old_tag_keys
            else:
                del params["tags"]

        if "metadata" in params:
            old_metadata = old_asset_data.get("metadata", {})
            new_metadata = self._convert_metadata(params["metadata"], provider)

            if self._is_different_data(new_metadata, old_metadata, provider):
                old_metadata.update(new_metadata)
                params["metadata"] = old_metadata
            else:
                del params["metadata"]

        params["collection_info"] = self._get_collection_info()

        params = self.asset_mgr.merge_data(params, old_asset_data)

        asset_vo = self.asset_mgr.update_asset_by_vo(params, asset_vo)

        # todo: Create Update History
        # Create Update History
        # ch_mgr.add_update_history(asset_vo, params, old_asset_data)

        # Update Collection History
        state_vo = self.state_mgr.get_collection_state(asset_id, domain_id)
        if state_vo:
            self.state_mgr.reset_collection_state(state_vo)
        else:
            self.state_mgr.create_collection_state(asset_id, domain_id)

        return asset_vo

    @transaction(
        permission="inventory-v2:Asset.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @convert_model
    def get(self, params: AssetGetRequest) -> Union[AssetResponse, dict]:
        """
        Args:
            params (dict): {
                    'asset_id': 'str',      # required
                    'user_projects': 'list'         # injected from auth
                    'workspace_id': 'str',          # injected from auth
                    'domain_id': 'str',             # injected from auth (required)
                }

        Returns:
            cloud_service_vo (object)

        """

        asset_vo = self.asset_mgr.get_asset(
            params.asset_id, params.domain_id, params.workspace_id, params.user_projects
        )
        return AssetResponse(**asset_vo.to_dict())

    @transaction(
        permission="inventory-v2:Asset.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @append_query_filter(
        [
            "asset_id",
            "name",
            "state",
            "ip_address",
            "account",
            "instance_type",
            "asset_type_id",
            "cloud_service_group",
            "provider",
            "region_code",
            "project_id",
            "project_group_id",
            "workspace_id",
            "domain_id",
            "user_projects",
        ]
    )
    @append_keyword_filter(_KEYWORD_FILTER)
    @set_query_page_limit(1000)
    @convert_model
    def list(self, params: AssetSearchQueryRequest):
        """
        Args:
            params (dict): {
                    'query': 'dict (spaceone.api.core.v1.Query)',
                    'asset_id': 'str',
                    'name': 'str',
                    'state': 'str',
                    'ip_address': 'str',
                    'account': 'str',
                    'instance_type': 'str',
                    'cloud_service_type': 'str',
                    'cloud_service_group': 'str',
                    'provider': 'str',
                    'region_code': 'str',
                    'project_id': 'str',
                    'project_group_id': 'str',
                    'workspace_id': 'str',          # injected from auth
                    'domain_id': 'str',             # injected from auth (required)
                    'user_projects': 'list',        # injected from auth
                }

        Returns:
            results (list)
            total_count (int)
        """

        domain_id = params.domain_id
        workspace_id = params.workspace_id
        query = params.query or {}
        reference_filter = {"domain_id": domain_id, "workspace_id": workspace_id}

        return self.asset_mgr.list_assets(
            query,
            change_filter=True,
            domain_id=domain_id,
            reference_filter=reference_filter,
        )

    @staticmethod
    def _make_cloud_service_type_key(resource_data: dict) -> str:
        return (
            f'{resource_data["domain_id"]}.{resource_data["workspace_id"]}.{resource_data["provider"]}.'
            f'{resource_data["cloud_service_group"]}.{resource_data["cloud_service_type"]}'
        )

    @staticmethod
    def _make_region_key(domain_id: str, provider: str, region_code: str) -> str:
        return f"{domain_id}.{provider}.{region_code}"

    @staticmethod
    def _convert_metadata(metadata: dict, provider: str) -> dict:
        return {provider: copy.deepcopy(metadata)}

    def _get_collection_info(self) -> dict:
        collector_id = self.transaction.get_meta("collector_id")
        secret_id = self.transaction.get_meta("secret.secret_id")
        service_account_id = self.transaction.get_meta("secret.service_account_id")

        return {
            "collector_id": collector_id,
            "secret_id": secret_id,
            "service_account_id": service_account_id,
            "last_collected_at": datetime.utcnow(),
        }

    @staticmethod
    def _convert_tags_to_dict(tags: Union[list, dict]) -> dict:
        if isinstance(tags, list):
            dot_tags = utils.tags_to_dict(tags)
        elif isinstance(tags, dict):
            dot_tags = copy.deepcopy(tags)
        else:
            dot_tags = {}

        return dot_tags

    @staticmethod
    def _convert_tags_to_hash(dot_tags: dict, provider: str) -> Tuple[dict, dict]:
        tag_keys = {provider: list(dot_tags.keys())}

        tags = {provider: {}}
        for key, value in dot_tags.items():
            hashed_key = utils.string_to_hash(key)
            tags[provider][hashed_key] = {"key": key, "value": value}

        return tags, tag_keys

    @staticmethod
    def _is_different_data(new_data: dict, old_data: dict, provider: str) -> bool:
        if new_data[provider] != old_data.get(provider):
            return True
        else:
            return False

    def _get_provider_from_meta(self) -> str:
        if self._is_created_by_collector():
            return self.transaction.get_meta("secret.provider")
        else:
            return "custom"

    def _is_created_by_collector(self) -> str:
        return (
            self.collector_id
            and self.job_id
            and self.service_account_id
            and self.plugin_id
        )

    @staticmethod
    def _check_timezone(timezone: str) -> None:
        if timezone not in pytz.all_timezones:
            raise ERROR_INVALID_PARAMETER(key="timezone", reason="Timezone is invalid.")
