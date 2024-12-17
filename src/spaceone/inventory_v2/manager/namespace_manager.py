import logging
from typing import Tuple,List, Optional, Union
from anyio import Condition
from mongoengine import QuerySet
from spaceone.core import utils, cache

from spaceone.core.manager import BaseManager
from spaceone.inventory_v2.error.error_namespace import *
from spaceone.inventory_v2.model import namespace_group
from spaceone.inventory_v2.model.namespace.database import Namespace
from spaceone.inventory_v2.manager.managed_resource_manager import ManagedResourceManager

_LOGGER = logging.getLogger(__name__)


class NamespaceManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namespace_model = Namespace
        
    
    def create_namespace(self, params:dict) -> Namespace:
        def _rollback(vo: Namespace):
            _LOGGER.info(f"[ROLLBACK] Delete namespace : {vo.name} ({vo.namespace_id}) ({vo.namespace_group_id})")
            vo.delete()

        if params.get("namespace_id") is None :
            params["namespace_id"] = utils.generate_id("ns")

        namespace_vo: Namespace = self.namespace_model.create(params)
        self.transaction.add_rollback(_rollback, namespace_vo)
        
        return namespace_vo
    
    def update_namespace_by_vo(
        self, 
        params: dict, 
        namespace_vo: Namespace
    ) -> Namespace:
        def _rollback(old_data):
            _LOGGER.info(f'[ROLLBACK] Revert Data : {old_data["name"]} ({old_data["namespace_id"]}) ({old_data["namespace_group_id"]})')
            
            namespace_vo.update(old_data)
        
        self.transaction.add_rollback(_rollback, namespace_vo.to_dict())
        
        return namespace_vo.update(params)  
    
    def delete_namespace_by_vo(
        self, 
        namespace_vo: Namespace
    ) -> None:
        namespace_vo.delete()
        
    def get_namespace(
        self, 
        namespace_id: str,
        domain_id: str,
        workspace_id: Union[list, str, None] = None,
    ) -> Namespace:

        conditions: dict = {
            "namespace_id": namespace_id,
            "domain_id": domain_id
        }
        
        if workspace_id:
            conditions.update({"workspace_id": workspace_id})
            
        return self.namespace_model.get(**conditions)
    
    def filter_namespaces(self, **conditions) -> QuerySet:
        return self.namespace_model.filter(**conditions)    

    def list_namespaces(self, query: dict, domain_id: str) -> Tuple[QuerySet, int]:
        # self.create_managed_namespace(domain_id)
        return self.namespace_model.query(**query)
    
    def stat_namespaces(self, query: dict) -> dict:
        return self.namespace_model.stat(**query)
    
    @cache.cacheable(key="inventory-v2:managed-namespace:{domain_id}:sync", expire=300)
    def create_managed_namespace(self, domain_id:str) -> bool:
        managed_resource_mgr = ManagedResourceManager()
        
        namespace_vos = self.filter_namespaces(domain_id=domain_id, is_managed=True)
        
        installed_namespace_version_map = {}
        for namespace_vo in namespace_vos:
            installed_namespace_version_map[
                namespace_vo.namespace_id
            ] = namespace_vo.version

        managed_namespace_map = managed_resource_mgr.get_managed_namespaces()

        for managed_ns_id, managed_ns_info in managed_namespace_map.items():
            managed_ns_info["domain_id"] = domain_id
            managed_ns_info["is_managed"] = True
            managed_ns_info["resource_group"] = "DOMAIN"
            managed_ns_info["workspace_id"] = "*"

            if ns_version := installed_namespace_version_map.get(managed_ns_id):
                if ns_version != managed_ns_info["version"]:
                    _LOGGER.debug(
                        f"[_create_managed_namespace] update managed namespace: {managed_ns_id}"
                    )
                    namespace_vo = self.get_namespace(managed_ns_id, domain_id)
                    self.update_namespace_by_vo(managed_ns_info, namespace_vo)
            else:
                _LOGGER.debug(
                    f"[_create_managed_namespace] create new managed namespace: {managed_ns_id}"
                )
                self.create_namespace(managed_ns_info)

        return True

