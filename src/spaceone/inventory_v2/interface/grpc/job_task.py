from spaceone.api.inventory_v2.v1 import job_task_pb2, job_task_pb2_grpc
from spaceone.core.pygrpc import BaseAPI

from spaceone.inventory_v2.service.job_task_service import JobTaskService


class JobTask(BaseAPI, job_task_pb2_grpc.JobTaskServicer):
    pb2 = job_task_pb2
    pb2_grpc = job_task_pb2_grpc

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_task_svc = JobTaskService(metadata)
        job_task_svc.delete(params)
        return self.empty()

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_task_svc = JobTaskService(metadata)
        response = job_task_svc.get(params)
        return self.dict_to_message(response)

    def get_detail(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_task_svc = JobTaskService(metadata)
        response = job_task_svc.get_detail(params)
        return self.dict_to_message(response)

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_task_svc = JobTaskService(metadata)
        response = job_task_svc.list(params)
        return self.dict_to_message(response)

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_task_svc = JobTaskService(metadata)
        response = job_task_svc.stat(params)
        return self.dict_to_message(response)
