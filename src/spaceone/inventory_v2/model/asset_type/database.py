from mongoengine import *

from spaceone.core.model.mongo_model import MongoModel


class AssetType(MongoModel):
    asset_type_id = StringField(max_length=40, unique=True)
    name = StringField(max_length=255)
    description = StringField(max_length=255, default=None, null=True)
    icon = StringField(max_length=255, default=None, null=True)
    provider = StringField(max_length=255)
    metadata = DictField()
    tags = DictField()
    is_managed = BooleanField(default=None, null=True)
    resource_group = StringField(
        max_length=255, required=True, choices=("DOMAIN", "WORKSPACE")
    )
    asset_groups = StringField(max_length=255)
    workspace_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    updated_by = StringField(default=None, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    meta = {
        "updatable_fields": [
            "name",
            "description",
            "icon",
            "metadata",
            "tags",
            "asset_groups",
            "updated_by",
            "updated_at",
        ],
        "minimal_fields": ["asset_type_id", "name", "provider", "asset_groups"],
        "change_query_keys": {
            "asset_groups": "asset_group_id",
        },
        "ordering": ["provider", "name", "resource_group"],
        "indexes": [
            {
                "fields": ["domain_id", "-updated_at", "updated_by"],
                "name": "COMPOUND_INDEX_FOR_GC_1",
            },
            {
                "fields": ["domain_id", "workspace_id", "asset_type_id"],
                "name": "COMPOUND_INDEX_FOR_SEARCH_1",
            },
            {
                "fields": [
                    "domain_id",
                    "workspace_id",
                    "provider",
                    "asset_groups",
                    "name",
                ],
                "name": "COMPOUND_INDEX_FOR_SEARCH_2",
            },
            # {
            #     "fields": ["domain_id", "workspace_id", "cloud_service_type_key"],
            #     "name": "COMPOUND_INDEX_FOR_SEARCH_3",
            # },
            # {
            #     "fields": ["cloud_service_type_id", "ref_cloud_service_type"],
            #     "name": "COMPOUND_INDEX_FOR_REF_1",
            # },
            # {
            #     "fields": ["labels", "is_primary", "ref_cloud_service_type"],
            #     "name": "COMPOUND_INDEX_FOR_REF_2",
            # },
            # "ref_cloud_service_type",
            "workspace_id",
            "domain_id",
        ],
    }
