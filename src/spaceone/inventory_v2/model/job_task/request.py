from typing import Union, Literal, List
from pydantic import BaseModel

__all__ = [
    "JobTaskDeleteRequest",
    "JobTaskGetRequest",
    "JobTaskGetDetailRequest",
    "JobTaskSearchQueryRequest",
    "JobTaskStatQueryRequest",
    "Status",
]

Status = Literal["PENDING", "IN_PROGRESS", "SUCCESS", "FAILURE", "CANCELLED"]


class JobTaskDeleteRequest(BaseModel):
    job_task_id: str
    workspace_id: Union[str, None]
    domain_id: str


class JobTaskGetRequest(BaseModel):
    job_task_id: str
    workspace_id: Union[str, None]
    domain_id: str
    user_projects: Union[List[str], None]


class JobTaskGetDetailRequest(BaseModel):
    job_task_id: str
    workspace_id: Union[str, None]
    domain_id: str
    user_projects: Union[List[str], None]


class JobTaskSearchQueryRequest(BaseModel):
    query: dict
    job_task_id: Union[str, None]
    status: Union[Status, None]
    provider: Union[str, None]
    job_id: Union[str, None]
    secret_id: Union[str, None]
    service_account_id: Union[str, None]
    project_id: Union[str, None]
    workspace_id: Union[str, None]
    domain_id: str


class JobTaskStatQueryRequest(BaseModel):
    query: dict
    workspace_id: Union[str, None] = None
    domain_id: str
    user_projects: Union[List[str], None] = None
