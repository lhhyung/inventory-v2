from mongoengine import *
from datetime import datetime

from spaceone.core.model.mongo_model import MongoModel
from spaceone.inventory_v2.error.asset import ERROR_RESOURCE_ALREADY_DELETED


class HistoryDiff(EmbeddedDocument):
    key = StringField(required=True)
    before = DynamicField(default=None, null=True)
    after = DynamicField(default=None, null=True)
    type = StringField(
        max_length=20, choices=("ADDED", "CHANGED", "DELETED"), required=True
    )

    def to_dict(self):
        return dict(self.to_mongo())


class History(MongoModel):
    history_id = StringField(max_length=40, generate_id="history", unique=True)
    asset_id = StringField(max_length=40, required=True)
    action = StringField(
        max_length=20, choices=("CREATE", "UPDATE", "DELETE"), required=True
    )
    diff = ListField(EmbeddedDocumentField(HistoryDiff), default=[])
    diff_count = IntField(default=0)
    updated_by = StringField(max_length=40, choices=("COLLECTOR", "USER"))
    collector_id = StringField(max_length=40, default=None, null=True)
    job_id = StringField(max_length=40, default=None, null=True)
    user_id = StringField(max_length=255, default=None, null=True)
    project_id = StringField(max_length=40)
    workspace_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now=True)

    meta = {
        "minimal_fields": [
            "history_id",
            "action",
            "diff_count",
            "asset_id",
            "updated_by",
            "user_id",
            "collector_id",
            "job_id",
        ],
        "ordering": ["-created_at"],
        "indexes": [
            {
                "fields": ["domain_id", "asset_id", "-created_at", "diff.key"],
                "name": "COMPOUND_INDEX_FOR_SEARCH",
            },
            {"fields": ["domain_id", "history_id"], "name": "COMPOUND_INDEX_FOR_GET"},
            "collector_id",
            "job_id",
            "domain_id",
        ],
    }


class Asset(MongoModel):
    asset_id = StringField(max_length=40, unique=True)
    name = StringField(default=None, null=True)
    state = StringField(max_length=20, choices=("ACTIVE", "DELETED"), default="ACTIVE")
    resource_id = StringField(max_length=255, default=None, null=True)
    ip_addresses = ListField(StringField(max_length=255), default=[])
    external_link = StringField(max_length=255, default=None, null=True)
    data = DictField()
    tags = DictField()
    provider = StringField(max_length=255)
    account = StringField(max_length=255, default=None, null=True)
    region_id = StringField(max_length=40)
    secret_id = StringField(max_length=40, default=None, null=True)
    asset_type_id = StringField(max_length=255)
    service_account_id = StringField(max_length=40, default=None, null=True)
    collector_id = StringField(max_length=40, default=None, null=True)
    project_id = StringField(max_length=40)
    workspace_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    last_collected_at = DateTimeField(default=None, null=True)
    deleted_at = DateTimeField(default=None, null=True)

    meta = {
        "updatable_fields": [
            "name",
            "data",
            "state",
            "ip_addresses",
            "tags",
            "account",
            "region_id",
            "asset_type_id",
            "secret_id",
            "service_account_id",
            "collector_id",
            "project_id",
            "updated_at",
            "last_collected_at",
            "deleted_at",
        ],
        "minimal_fields": [
            "asset_id",
            "name",
            "asset_type_id",
            "provider",
            "resource_id",
            "region_id",
            "project_id",
        ],
        "change_query_keys": {
            "user_projects": "project_id",
            "ip_address": "ip_addresses",
        },
        # "reference_query_keys": {
        #     "ref_asset_type_id": {
        #         "model": AssetType,
        #         "foreign_key": "ref_asset_type_id",
        #     },
        #     "ref_region": {"model": Region, "foreign_key": "ref_region_if"},
        # },
        "indexes": [
            {
                "fields": ["domain_id", "workspace_id", "state"],
                "name": "COMPOUND_INDEX_FOR_GC_1",
            },
            {
                "fields": ["domain_id", "state", "updated_at"],
                "name": "COMPOUND_INDEX_FOR_GC_2",
            },
            {
                "fields": ["domain_id", "state", "-deleted_at"],
                "name": "COMPOUND_INDEX_FOR_GC_3",
            },
            {
                "fields": [
                    "domain_id",
                    "workspace_id",
                    "state",
                    "resource_id",
                    "provider",
                    "asset_type_id",
                    "asset_id",
                    "account",
                ],
                "name": "COMPOUND_INDEX_FOR_COLLECTOR",
            },
            {
                "fields": [
                    "domain_id",
                    "workspace_id",
                    "state",
                    "provider",
                    "asset_type_id",
                    "project_id",
                    "region_id",
                ],
                "name": "COMPOUND_INDEX_FOR_SEARCH_1",
            },
            {
                "fields": [
                    "domain_id",
                    "workspace_id",
                    "state",
                    # "ref_cloud_service_type",
                    "project_id",
                    "region_id",
                ],
                "name": "COMPOUND_INDEX_FOR_SEARCH_2",
            },
            {
                "fields": [
                    "domain_id",
                    "workspace_id",
                    "state",
                    "-created_at",
                    "project_id",
                ],
                "name": "COMPOUND_INDEX_FOR_SEARCH_3",
            },
            {
                "fields": [
                    "domain_id",
                    "workspace_id",
                    "state",
                    "-deleted_at",
                    "project_id",
                ],
                "name": "COMPOUND_INDEX_FOR_SEARCH_4",
            },
            "resource_id",
            "state",
            "workspace_id",
            "domain_id",
        ],
    }

    def update(self, data):
        if self.state == "DELETED":
            raise ERROR_RESOURCE_ALREADY_DELETED(
                resource_type="Asset", resource_id=self.asset_id
            )

        return super().update(data)

    def delete(self):
        if self.state == "DELETED":
            raise ERROR_RESOURCE_ALREADY_DELETED(
                resource_type="Asset", resource_id=self.asset_id
            )

        self.update({"state": "DELETED", "deleted_at": datetime.utcnow()})
