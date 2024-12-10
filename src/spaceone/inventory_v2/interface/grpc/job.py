from spaceone.api.inventory_v2.v1 import job_pb2, job_pb2_grpc
from spaceone.core.pygrpc import BaseAPI

from spaceone.inventory_v2.service.job_service import JobService


class Job(BaseAPI, job_pb2_grpc.JobServicer):
    pb2 = job_pb2
    pb2_grpc = job_pb2_grpc

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_svc = JobService(metadata)
        job_svc.delete(params)
        return self.empty()

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_svc = JobService(metadata)
        response = job_svc.get(params)
        return self.dict_to_message(response)

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_svc = JobService(metadata)
        response = job_svc.list(params)
        return self.dict_to_message(response)

    def analyze(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_svc = JobService(metadata)
        response = job_svc.analyze(params)
        return self.dict_to_message(response)

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)
        job_svc = JobService(metadata)
        response = job_svc.stat(params)
        return self.dict_to_message(response)
