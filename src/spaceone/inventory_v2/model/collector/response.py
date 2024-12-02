from datetime import datetime
from typing import Union, Literal, List
from pydantic import BaseModel

from spaceone.core import utils

from spaceone.inventory_v2.model.collector.request import ResourceGroup

__all__ = [
    "CollectorResponse",
    "CollectorsResponse",
]


class CollectorResponse(BaseModel):
    collector_id: Union[str, None] = None
    name: Union[str, None] = None
    provider: Union[str, None] = None
    secret_filter: Union[dict, None] = None
    plugin_info: Union[dict, None] = None
    schedule: Union[dict, None] = None
    tags: Union[dict, None] = None
    resource_group: ResourceGroup
    workspace_id: Union[str, None] = None
    domain_id: Union[str, None] = None
    created_at: Union[datetime, None] = None
    updated_at: Union[datetime, None] = None
    last_collected_at: Union[datetime, None] = None

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["created_at"] = utils.datetime_to_iso8601(data["created_at"])
        data["updated_at"] = utils.datetime_to_iso8601(data["updated_at"])
        data["last_collected_at"] = utils.datetime_to_iso8601(
            data.get("last_collected_at")
        )
        return data


class CollectorsResponse(BaseModel):
    results: List[CollectorResponse]
    total_count: int
