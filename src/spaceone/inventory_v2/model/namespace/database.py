from unicodedata import category
from mongoengine import *
from typing import Dict, List, Literal, Union
from spaceone.core.model.mongo_model import MongoModel


class Namespace(MongoModel):
    namespace_id = StringField(max_length=40, unique_with="domain_id")
    name = StringField(max_length=255)
    category = StringField(max_length=40, default=None, null=True)
    icon = StringField(default=None, null=True)
    tag = DictField(default=None)
    is_managed = BooleanField(null=True)
    resource_group = StringField(max_length=40, choices=("DOMAIN", "WORKSPACE"))
    namespace_group_id = StringField(max_length=40)
    workspace_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    version = StringField(max_length=40, default=None, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    meta = {
        "updatable_fields": ["name", "icon", "tag", "updated_at"],
        "minimal_fields": ["namespace_group_id", "name", "workspace_id","domain_id"],
        "ordering": ["domain_id","workspace_id","namespace_group_id", "name"],
        "indexes": [
            "domain_id",
            "workspace_id",
            "namespace_group_id",
            "name",
        ],
    }
