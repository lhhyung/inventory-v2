from typing import Dict, List, Literal, Union
from unicodedata import category

from pydantic import BaseModel
from spaceone.inventory_v2.model import namespace_group

__all__ = [
    "NamespaceCreateRequest",
    "NamespaceUpdateRequest",
    "NamespaceDeleteRequest",
    "NamespaceGetRequest",
    "NamespaceSearchQueryRequest",
    "NamespaceStatQueryRequest",
    "ResourceGroup",
]


ResourceGroup = Literal["DOMAIN", "WORKSPACE"]

class NamespaceCreateRequest(BaseModel):
    namespace_id: Union[str, None] = None
    name: str
    category: str
    icon: Union[str, None] = None
    tags: Union[Dict, None] = None
    resource_group: ResourceGroup
    namespace_group_id: str
    workspace_id: Union[str,None] = None
    domain_id: str


class NamespaceUpdateRequest(BaseModel):
    namespace_id: str
    name: Union[str, None] = None
    icon: Union[str, None] = None
    tags: Union[Dict, None] = None
    workspace_id: Union[list,str,None] = None
    domain_id: str
    

class NamespaceDeleteRequest(BaseModel):
    namespace_id: str
    workspace_id:Union[list,str,None] = None
    domain_id: str


class NamespaceGetRequest(BaseModel):
    namespace_id: str
    workspace_id:Union[list,str,None] = None
    domain_id: str



class NamespaceSearchQueryRequest(BaseModel):
    query: Union[dict, None] = None
    namespace_id: Union[str, None] = None
    workspace_id:Union[list,str,None] = None
    domain_id: str


class NamespaceStatQueryRequest(BaseModel):
    query: dict
    workspace_id:Union[list,str,None] = None
    domain_id: str