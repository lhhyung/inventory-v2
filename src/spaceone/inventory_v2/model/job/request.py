from typing import Union, Literal, List
from pydantic import BaseModel

__all__ = [
    "JobDeleteRequest",
    "JobGetRequest",
    "JobSearchQueryRequest",
    "JobAnalyzeQueryRequest",
    "JobStatQueryRequest",
]

Status = Literal["CANCELED", "IN_PROGRESS", "FAILURE", "SUCCESS"]


class JobDeleteRequest(BaseModel):
    job_id: str
    workspace_id: Union[str, None]
    domain_id: str


class JobGetRequest(BaseModel):
    job_id: str
    workspace_id: Union[list, str, None]
    domain_id: str


class JobSearchQueryRequest(BaseModel):
    query: dict
    job_id: Union[str, None]
    collector_id: Union[str, None]
    workspace_id: Union[list, str, None]
    domain_id: str


class JobAnalyzeQueryRequest(BaseModel):
    query: Union[dict, None] = None
    workspace_id: Union[list, str, None] = None
    domain_id: str


class JobStatQueryRequest(BaseModel):
    query: dict
    workspace_id: Union[str, None] = None
    domain_id: str
