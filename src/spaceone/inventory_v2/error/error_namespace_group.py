
from spaceone.core.error import *


class ERROR_REQUIRED_PARAMETER(ERROR_INVALID_ARGUMENT):
    _message = "Required parameter. (key = {key})"
    
    
class ERROR_RELATED_NAMESPACE_EXIST(ERROR_INVALID_ARGUMENT):
    _message = "Related namespace is exist. (namespace_id = {namespace_id})"


class ERROR_RELATED_NAMESPACE_GROUP_EXIST(ERROR_INVALID_ARGUMENT):
    _message = "Related namespace group is exist. (namespace_group_id = {namespace_group_id})"


class ERROR_NOT_ALLOWED_TO_CHANGE_PARENT_GROUP_TO_SUB_PROJECT_GROUP(ERROR_INVALID_ARGUMENT):
    _message = "Not allowed to change parent group to sub namespace group. (namespace_group_id = {namespace_group_id})"


class ERROR_USER_NOT_IN_PROJECT_GROUP(ERROR_PERMISSION_DENIED):
    _message = "{namespace_id} is not in namespace group."
    
    