from datetime import datetime
from typing import Union, List, Literal

from pydantic import BaseModel
from spaceone.core import utils

__all__ = ["AssetResponse", "AssetsResponse", "AssetHistoriesResponse"]

Action = Literal["CREATE", "UPDATE", "DELETE"]


class AssetHistoryResponse(BaseModel):
    history_id: Union[str, None]
    asset_id: Union[str, None]
    action: Union[Action, None]
    diff: Union[list, None]
    diff_count: Union[int, None]
    updated_by: Union[str, None]
    user_id: Union[str, None]
    collector_id: Union[str, None]
    job_id: Union[str, None]
    domain_id: Union[str, None]
    created_at: Union[datetime, None]

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["created_at"] = utils.datetime_to_iso8601(data["created_at"])
        return data


class AssetHistoriesResponse(BaseModel):
    results: List[AssetHistoryResponse]
    total_count: int


class AssetResponse(BaseModel):
    asset_id: Union[str, None]
    name: Union[str, None]
    provider: Union[str, None]
    ip_addresses: Union[List[str], None]
    account: Union[str, None]
    data: Union[dict, None]
    tags: Union[dict, None]
    region_id: Union[str, None]
    asset_type_id: Union[str, None]
    secret_id: Union[str, None]
    service_account_id: Union[str, None]
    collector_id: Union[str, None]
    project_id: Union[str, None]
    workspace_id: Union[str, None]
    domain_id: Union[str, None]
    created_at: Union[datetime, None]
    updated_at: Union[datetime, None]

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["created_at"] = utils.datetime_to_iso8601(data["created_at"])
        data["updated_at"] = utils.datetime_to_iso8601(data.get("updated_at"))
        return data


class AssetsResponse(BaseModel):
    results: List[AssetResponse]
    total_count: int
