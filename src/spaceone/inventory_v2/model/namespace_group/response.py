from datetime import datetime
from typing import Union, List
from pydantic import BaseModel
from spaceone.core import utils

from spaceone.inventory_v2.model.namespace_group.request import ResourceGroup

__all__ = ["NamespaceGroupResponse", "NamespaceGroupsResponse"]


class NamespaceGroupResponse(BaseModel):
    namespace_group_id: Union[str, None] = None
    name: Union[str, None] = None
    icon: Union[str, None] = None
    description: Union[str, None] = None
    tags: Union[dict, None] = None
    resource_group: Union[ResourceGroup, None] = None
    is_managed: Union[bool, None] = None
    workspace_id: Union[str, None] = None
    domain_id: Union[str, None] = None
    created_at: Union[datetime, None] = None
    updated_at: Union[datetime, None] = None

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["created_at"] = utils.datetime_to_iso8601(data["created_at"])
        data["updated_at"] = utils.datetime_to_iso8601(data["updated_at"])
        return data


class NamespaceGroupsResponse(BaseModel):
    results: List[NamespaceGroupResponse] = []
    total_count: int
