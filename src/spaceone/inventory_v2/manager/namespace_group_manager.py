import logging
from operator import is_
from re import U
from typing import Tuple, List, Optional, Union

from fastapi.background import P
from mongoengine import QuerySet
from spaceone.core import utils, cache


from spaceone.core.manager import BaseManager
from spaceone.inventory_v2.error.error_namespace_group import *
from spaceone.inventory_v2.manager.namespace_manager import NamespaceManager
from spaceone.inventory_v2.model.namespace_group.database import NamespaceGroup
from spaceone.inventory_v2.model.namespace.database import Namespace
from spaceone.inventory_v2.model.namespace.response import NamespaceResponse
from spaceone.inventory_v2.manager.managed_resource_manager import ManagedResourceManager

_LOGGER = logging.getLogger(__name__)


class NamespaceGroupManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namespace_group_model = NamespaceGroup
        self.namespace_model = Namespace

    def create_namespace_group(self, params: dict) -> NamespaceGroup:
        def _rollback(vo: NamespaceGroup):
            _LOGGER.info(
                f"[ROLLBACK] Delete namespace_group : {vo.name} ({vo.namespace_group_id})"
            )
            vo.delete()

        if params.get("namespace_group_id") is None : 
            params["namespace_group_id"] = utils.generate_id("nsg")

        if "is_managed" not in params:
            params["is_managed"] = False

        namespace_group_vo= self.namespace_group_model.create(params)
        self.transaction.add_rollback(_rollback, namespace_group_vo)

        return namespace_group_vo

    def update_namespace_group_by_vo(
        self, 
        params: dict, 
        namespace_group_vo: NamespaceGroup
    ) -> NamespaceGroup:
        def _rollback(old_data):
            _LOGGER.info(
                f'[ROLLBACK] Revert Data : {old_data["name"]} ({old_data["namespace_group_id"]})'
            )
            namespace_group_vo.update(old_data)

        self.transaction.add_rollback(_rollback, namespace_group_vo.to_dict())
        return namespace_group_vo.update(params)

    # @staticmethod
    def delete_namespace_group_by_vo(
        self, 
        namespace_group_vo: NamespaceGroup
    ) -> None:
        
        namespace_mgr = NamespaceManager()
        namespace_vos = namespace_mgr.filter_namespaces(
            namespace_group_id=namespace_group_vo.namespace_group_id,
            domain_id = namespace_group_vo.domain_id,
        )
        
        for namespace_vo in namespace_vos:
            raise ERROR_RELATED_NAMESPACE_EXIST(namespace_id=namespace_vo.namespace_id)

        namespace_group_vo.delete()
    
    def get_namespace_group(
        self, 
        namespace_group_id: str,
        domain_id: str,
        workspace_id: Union[list, str, None] = None,

    ) -> NamespaceGroup:
        conditions:dict = {
            "namespace_group_id": namespace_group_id,
            "domain_id": domain_id,
        }
        
        if workspace_id:
            conditions.update({"workspace_id": workspace_id})

        return self.namespace_group_model.get(**conditions)


    def filter_namespace_groups(self, **conditions) -> QuerySet:
        return self.namespace_group_model.filter(**conditions)

    def list_namespace_groups(self, query: dict, domain_id:str) -> Tuple[QuerySet, int]:
        self.create_managed_namespace_group(domain_id)
        return self.namespace_group_model.query(**query)

    def stat_namespace_groups(self, query: dict) -> dict:
        result = self.namespace_group_model.stat(**query)
        return result if result is not None else {}


    # @cache.cacheable(key="inventory-v2:managed-namespace_group:{domain_id}:sync", expire=300)
    def create_managed_namespace_group(self, domain_id:str) -> bool:
        managed_resource_mgr = ManagedResourceManager()

        namespace_groups_vo = self.filter_namespace_groups(
            domain_id=domain_id,
            is_managed=True,
        )
        installed_namespace_groups_version_map = {}
        
        for namespace_group_vo in namespace_groups_vo:
            installed_namespace_groups_version_map[
                namespace_group_vo.namespace_group_id
            ] = namespace_group_vo.version

        
        managed_namespace_groups = managed_resource_mgr.get_managed_namespace_groups()
        
        for managed_nsg_id, managed_nsg_info in managed_namespace_groups.items():
            managed_nsg_info["domain_id"] = domain_id
            managed_nsg_info["is_managed"] = True
            managed_nsg_info["resource_group"] = "DOMAIN"
            managed_nsg_info["workspace_id"] = "*"

            if ns_version := installed_namespace_groups_version_map.get(managed_nsg_id):
                if ns_version != managed_nsg_info["version"]:
                    _LOGGER.debug(
                        f"[_create_managed_namespace_group] update managed namespace: {managed_nsg_id}"
                    )
                    namespace_group_vo = self.get_namespace_group(managed_nsg_id, domain_id)
                    self.update_namespace_group_by_vo(managed_nsg_info, namespace_group_vo)
            else:
                _LOGGER.debug(
                    f"[_create_managed_namespace_group] create new managed namespace: {managed_nsg_id}"
                )
                self.create_namespace_group(managed_nsg_info)

        return True
    
    
    # def get_namespaces_in_namespace_group(
    #     self, 
    #     namespace_group_id: str,
    # ) -> NamespaceResponse:
        
    #     namespace_vos = self.namespace_model.filter(
    #         namespace_group_id=namespace_group_id
    #     )
    #     namespaces = [namespace_vo.namespace_id for namespace_vo in namespace_vos]

    #     child_namespace_groups = self.namespace_group_model.filter(
    #         parent_group_id=namespace_group_id
    #     )
    #     for child_namespace_group in child_namespace_groups:
    #         parent_group_id = child_namespace_group.namespace_group_id
    #         namespaces.extend(
    #             self.get_namespaces_in_namespace_group(parent_group_id)
    #         )
    #     return list(set(namespaces))
