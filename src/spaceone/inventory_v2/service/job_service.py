from typing import Union

from spaceone.core.service import *

from spaceone.inventory_v2.model.job.database import Job
from spaceone.inventory_v2.manager.job_manager import JobManager
from spaceone.inventory_v2.manager.job_task_manager import JobTaskManager
from spaceone.inventory_v2.model.job.request import *
from spaceone.inventory_v2.model.job.response import *


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class JobService(BaseService):
    resource = "Job"

    def __init__(self, metadata):
        super().__init__(metadata)
        self.job_mgr = JobManager()

    @transaction(
        permission="inventory-v2:Job.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def delete(self, params: JobDeleteRequest) -> None:
        """
        Args:
            params (dict): {
                'job_id': 'str',        # required
                'workspace_id': 'str',  # injected from auth
                'domain_id': 'str'      # injected from auth (required)
            }

        Returns:
            None
        """
        job_id = params.job_id
        domain_id = params.domain_id
        workspace_id = params.workspace_id

        job_vo: Job = self.job_mgr.get_job(job_id, domain_id, workspace_id)

        job_task_mgr = JobTaskManager()

        job_task_vos = job_task_mgr.filter_job_tasks(job_id=job_id, domain_id=domain_id)
        job_task_vos.delete()

        self.job_mgr.delete_job_by_vo(job_vo)

    @transaction(
        permission="inventory-v2:Job.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @append_query_filter(["workspace_id", "domain_id"])
    @convert_model
    def get(self, params: JobGetRequest) -> Union[JobResponse, dict]:
        """
        Args:
            params (dict): {
                'job_id': 'str',        # required
                'workspace_id': 'str',  # injected from auth
                'domain_id': 'str',     # injected from auth (required)
            }

        Returns:
            job_vo (object)
        """

        job_vo = self.job_mgr.get_job(
            params.job_id, params.domain_id, params.workspace_id
        )
        return JobResponse(**job_vo.to_dict())

    @transaction(
        permission="inventory-v2:Job.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @append_query_filter(
        [
            "job_id",
            "status",
            "collector_id",
            "plugin_id",
            "workspace_id",
            "domain_id",
        ]
    )
    @append_keyword_filter(["job_id"])
    @set_query_page_limit(1000)
    @convert_model
    def list(self, params: JobSearchQueryRequest) -> Union[JobsResponse, dict]:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'job_id': 'str',
                'status': 'str',
                'collector_id': 'dict',
                'plugin_id': 'str',
                'workspace_id': 'str',      # injected from auth
                'domain_id  ': 'str',       # injected from auth (required)
            }

        Returns:
            results (list)
            total_count (int)
        """

        query = params.query or {}
        job_vos, total_count = self.job_mgr.list_jobs(query)

        job_infos = [job_vo.to_dict() for job_vo in job_vos]

        return JobsResponse(results=job_infos, total_count=total_count)

    @transaction(
        permission="inventory-v2:Job.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @append_query_filter(["workspace_id", "domain_id"])
    @append_keyword_filter(["job_id"])
    @set_query_page_limit(1000)
    @convert_model
    def analyze(self, params: JobAnalyzeQueryRequest) -> dict:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.AnalyzeQuery)',    # required
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str',         # injected from auth (required)
            }

        Returns:
            dict: {
                'results': 'list',
                'total_count': 'int'
            }
        """

        query = params.query or {}
        return self.job_mgr.analyze_jobs(query)

    @transaction(
        permission="inventory-v2:Job.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @append_query_filter(["workspace_id", "domain_id"])
    @append_keyword_filter(["job_id"])
    @set_query_page_limit(1000)
    @convert_model
    def stat(self, params: JobStatQueryRequest) -> dict:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',     # required
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str',         # injected from auth (required)
            }

        Returns:
            values (list) : 'list of statistics data'
        """

        query = params.query or {}
        return self.job_mgr.stat_jobs(query)
