from re import U
from typing import Dict, List, Literal, Union
from unicodedata import category

from pydantic import BaseModel
from spaceone.inventory_v2.model import namespace_group

__all__ = [
    "NamespaceGroupCreateRequest",
    "NamespaceGroupUpdateRequest",
    "NamespaceGroupDeleteRequest",
    "NamespaceGroupGetRequest",
    "NamespaceGroupSearchQueryRequest",
    "NamespaceGroupStatQueryRequest",
]

ResourceGroup = Literal["DOMAIN", "WORKSPACE"]

class NamespaceGroupCreateRequest(BaseModel):
    namespace_group_id: Union[str, None] = None
    name: str
    icon: str
    description: Union[str, None] = None
    tags: Union[dict, None] = {}
    resource_group: ResourceGroup
    workspace_id: Union[str,None] = None
    domain_id:str


class NamespaceGroupUpdateRequest(BaseModel):
    namespace_group_id: str
    name: Union[str, None] = None
    icon: Union[str, None] = None
    description: Union[str, None] = None
    tags: Union[dict, None] = None
    workspace_id: Union[str,None] = None
    domain_id:str


class NamespaceGroupDeleteRequest(BaseModel):
    namespace_group_id: str
    workspace_id: Union[str,None] = None
    domain_id:str


class NamespaceGroupGetRequest(BaseModel):
    namespace_group_id: str
    workspace_id: Union[str,None] = None
    domain_id:str



class NamespaceGroupSearchQueryRequest(BaseModel):
    query: Union[dict, None] = None
    namespace_group_id: Union[str, None] = None
    exists_only: Union[bool, None] = None
    workspace_id:Union[list,str,None] = None
    domain_id:str


class NamespaceGroupStatQueryRequest(BaseModel):
    query: dict
    workspace_id:Union[list,str,None] = None
    domain_id: str