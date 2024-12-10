from datetime import datetime
from typing import Union, Literal, List
from pydantic import BaseModel

from spaceone.core import utils

from spaceone.inventory_v2.model.job_task.request import Status

__all__ = ["JobTaskResponse", "JobTasksResponse", "JobTaskDetailResponse"]


class JobTaskResponse(BaseModel):
    job_task_id: Union[str, None] = None
    status: Union[Status, None] = None
    provider: Union[str, None] = None
    created_count: Union[int, None] = None
    updated_count: Union[int, None] = None
    failure_count: Union[int, None] = None
    deleted_count: Union[int, None] = None
    disconnected_count: Union[int, None] = None
    job_id: Union[str, None] = None
    secret_id: Union[str, None] = None
    service_account_id: Union[str, None] = None
    collector_id: Union[str, None] = None
    project_id: Union[str, None] = None
    workspace_id: Union[str, None] = None
    domain_id: Union[str, None] = None
    created_at: Union[datetime, None] = None
    started_at: Union[datetime, None] = None
    updated_at: Union[datetime, None] = None
    finished_at: Union[datetime, None] = None

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["created_at"] = utils.datetime_to_iso8601(data["created_at"])
        data["started_at"] = utils.datetime_to_iso8601(data.get("started_at"))
        data["updated_at"] = utils.datetime_to_iso8601(data.get("updated_at"))
        data["finished_at"] = utils.datetime_to_iso8601(data.get("finished_at"))
        return data


class JobTaskDetailResponse(BaseModel):
    job_task_id: Union[str, None] = None
    created_info: Union[dict, None] = None
    updated_info: Union[dict, None] = None
    failure_info: Union[dict, None] = None
    deleted_info: Union[dict, None] = None
    disconnected_info: Union[dict, None] = None
    job_id: Union[str, None] = None
    project_id: Union[str, None] = None
    workspace_id: Union[str, None] = None
    domain_id: Union[str, None] = None
    created_at: Union[datetime, None] = None

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        data["created_at"] = utils.datetime_to_iso8601(data["created_at"])


class JobTasksResponse(BaseModel):
    results: List[JobTaskResponse]
    total_count: Union[int, None] = None
