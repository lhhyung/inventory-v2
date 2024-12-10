from datetime import datetime
from typing import Union, Literal, List
from pydantic import BaseModel

from spaceone.core import utils

from spaceone.inventory_v2.model.job.request import Status

__all__ = ["JobResponse", "JobsResponse"]


class JobResponse(BaseModel):
    job_id: Union[str, None] = None
    status: Union[Status, None] = None
    total_tasks: Union[int, None] = None
    remained_tasks: Union[int, None] = None
    success_tasks: Union[int, None] = None
    failure_tasks: Union[int, None] = None
    collector_id: Union[str, None] = None
    request_secret_id: Union[str, None] = None
    request_workspace_id: Union[str, None] = None
    plugin_id: Union[str, None] = None
    resource_group: Union[str, None] = None
    workspace_id: Union[str, None] = None
    domain_id: Union[str, None] = None
    created_at: Union[datetime, None] = None
    updated_at: Union[datetime, None] = None
    finished_at: Union[datetime, None] = None

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["created_at"] = utils.datetime_to_iso8601(data["created_at"])
        data["updated_at"] = utils.datetime_to_iso8601(data["updated_at"])
        data["finished_at"] = utils.datetime_to_iso8601(data.get("finished_at"))
        return data


class JobsResponse(BaseModel):
    results: List[JobResponse]
    total_count: Union[int, None] = None
