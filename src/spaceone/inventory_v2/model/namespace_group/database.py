from email.policy import default
from mongoengine import *
from spaceone.core.model.mongo_model import MongoModel


class NamespaceGroup(MongoModel):
    namespace_group_id = StringField(max_length=80, unique_with="domain_id")
    name = StringField(max_length=255)
    icon = StringField(default=None, null=True)
    description = StringField(max_length=255, null=True, default=None)
    tags = DictField(default=None)
    is_managed = BooleanField(null=True)
    resource_group = StringField(max_length=40, choices=("DOMAIN", "WORKSPACE"))
    workspace_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    version = StringField(max_length=40, default=None, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    meta = {
        "updatable_fields": ["name", "icon", "description", "tags", "updated_at"],
        "minimal_fields": ["namespace_group_id", "name", "workspace_id", "domain_id"],
        "ordering": ["domain_id","workspace_id","-created_at"],
        "indexes": [
            "domain_id",
            "workspace_id",
            "name",
        ],
    }
