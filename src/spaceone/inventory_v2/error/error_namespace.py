from spaceone.core.error import *


class ERROR_RELATED_NAMESPACE_GROUP(ERROR_INVALID_ARGUMENT):
    _message = (
        "Related namespace_group is exist. (namespace_group_id = {namespace_group_id})"
    )


class ERROR_NOT_ALLOWED_ADD_USER_TO_PUBLIC_PROJECT(ERROR_INVALID_ARGUMENT):
    _message = "Not allowed to add user to public project."