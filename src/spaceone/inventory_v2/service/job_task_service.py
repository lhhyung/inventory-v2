from typing import Union

from spaceone.core.service import *

from spaceone.inventory_v2.manager.job_task_detail_manager import JobTaskDetailManager
from spaceone.inventory_v2.manager.job_task_manager import JobTaskManager
from spaceone.inventory_v2.model.job_task.database import JobTask
from spaceone.inventory_v2.model.job_task.request import *
from spaceone.inventory_v2.model.job_task.response import *


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class JobTaskService(BaseService):
    resource = "JobTask"

    def __init__(self, metadata):
        super().__init__(metadata)
        self.job_task_mgr = JobTaskManager()
        self.job_task_detail_mgr = JobTaskDetailManager()

    @transaction(
        permission="inventory-v2:JobTask.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def delete(self, params: JobTaskDeleteRequest) -> None:
        """
        Args:
            params (dict): {
                'job_task_id': 'str',       # required
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str'          # injected from auth (required)
            }

        Returns:
            None
        """

        job_task_id = params.job_task_id
        domain_id = params.domain_id
        workspace_id = params.workspace_id

        job_task_vo: JobTask = self.job_task_mgr.get(
            job_task_id, domain_id, workspace_id
        )
        self.job_task_mgr.delete_job_task_by_vo(job_task_vo)

    @transaction(
        permission="inventory-v2:JobTask.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @convert_model
    def get(self, params: JobTaskGetRequest) -> Union[JobTaskResponse, dict]:
        """
        Args:
            params (dict): {
                'job_task_id': 'str',       # required
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str',         # injected from auth (required)
                'user_projects': 'list'     # injected from auth
            }

        Returns:
            job_task_vo (object)
        """

        job_task_vo = self.job_task_mgr.get_job_task(
            params.job_task_id,
            params.domain_id,
            params.workspace_id,
            params.user_projects,
        )

        return JobTaskResponse(**job_task_vo.to_dict())

    @transaction(
        permission="inventory-v2:JobTask.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @convert_model
    def get_detail(
        self, params: JobTaskGetDetailRequest
    ) -> Union[JobTaskDetailResponse, dict]:
        """
        Args:
            params (dict): {
            }
        Returns:
            job_task_detail_vo (object)
        """

        job_task_detail_vo = self.job_task_detail_mgr.get_job_task_detail(
            params.job_task_id,
            params.domain_id,
            params.workspace_id,
            params.user_projects,
        )
        return JobTaskDetailResponse(**job_task_detail_vo.to_dict())

    @transaction(
        permission="inventory-v2:JobTask.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @append_query_filter(
        [
            "job_task_id",
            "status",
            "provider",
            "job_id",
            "secret_id",
            "service_account_id",
            "project_id",
            "workspace_id",
            "domain_id",
            "user_projects",
        ]
    )
    @append_keyword_filter(["job_task_id"])
    @convert_model
    def list(self, params: JobTaskSearchQueryRequest) -> Union[JobTasksResponse, dict]:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v2.Query)',
                'job_task_id': 'str',
                'status': 'str',
                'job_id': 'str',
                'secret_id': 'str',
                'provider': 'str',
                'service_account_id': 'str',
                'project_id': 'str',
                'workspace_id': 'str',          # injected from auth
                'domain_id  ': 'str',           # injected from auth (required)
                'user_projects': 'list',        # injected from auth
            }

        Returns:
            results (list)
            total_count (int)
        """
        query = params.query or {}

        job_task_vos, total_count = self.job_task_mgr.list(query)

        job_task_infos = [job_task_vo.to_dict() for job_task_vo in job_task_vos]
        return JobTasksResponse(results=job_task_infos, total_count=total_count)

    @transaction(
        permission="inventory-v2:JobTask.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @append_keyword_filter(["job_task_id"])
    @convert_model
    def stat(self, params: JobTaskStatQueryRequest) -> dict:
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',     # required
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str',         # injected from auth (required)
                'user_projects': 'list',    # injected from auth
            }

        Returns:
            values (list) : 'list of statistics data'
        """

        query = params.query or {}
        return self.job_task_mgr.stat(query)
