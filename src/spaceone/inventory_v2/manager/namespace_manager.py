import logging
from typing import Tuple,List, Optional, Union
from anyio import Condition
from mongoengine import QuerySet
from spaceone.core import utils, cache

from spaceone.core.manager import BaseManager
from spaceone.inventory_v2.error.error_namespace import *
from spaceone.inventory_v2.model.namespace.database import Namespace

_LOGGER = logging.getLogger(__name__)


class NamespaceManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.namespace_model = Namespace
        
    
    def create_namespace(self, params:dict) -> Namespace:
        def _rollback(vo: Namespace):
            _LOGGER.info(f"[ROLLBACK] Delete namespace : {vo.name} ({vo.namespace_id}) ({vo.namespace_group_id})")
            vo.delete()
        
        if namespace_id := params.get("namespace_id"):
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

    def list_namespaces(self, query: dict) -> Tuple[QuerySet, int]:
        return self.namespace_model.query(**query)
    
    def stat_namespaces(self, query: dict) -> dict:
        return self.namespace_model.stat(**query)
    
    
    
