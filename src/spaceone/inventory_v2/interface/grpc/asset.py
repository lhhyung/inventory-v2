from spaceone.api.inventory_v2.v1 import asset_pb2, asset_pb2_grpc
from spaceone.core.pygrpc import BaseAPI

from spaceone.inventory_v2.service import AssetService


class Asset(BaseAPI, asset_pb2_grpc.AssetServicer):
    pb2 = asset_pb2
    pb2_grpc = asset_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)
        asset_svc = AssetService(metadata)
        response: dict = asset_svc.create(params)
        return self.dict_to_message(response)

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "CloudServiceService", metadata
        ) as cloud_svc_service:
            return self.locator.get_info(
                "CloudServiceInfo", cloud_svc_service.update(params)
            )

    def pin_data(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "CloudServiceService", metadata
        ) as cloud_svc_service:
            return self.locator.get_info(
                "CloudServiceInfo", cloud_svc_service.pin_data(params)
            )

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "CloudServiceService", metadata
        ) as cloud_svc_service:
            cloud_svc_service.delete(params)
            return self.locator.get_info("EmptyInfo")

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "CloudServiceService", metadata
        ) as cloud_svc_service:
            return self.locator.get_info(
                "CloudServiceInfo", cloud_svc_service.get(params)
            )

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)
        asset_svc = AssetService(metadata)
        response: dict = asset_svc.list(params)
        return self.dict_to_message(response)

    def export(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "CloudServiceService", metadata
        ) as cloud_svc_service:
            return self.locator.get_info("ExportInfo", cloud_svc_service.export(params))

    def history(self, request, context):
        params, metadata = self.parse_request(request, context)
        asset_svc = AssetService(metadata)
        response: dict = asset_svc.history(params)
        return self.dict_to_message(response)

    def analyze(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "CloudServiceService", metadata
        ) as cloud_svc_service:
            return self.locator.get_info(
                "AnalyzeInfo", cloud_svc_service.analyze(params)
            )

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "CloudServiceService", metadata
        ) as cloud_svc_service:
            return self.locator.get_info(
                "StatisticsInfo", cloud_svc_service.stat(params)
            )
