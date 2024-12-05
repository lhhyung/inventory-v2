from typing import Union, Literal, List
from pydantic import BaseModel

__all__ = [
    "AsseTypeCreateRequest",
    "AsseTypeUpdateRequest",
    "AssetTypeAddAssetGroupRequest",
    "AssetTypeRemoveAssetGroupRequest",
    "AssetTypeDeleteRequest",
    "AssetTypeGetRequest",
    "AssetTypeSearchQueryRequest",
]

ResourceGroup = Literal["DOMAIN", "WORKSPACE"]


class AsseTypeCreateRequest(BaseModel):
    asset_type_id: Union[str, None]
    name: str
    description: Union[str, None]
    icon: Union[str, None]
    provider: str
    metadata: Union[dict, None]
    tags: Union[dict, None]
    asset_groups: Union[List[str], str]
    resource_group: ResourceGroup
    workspace_id: Union[str, None]
    domain_id: str


class AsseTypeUpdateRequest(BaseModel):
    name: Union[str, None]
    description: Union[str, None]
    icon: Union[str, None]
    provider: str
    metadata: Union[dict, None]
    tags: Union[dict, None]
    workspace_id: Union[str, None]
    domain_id: str


class AssetTypeAddAssetGroupRequest(BaseModel):
    pass


class AssetTypeRemoveAssetGroupRequest(BaseModel):
    pass


class AssetTypeDeleteRequest(BaseModel):
    asset_type_id: str


class AssetTypeGetRequest(BaseModel):
    asset_type_id: str
    workspace_id: Union[str, None]
    domain_id: str


class AssetTypeSearchQueryRequest(BaseModel):
    query: Union[dict, None] = None
    exists_only: Union[bool, None] = None
    users_projects: Union[List[str], None] = None
    workspace_id: Union[str, None] = None
    domain_id: str
