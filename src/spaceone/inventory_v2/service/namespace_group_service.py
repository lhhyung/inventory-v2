import logging
from typing import Union

from spaceone.core.service import *
from spaceone.core.service.utils import *
from spaceone.core.error import *

from spaceone.inventory_v2.manager.identity_manager import IdentityManager
from spaceone.inventory_v2.manager.namespace_group_manager import NamespaceGroupManager
from spaceone.inventory_v2.manager.namespace_manager import NamespaceManager
from spaceone.inventory_v2.model.namespace_group.request import * 
from spaceone.inventory_v2.model.namespace_group.response import *

from spaceone.inventory_v2.error.error_namespace_group import *

_LOGGER = logging.getLogger(__name__)
_KEYWORD_FILTER = ["namepspace_group_id", "name"]

@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class NamespaceGroupService(BaseService):
    resource = "NamespaceGroup"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namespace_group_mgr = NamespaceGroupManager()
        self.namespace_mgr = NamespaceManager()
        self.identity_mgr = IdentityManager()

    @transaction(
        permission="inventory-v2:NamespaceGroup.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def create(self, params: NamespaceGroupCreateRequest) -> Union[NamespaceGroupResponse, dict]:
        """Create namespace Group

        Args:
            params (dict): {
                'namespace_group_id': 'str',
                'name': 'str',                  # required
                'icon': 'str',                  # required
                'description': 'str',
                'tags': 'dict',
                'resource_group': 'str',        # required
                'workspace_id': 'str',          # injected from auth
                'domain_id': 'str',             # injected from auth (required)
            }

        Returns:
            NamespaceGroupResponse:
        """

        domain_id = params.domain_id
        workspace_id = params.workspace_id
        resource_group = params.resource_group

        # Check permission by resource group
        if resource_group == "WORKSPACE":
            if workspace_id is None:
                raise ERROR_REQUIRED_PARAMETER(key="workspace_id")

            self.identity_mgr.check_workspace(workspace_id, domain_id)
        else:
            params.workspace_id = "*"

        namespace_group_vo = self.namespace_group_mgr.create_namespace_group(params.dict())
        return NamespaceGroupResponse(**namespace_group_vo.to_dict())

    @transaction(
        permission="inventory-v2:NamespaceGroup.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def update(self, params: NamespaceGroupUpdateRequest) -> Union[NamespaceGroupResponse, dict]:
        """Update namespace Group

        Args:
            params (dict): {
                'namespace_group_id': 'str',    # required
                'name': 'str',                  
                'icon': 'str',
                'description': 'str',
                'tags': 'dict',
                'workspace_id': 'str',          # injected from auth
                'domain_id': 'str',             # injected from auth (required)
            }

        Returns:
            NamespaceGroupResponse:
        """

        namespace_group_vo = self.namespace_group_mgr.get_namespace_group(
            params.namespace_group_id,
            params.domain_id,
            workspace_id=params.workspace_id,
        )

        if namespace_group_vo.is_managed:
            raise ERROR_PERMISSION_DENIED()

        namespace_group_vo = self.namespace_group_mgr.update_namespace_group_by_vo(
            params.dict(exclude_unset=True), namespace_group_vo
        )

        return NamespaceGroupResponse(**namespace_group_vo.to_dict())

    @transaction(
        permission="inventory-v2:NamespaceGroup.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def delete(self, params: NamespaceGroupDeleteRequest) -> None:
        """Delete namespace Group

        Args:
            params (dict): {
                'namespace_group_id': 'str',    # required
                'workspace_id': 'str',          # injected from auth
                'domain_id': 'str',             # injected from auth (required)
            }

        Returns:
            None
        """

        namespace_group_vo = self.namespace_group_mgr.get_namespace_group(
            namespace_group_id=params.namespace_group_id,
            domain_id=params.domain_id,
            workspace_id=params.workspace_id,
        )

        if namespace_group_vo.is_managed:
            raise ERROR_PERMISSION_DENIED()

        self.namespace_group_mgr.delete_namespace_group_by_vo(namespace_group_vo=namespace_group_vo)

    @transaction(
        permission="inventory-v2:NamespaceGroup.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id","*")
    @convert_model
    def get(self, params: NamespaceGroupGetRequest) -> Union[NamespaceGroupResponse, dict]:
        """Get namespace Group

        Args:
            params (dict): {
                'namespace_group_id': 'str',    # required
                'workspace_id': 'str',          # injected from auth
                'domain_id': 'str',             # injected from auth (required)
            }

        Returns:
            NamespaceGroupResponse:
        """



        namespace_vo = self.namespace_group_mgr.get_namespace_group(
            namespace_group_id=params.namespace_group_id,
            domain_id=params.domain_id,
            workspace_id = params.workspace_id,
        )

        

        return NamespaceGroupResponse(**namespace_vo.to_dict())


    @transaction(
        permission="inventory-v2:NamespaceGroup.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id","*")
    @append_query_filter(
        [
            "namespace_group_id",
            "workspace_id",
            "domain_id",
        ]
    )
    @append_keyword_filter(["namespace_group_id", "name"])
    @convert_model
    def list(
        self, params: NamespaceGroupSearchQueryRequest
    ) -> Union[NamespaceGroupsResponse, dict]:
        """List namespaces group

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'namespace_group_id': 'str',
                'exists_only': 'bool',
                'workspace_id': 'str',          # injected from auth
                'domain_id': 'str',             # injected from auth (required)
            }

        Returns:
            NamespacesGroupResponse:
        """
        

        query = params.query or {}
        namespace_group_vos, total_count = self.namespace_group_mgr.list_namespace_groups(
            query, params.domain_id
        )

        namespaces_group_info = [namespace_group_vo.to_dict() for namespace_group_vo in namespace_group_vos]
        return NamespaceGroupsResponse(results=namespaces_group_info, total_count=total_count)

    @transaction(
        permission="inventory-v2:NamespaceGroup.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @append_query_filter(["domain_id"])
    @append_keyword_filter(["namespace_group_id", "name"])
    @convert_model
    def stat(self, params: NamespaceGroupStatQueryRequest) -> dict:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)', # required
                'workspace_id': 'list',     # injected from auth
                'domain_id': 'str',         # injected from auth (required)
            }

        Returns:
            dict: {
                'results': 'list',
                'total_count': 'int'
            }
        """

        query = params.query or {}
        return self.namespace_group_mgr.stat_namespace_groups(query)