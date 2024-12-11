from typing import Union, Literal, List
from pydantic import BaseModel

__all__ = [
    "AssetCreateRequest",
    "AssetUpdateRequest",
    "AssetGetRequest",
    "AssetSearchQueryRequest",
    "AssetHistorySearchQueryRequest",
]

Action = Literal["CREATE", "UPDATE", "DELETE"]


class AssetCreateRequest(BaseModel):
    asset_id: Union[str, None]
    name: Union[str, None]
    provider: str
    asset_type: str
    ipaddresses: Union[List[str], None]
    account: Union[str, None]
    data: dict
    metadata: Union[dict, None]
    tags: Union[dict, None]
    region_id: Union[str, None]
    service_account_id: Union[str, None]
    project_id: str
    workspace_id: str
    domain_id: str
    users_projects: Union[List[str], None]


class AssetUpdateRequest(BaseModel):
    asset_id: str
    name: Union[str, None]
    account: Union[str, None]
    instance_type: Union[str, None]
    instance_size: Union[float, None]
    ip_addresses: Union[List[str], None]
    data: dict
    metadata: Union[dict, None]
    tags: Union[dict, None]
    region: Union[str, None]
    user_projects: Union[List[str], None]
    project_id: Union[str, None]
    workspace_id: str
    domain_id: str


class AssetGetRequest(BaseModel):
    asset_id: str
    user_projects: List[str]
    workspace_id: str
    domain_id: str


class AssetSearchQueryRequest(BaseModel):
    query: Union[dict, None] = None
    user_projects: Union[List[str], None] = None
    workspace_id: Union[str, None] = None
    domain_id: str


class AssetHistorySearchQueryRequest(BaseModel):
    query: Union[dict, None] = None
    history_id: Union[str, None] = None
    asset_id: str
    action: Union[Action, None] = None
    user_id: Union[str, None] = None
    collector_id: Union[str, None] = None
    job_id: Union[str, None] = None
    workspace_id: Union[str, None] = None
    domain_id: str
    user_projects: Union[List[str], None] = None
