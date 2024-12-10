from typing import Union, Literal, List
from pydantic import BaseModel

__all__ = [
    "CollectorCreateRequest",
    "CollectorUpdateRequest",
    "CollectorUpdatePluginRequest",
    "CollectorVerifyPluginRequest",
    "CollectorDeleteRequest",
    "CollectorGetRequest",
    "CollectorSearchQueryRequest",
    "CollectorStatQueryRequest",
    "CollectorCollectRequest",
]

ScheduleState = Literal["ENABLED", "DISABLED"]
ResourceGroup = Literal["DOMAIN", "WORKSPACE"]
UpgradeMode = Literal["AUTO", "MANUAL"]


class CollectorCreateRequest(BaseModel):
    name: str
    provider: Union[str, None] = None
    plugin_info: dict
    schedule: Union[dict, None] = None
    secret_filter: Union[dict, None] = None
    tags: Union[dict, None] = None
    resource_group: ResourceGroup
    workspace_id: Union[str, None] = None
    domain_id: str


class CollectorUpdateRequest(BaseModel):
    collector_id: str
    name: Union[str, None] = None
    schedule: Union[dict, None] = None
    secret_filter: Union[dict, None] = None
    tags: Union[dict, None] = None
    workspace_id: Union[str, None] = None
    domain_id: str


class CollectorUpdatePluginRequest(BaseModel):
    collector_id: str
    version: Union[str, None] = None
    options: Union[dict, None] = None
    upgrade_mode: Union[UpgradeMode, None] = None
    workspace_id: Union[str, None] = None
    domain_id: str


class CollectorVerifyPluginRequest(BaseModel):
    collector_id: str
    secret_id: str
    workspace_id: Union[str, None] = None
    domain_id: str


class CollectorDeleteRequest(BaseModel):
    collector_id: str
    workspace_id: Union[str, None] = None
    domain_id: str


class CollectorGetRequest(BaseModel):
    collector_id: str
    workspace_id: Union[list, str, None] = None
    domain_id: str


class CollectorSearchQueryRequest(BaseModel):
    query: Union[dict, None] = None
    collector_id: Union[str, None] = None
    workspace_id: Union[str, list, None] = None
    domain_id: str


class CollectorStatQueryRequest(BaseModel):
    query: dict
    workspace_id: Union[list, str, None] = None
    domain_id: str


class CollectorCollectRequest(BaseModel):
    collector_id: str
    secret_id: str
    workspace_id: Union[list, str, None] = None
    domain_id: str
