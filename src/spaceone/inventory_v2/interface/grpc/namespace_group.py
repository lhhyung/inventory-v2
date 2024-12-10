from google.protobuf.json_format import ParseDict
from spaceone.api.inventory_v2.v1 import namespace_group_pb2, namespace_group_pb2_grpc
from spaceone.core.pygrpc import BaseAPI

from spaceone.inventory_v2.service.namespace_group_service import NamespaceGroupService


class NamespaceGroup(BaseAPI, namespace_group_pb2_grpc.NamespaceGroupServicer):

    pb2 = namespace_group_pb2
    pb2_grpc = namespace_group_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)
        namespacegroup_svc = NamespaceGroupService(metadata)
        response: dict = namespacegroup_svc.create(params)
        return self.dict_to_message(response)

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)
        namespacegroup_svc = NamespaceGroupService(metadata)
        response: dict = namespacegroup_svc.update(params)
        return self.dict_to_message(response)

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)
        namespacegroup_svc = NamespaceGroupService(metadata)
        response: dict = namespacegroup_svc.delete(params)
        return self.empty()

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)
        namespacegroup_svc = NamespaceGroupService(metadata)
        response: dict = namespacegroup_svc.get(params)
        return self.dict_to_message(response)

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)
        namespacegroup_svc = NamespaceGroupService(metadata)
        response: dict = namespacegroup_svc.list(params)
        return self.dict_to_message(response)

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)
        namespacegroup_svc = NamespaceGroupService(metadata)
        response: dict = namespacegroup_svc.stat(params)
        return self.dict_to_message(response)