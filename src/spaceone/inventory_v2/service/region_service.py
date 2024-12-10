import logging
from typing import Union

from spaceone.core.error import *
from spaceone.core.service import *

from spaceone.inventory_v2.manager.region_manager import RegionManager
from spaceone.inventory_v2.manager.identity_manager import IdentityManager
from spaceone.inventory_v2.model.region.request import *
from spaceone.inventory_v2.model.region.response import *
from spaceone.inventory_v2.model.region.database import Region

_LOGGER = logging.getLogger(__name__)
_KEYWORD_FILTER = ["region_id", "name", "region_code"]


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class RegionService(BaseService):
    resource = "Region"

    def __init__(self, metadata):
        super().__init__(metadata)
        self.region_mgr = RegionManager()

    @transaction(
        permission="inventory-v2:Region.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def create(self, params: RegionCreateRequest) -> Union[RegionResponse, dict]:
        """
        Args:
        params (dict): {
            'region_id': 'str,
            'name': 'str',              # required
            'region_code': 'str',       # required
            'provider': 'str',          # required
            'tags': 'dict',
            'resource_group': 'str',    # required
            'workspace_id': 'str',      # injected from auth
            'domain_id': 'str',         # injected from auth (required)
        }
        Returns:
            RegionResponse:
        """
        region_vo = self.create_resource(params.dict())

        # return self.create_resource(params)
        return RegionResponse(**region_vo.to_dict())

    def create_resource(self, params: dict) -> Region:

        identity_mgr = IdentityManager()

        domain_id = params["domain_id"]
        workspace_id = params.get("workspace_id")
        resource_group = params["resource_group"]

        # Check permission by resource group
        if resource_group == "WORKSPACE":
            if workspace_id is None:
                raise ERROR_REQUIRED_PARAMETER(key="workspace_id")

            identity_mgr.check_workspace(workspace_id, domain_id)
        else:
            params["workspace_id"] = "*"

        region_id = f'{params["provider"]}-{params["region_code"]}'

        params["region_id"] = region_id

        return self.region_mgr.create_region(params)

    @transaction(
        permission="inventory-v2:Region.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @convert_model
    def update(self, params: RegionUpdateRequest) -> Union[RegionResponse, dict]:
        """
        Args:
        params (dict): {
            'region_id': 'str',     # required
            'name': 'str',
            'tags': 'dict',
            'workspace_id': 'str',  # injected from auth
            'domain_id': 'str',     # injected from auth (required)
        }
        Returns:
            region_vo (object)
        """

        region_vo = self.update_resource(params.dict(exclude_unset=True))

        return RegionResponse(**region_vo.to_dict())

    def update_resource(self, params: dict) -> Region:

        region_vo = self.region_mgr.get_region(
            params["region_id"], params["domain_id"], params.get("workspace_id")
        )

        return self.region_mgr.update_region_by_vo(params, region_vo)

    @transaction(
        permission="inventory-v2:Region.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @convert_model
    def delete(self, params: RegionDeleteRequest) -> None:
        """
        Args:
        params (dict): {
            'region_id': 'str',     # required
            'workspace_id': 'str',  # injected from auth
            'domain_id': 'str'      # injected from auth (required)
        }
        Returns:
            None
        """

        self.delete_resource(params.dict())

    def delete_resource(self, params: dict) -> None:
        region_vo = self.region_mgr.get_region(
            params["region_id"], params["domain_id"], params.get("workspace_id")
        )
        self.region_mgr.delete_region_by_vo(region_vo)

    @transaction(
        permission="inventory-v2:Region.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @convert_model
    def get(self, params: RegionGetRequest) -> Union[RegionResponse, dict]:
        """
        Args:
            params (dict): {
                'region_id': 'str',     # required
                'workspace_id': 'str',  # injected from auth
                'domain_id': 'str',     # injected from auth (required)
            }

        Returns:
            region_vo (object)

        """

        region_vo = self.region_mgr.get_region(
            params.region_id, params.domain_id, params.workspace_id
        )

        return RegionResponse(**region_vo.to_dict())

    @transaction(
        permission="inventory-v2:Region.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @append_query_filter(
        [
            "region_id",
            "name",
            "region_code",
            "provider",
            "exists_only",
            "workspace_id",
            "domain_id",
        ]
    )
    @append_keyword_filter(_KEYWORD_FILTER)
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @convert_model
    def list(self, params: RegionSearchQueryRequest) -> Union[RegionsResponse, dict]:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'region_id': 'str',
                'name': 'str',
                'region_code': 'str',
                'provider': 'str',
                'exists_only': 'bool',
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str',         # injected from auth (required)
            }

        Returns:
            results (list)
            total_count (int)

        """

        query = params.query or {}
        region_vos, total_count = self.region_mgr.list_regions(query=query)

        regions_info = [region_vo.to_dict() for region_vo in region_vos]

        return RegionsResponse(results=regions_info, total_count=total_count)

    @transaction(
        permission="inventory-v2:Region.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @append_query_filter(["workspace_id", "domain_id"])
    @append_keyword_filter(_KEYWORD_FILTER)
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @convert_model
    def stat(self, params: RegionStatQueryRequest) -> dict:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',     # required
                'domain_id': 'str',     # injected from auth (required)
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.query or {}
        return self.region_mgr.stat_regions(query)
