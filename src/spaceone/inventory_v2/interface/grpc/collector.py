from google.protobuf.json_format import ParseDict
from spaceone.api.inventory_v2.v1 import collector_pb2, collector_pb2_grpc
from spaceone.api.inventory_v2.v1 import job_pb2
from spaceone.core.pygrpc import BaseAPI

from spaceone.inventory_v2.service.collector_service import CollectorService


class Collector(BaseAPI, collector_pb2_grpc.CollectorServicer):
    pb2 = collector_pb2
    pb2_grpc = collector_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)
        collector_svc = CollectorService(metadata)
        response: dict = collector_svc.create(params)
        return self.dict_to_message(response)

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)
        collector_svc = CollectorService(metadata)
        response: dict = collector_svc.update(params)
        return self.dict_to_message(response)

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)
        collector_svc = CollectorService(metadata)
        collector_svc.delete(params)
        return self.empty()

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        collector_svc = CollectorService(metadata)
        response: dict = collector_svc.get(params)
        return self.dict_to_message(response)

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)
        collector_svc = CollectorService(metadata)
        response: dict = collector_svc.list(params)
        return self.dict_to_message(response)

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)
        collector_svc = CollectorService(metadata)
        response: dict = collector_svc.stat(params)
        return self.dict_to_message(response)

    def collect(self, request, context):
        params, metadata = self.parse_request(request, context)
        collector_svc = CollectorService(metadata)
        response: dict = collector_svc.collect(params)
        return ParseDict(response, job_pb2.JobInfo())

    def update_plugin(self, request, context):
        params, metadata = self.parse_request(request, context)
        collector_svc = CollectorService(metadata)
        response: dict = collector_svc.update_plugin(params)
        return self.dict_to_message(response)

    def verify_plugin(self, request, context):
        params, metadata = self.parse_request(request, context)
        collector_svc = CollectorService(metadata)
        collector_svc.verify_plugin(params)
        return self.empty()
