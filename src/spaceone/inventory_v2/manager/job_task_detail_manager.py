import logging
from typing import Tuple

from spaceone.core.manager import BaseManager
from spaceone.core.model.mongo_model import QuerySet

from spaceone.inventory_v2.model.job_task.database import JobTask, JobTaskDetail

_LOGGER = logging.getLogger(__name__)


class JobTaskDetailManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_task_detail_model = JobTaskDetail
        self.job_task_model = JobTask

    def create_job_task_detail_by_task_vo(self, job_task_vo: JobTask) -> JobTaskDetail:
        def _rollback(vo: JobTaskDetail):
            _LOGGER.info(f"[ROLLBACK] Delete job task detail: {vo.job_task_id}")
            vo.delete()

        params = {
            "job_task_id": job_task_vo.job_task_id,
            "job_id": job_task_vo.job_id,
        }
        job_task_detail_vo: JobTaskDetail = self.job_task_detail_model.create(params)

        self.transaction.add_rollback(_rollback, job_task_vo)

        return job_task_detail_vo

    def get_job_task_detail(
        self,
        job_task_id: str,
        domain_id: str,
        workspace_id: str = None,
        user_projects: list = None,
    ) -> JobTaskDetail:
        conditions = {
            "job_task_id": job_task_id,
            "domain_id": domain_id,
        }

        if workspace_id:
            conditions["workspace_id"] = workspace_id

        if user_projects:
            conditions["project_id"] = user_projects

        return self.job_task_detail_model.get(**conditions)

    def filter_job_task_details(self, **conditions) -> QuerySet:
        return self.job_task_detail_model.filter(**conditions)

    def list_job_task_details(self, query: dict) -> Tuple[QuerySet, int]:
        return self.job_task_detail_model.query(**query)

    def stat_job_task_details(self, query: dict) -> dict:
        return self.job_task_detail_model.stat(**query)
