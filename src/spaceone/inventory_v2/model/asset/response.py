from datetime import datetime
from typing import Union, List

from pydantic import BaseModel
from spaceone.core import utils


class AssetResponse(BaseModel):
    asset_id: Union[str, None]
    name: Union[str, None]
    provider: Union[str, None]
    ipaddresses: Union[List[str], None]
    account: Union[str, None]
    data: Union[dict, None]
    metadata: Union[dict, None]
    tags: Union[dict, None]
    region_id: Union[str, None]
    asset_type_id: Union[str, None]
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
