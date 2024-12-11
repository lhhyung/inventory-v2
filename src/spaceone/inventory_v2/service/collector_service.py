import logging
import os
from typing import Union, Tuple

from mongoengine import QuerySet
from spaceone.core import utils
from spaceone.core.error import *
from spaceone.core.service import *

from spaceone.inventory_v2.manager.collection_state_manager import (
    CollectionStateManager,
)
from spaceone.inventory_v2.manager.collector_manager import CollectorManager
from spaceone.inventory_v2.manager.collector_plugin_manager import (
    CollectorPluginManager,
)
from spaceone.inventory_v2.manager.collector_rule_manager import CollectorRuleManager
from spaceone.inventory_v2.manager.identity_manager import IdentityManager
from spaceone.inventory_v2.manager.job_manager import JobManager
from spaceone.inventory_v2.manager.job_task_detail_manager import JobTaskDetailManager
from spaceone.inventory_v2.manager.job_task_manager import JobTaskManager
from spaceone.inventory_v2.manager.plugin_manager import PluginManager
from spaceone.inventory_v2.manager.repository_manager import RepositoryManager
from spaceone.inventory_v2.manager.secret_manager import SecretManager
from spaceone.inventory_v2.model import Collector
from spaceone.inventory_v2.model.collector.request import *
from spaceone.inventory_v2.model.collector.response import *
from spaceone.inventory_v2.model.job.response import JobResponse

_LOGGER = logging.getLogger(__name__)
_KEYWORD_FILTER = ["collector_id", "name", "provider"]


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class CollectorService(BaseService):
    resource = "Collector"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collector_mgr = CollectorManager()

    @transaction(
        permission="inventory-v2:Collector.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def create(self, params: CollectorCreateRequest) -> Union[CollectorResponse, dict]:
        """Create collector
        Args:
            params (dict): {
                'name': 'str',              # required
                'provider': 'str',
                'plugin_info': 'dict',      # required
                'schedule': 'dict',
                'secret_filter': 'dict',
                'tags': 'dict',
                'resource_group': 'str',    # required
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str'          # injected from auth (required)
            }

        Returns:
            collector_vo (object)
        """

        identity_mgr = IdentityManager()
        secret_mgr = SecretManager()

        domain_id = params.domain_id
        workspace_id = params.workspace_id
        resource_group = params.resource_group

        # Check permission by resource group
        if resource_group == "WORKSPACE":
            if workspace_id is None:
                raise ERROR_REQUIRED_PARAMETER(key="workspace_id")

            identity_mgr.check_workspace(workspace_id, domain_id)
        else:
            params.workspace_id = "*"

        if schedule := params.schedule:
            self._check_schedule(schedule)

        plugin_manager = PluginManager()
        collector_plugin_mgr = CollectorPluginManager()

        plugin_info = params.plugin_info
        plugin_id = plugin_info["plugin_id"]

        plugin_info_from_repository = self._get_plugin_from_repository(plugin_id)
        params.provider = self._get_plugin_providers(
            params.provider, plugin_info_from_repository
        )

        if secret_filter := params.secret_filter:
            if secret_filter.get("state") == "ENABLED":
                self._validate_secret_filter(
                    identity_mgr,
                    secret_mgr,
                    params.secret_filter,
                    params.provider,
                    domain_id,
                )
            else:
                # todo : test
                params.secret_filter = None

        collector_vo = self.collector_mgr.create_collector(params.dict())

        endpoint, updated_version = plugin_manager.get_endpoint(
            plugin_info["plugin_id"],
            domain_id,
            plugin_info.get("upgrade_mode", "AUTO"),
            plugin_info.get("version"),
        )

        plugin_response = collector_plugin_mgr.init_plugin(
            endpoint, plugin_info.get("options", {})
        )

        if updated_version:
            plugin_info["version"] = updated_version

        plugin_info["metadata"] = plugin_response.get("metadata", {})

        collector_vo = self.collector_mgr.update_collector_by_vo(
            {"plugin_info": plugin_info}, collector_vo
        )

        collector_rules = plugin_info["metadata"].get("collector_rules", [])
        self.create_collector_rules_by_metadata(
            collector_rules,
            collector_vo.collector_id,
            resource_group,
            domain_id,
            workspace_id,
        )

        return CollectorResponse(**collector_vo.to_dict())

    @transaction(
        permission="inventory-v2:Collector.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def update(self, params: CollectorUpdateRequest) -> Union[CollectorResponse, dict]:
        """Update collector
        Args:
            params (dict): {
                'collector_id': 'str',      # required
                'name': 'str',
                'schedule': 'dict',
                'secret_filter': 'dict',
                'tags': 'dict',
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str'          # injected from auth (required)
            }

        Returns:
            collector_vo (object)
        """

        domain_id = params.domain_id
        workspace_id = params.workspace_id
        collector_id = params.collector_id

        if schedule := params.schedule:
            self._check_schedule(schedule)

        collector_vo = self.collector_mgr.get_collector(
            collector_id, domain_id, workspace_id
        )

        if secret_filter := params.secret_filter:
            if secret_filter.get("state") == "ENABLED":
                identity_mgr = IdentityManager()
                secret_mgr = SecretManager()

                self._validate_secret_filter(
                    identity_mgr,
                    secret_mgr,
                    secret_filter,
                    collector_vo.provider,
                    domain_id,
                )
            else:
                params.secret_filter = {
                    "state": "DISABLED",
                }

        collector_vo = self.collector_mgr.update_collector_by_vo(
            params.dict(exclude_unset=True), collector_vo
        )
        return CollectorResponse(**collector_vo.to_dict())

    @transaction(
        permission="inventory-v2:Collector.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def update_plugin(
        self, params: CollectorUpdatePluginRequest
    ) -> Union[CollectorResponse, dict]:
        """Update plugin info of collector
        Args:
            params (dict): {
                'collector_id': 'str',      # required
                'version': 'str',
                'options': 'dict',
                'upgrade_mode': 'str',
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str'          # injected from auth (required)
            }

        Returns:
            collector_vo (object)
        """

        plugin_manager = PluginManager()

        collector_id = params.collector_id
        domain_id = params.domain_id
        workspace_id = params.workspace_id

        collector_vo = self.collector_mgr.get_collector(
            collector_id, domain_id, workspace_id
        )
        plugin_info = collector_vo.plugin_info.to_dict()

        if version := params.version:
            plugin_info["version"] = version

        if options := params.options:
            plugin_info["options"] = options

        if upgrade_mode := params.upgrade_mode:
            plugin_info["upgrade_mode"] = upgrade_mode

        endpoint, updated_version = plugin_manager.get_endpoint(
            plugin_info["plugin_id"],
            domain_id,
            plugin_info.get("upgrade_mode", "AUTO"),
            plugin_info.get("version"),
        )

        collector_vo = self._update_collector_plugin(
            endpoint, updated_version, plugin_info, collector_vo
        )
        return CollectorResponse(**collector_vo.to_dict())

    @transaction(
        permission="inventory-v2:Collector.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def verify_plugin(self, params: CollectorVerifyPluginRequest) -> None:
        """Verify plugin info of collector
        Args:
            params (dict): {
                'collector_id': 'str',      # required
                'secret_id': 'str',
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str'          # injected from auth (required)
            }

        Returns:
            collector_vo (object)
        """

        collector_plugin_mgr = CollectorPluginManager()

        plugin_manager = PluginManager()
        secret_manager = SecretManager()

        collector_id = params.collector_id
        domain_id = params.collector_id
        workspace_id = params.workspace_id

        collector_vo = self.collector_mgr.get_collector(
            collector_id, domain_id, workspace_id
        )

        if collector_vo.resource_group == "WORKSPACE":
            collector_workspace_id = collector_vo.workspace_id
        else:
            collector_workspace_id = None

        plugin_info = collector_vo.plugin_info.to_dict()

        endpoint, updated_version = plugin_manager.get_endpoint(
            plugin_info["plugin_id"],
            plugin_info.get("version"),
            plugin_info.get("upgrade_mode", "AUTO"),
            domain_id,
        )

        secret_ids = self._get_secret_ids_from_filter(
            collector_vo.secret_filter.to_dict(),
            collector_vo.provider,
            domain_id,
            params.secret_id,
            collector_workspace_id,
        )

        if secret_ids:
            secret_data_info = secret_manager.get_secret_data(secret_ids[0], domain_id)
            secret_data = secret_data_info.get("data", {})
            collector_plugin_mgr.verify_plugin(
                endpoint, plugin_info.get("options", {}), secret_data
            )

    @transaction(
        permission="inventory-v2:Collector.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @convert_model
    def delete(self, params: CollectorDeleteRequest) -> None:
        """Delete collector
        Args:
            params (dict): {
                'collector_id': 'str',      # required
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str'          # injected from auth (required)
            }

        Returns:
            None:
        """
        state_mgr = CollectionStateManager()
        job_mgr = JobManager()
        job_task_mgr = JobTaskManager()

        collector_id = params.collector_id
        domain_id = params.domain_id
        workspace_id = params.workspace_id

        collector_vo: Collector = self.collector_mgr.get_collector(
            collector_id, domain_id, workspace_id
        )

        state_mgr.delete_collection_state_by_collector_id(collector_id, domain_id)

        job_vos = job_mgr.filter_jobs(collector_id=collector_id, domain_id=domain_id)
        job_vos.delete()

        job_task_vos = job_task_mgr.filter_job_tasks(
            collector_id=collector_id, domain_id=domain_id
        )
        job_task_vos.delete()

        self.collector_mgr.delete_collector_by_vo(collector_vo)

    @transaction(
        permission="inventory-v2:Collector.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @convert_model
    def get(self, params: CollectorGetRequest) -> Union[CollectorResponse, dict]:
        """Get collector
        Args:
            params (dict): {
                'collector_id': 'str',      # required
                'workspace_id': 'str',      # injected from auth
                'domain_id': 'str'          # injected from auth (required)
            }

        Returns:
            collector_vo (object)
        """

        collector_mgr: CollectorManager = self.locator.get_manager(CollectorManager)
        collector_id = params.collector_id
        domain_id = params.domain_id
        workspace_id = params.workspace_id

        collector_vo = collector_mgr.get_collector(
            collector_id, domain_id, workspace_id
        )

        return CollectorResponse(**collector_vo.to_dict())

    @transaction(
        permission="inventory-v2:Collector.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @append_query_filter(
        [
            "collector_id",
            "name",
            "state",
            "secret_filter_state",
            "schedule_state",
            "plugin_id",
            "workspace_id",
            "domain_id",
        ]
    )
    @append_keyword_filter(_KEYWORD_FILTER)
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @convert_model
    def list(
        self, params: CollectorSearchQueryRequest
    ) -> Union[CollectorsResponse, dict]:
        """List collectors
        Args:
            params (dict): {
                    'query': 'dict (spaceone.api.core.v1.Query)',
                    'collector_id': 'str',
                    'name': 'str',
                    'secret_filter_state': 'str',
                    'schedule_state': 'str',
                    'plugin_id': 'str',
                    'workspace_id': 'str',          # injected from auth
                    'domain_id': 'str',             # injected from auth (required)
                }

        Returns:
            results (list)
            total_count (int)
        """
        query = params.query or {}
        collector_vos, total_count = self.collector_mgr.list_collectors(query=query)

        collectors_info = [collector_vo.to_dict() for collector_vo in collector_vos]
        return CollectorsResponse(results=collectors_info, total_count=total_count)

    @transaction(
        permission="inventory-v2:Collector.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @append_query_filter(["workspace_id", "domain_id"])
    @append_keyword_filter(_KEYWORD_FILTER)
    @convert_model
    def stat(self, params: CollectorStatQueryRequest) -> dict:
        """Stat collectors
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)', # required
                'workspace_id': 'str',          # injected from auth
                'domain_id': 'str',             # injected from auth (required)
            }

        Returns:
            values (list) : 'list of statistics data'

        """
        query = params.query or {}
        return self.collector_mgr.stat_collectors(query)

    @transaction(
        permission="inventory-v2:Collector.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @convert_model
    def collect(self, params: CollectorCollectRequest) -> Union[JobResponse, dict]:
        """Collect data
        Args:
            params (dict): {
                'collector_id': 'str',      # required
                'secret_id': 'str',
                'workspace_id': 'str | list',      # injected from auth
                'domain_id': 'str',         # injected from auth (required)
                'user_projects': 'list',    # injected from auth
            }

        Returns:
            job_vo (object)
        """

        plugin_mgr = PluginManager()
        job_mgr = JobManager()
        job_task_mgr = JobTaskManager()
        task_detail_mgr = JobTaskDetailManager()

        collector_id = params.collector_id
        domain_id = params.domain_id
        workspace_id = params.workspace_id

        collector_vo = self.collector_mgr.get_collector(
            collector_id, domain_id, workspace_id
        )
        collector_data = collector_vo.to_dict()

        if collector_data["resource_group"] == "WORKSPACE":
            collector_workspace_id = collector_data["workspace_id"]
        else:
            collector_workspace_id = None

        plugin_info = collector_data["plugin_info"]
        secret_filter = collector_data.get("secret_filter", {}) or {}
        plugin_id = plugin_info["plugin_id"]
        version = plugin_info.get("version")
        upgrade_mode = plugin_info.get("upgrade_mode", "AUTO")

        endpoint, updated_version = plugin_mgr.get_endpoint(
            plugin_id, domain_id, upgrade_mode, version
        )

        if updated_version and version != updated_version:
            _LOGGER.debug(
                f"[collect] upgrade plugin version: {version} -> {updated_version}"
            )
            collector_vo = self._update_collector_plugin(
                endpoint, updated_version, plugin_info, collector_vo
            )

        tasks = self._get_tasks(
            params.dict(),
            endpoint,
            collector_id,
            collector_vo.provider,
            plugin_info,
            secret_filter,
            domain_id,
            collector_workspace_id,
        )

        duplicated_job_vos = job_mgr.get_duplicate_jobs(
            collector_id, domain_id, workspace_id, params.secret_id
        )

        for job_vo in duplicated_job_vos:
            job_mgr.make_canceled_by_vo(job_vo)

        # create job
        create_job_params = params.dict()
        create_job_params["plugin_id"] = plugin_id
        create_job_params["total_tasks"] = len(tasks)
        create_job_params["remained_tasks"] = len(tasks)
        job_vo = job_mgr.create_job(collector_vo, create_job_params)

        _LOGGER.debug(f"[collect] total tasks ({job_vo.job_id}): {len(tasks)}")
        if len(tasks) > 0:
            for task in tasks:
                secret_info = task["secret_info"]
                sub_tasks = task.get("sub_tasks", [])
                if len(sub_tasks) == 0:
                    sub_task_count = 1
                else:
                    sub_task_count = len(sub_tasks)

                if "sub_tasks" in task:
                    del task["sub_tasks"]

                create_params = {
                    "total_sub_tasks": sub_task_count,
                    "remained_sub_tasks": sub_task_count,
                    "job_id": job_vo.job_id,
                    "collector_id": job_vo.collector_id,
                    "secret_id": secret_info.get("secret_id"),
                    "service_account_id": secret_info.get("service_account_id"),
                    "project_id": secret_info.get("project_id"),
                    "workspace_id": secret_info.get("workspace_id"),
                    "domain_id": domain_id,
                }

                task.update({"collector_id": collector_id, "job_id": job_vo.job_id})

                try:
                    # create job task
                    job_task_vo = job_task_mgr.create_job_task(create_params)
                    task_detail_vo = task_detail_mgr.create_job_task_detail_by_task_vo(
                        job_task_vo
                    )
                    task.update({"job_task_id": job_task_vo.job_task_id})

                    if len(sub_tasks) > 0:
                        for sub_task in sub_tasks:
                            task_options = sub_task.get("task_options", {})
                            task.update(
                                {"task_options": task_options, "is_sub_task": True}
                            )
                            _LOGGER.debug(
                                f"[collect] push sub task ({job_task_vo.job_task_id}) => {utils.dump_json(task_options)}"
                            )
                            job_task_mgr.push_job_task(task)
                    else:
                        _LOGGER.debug(
                            f"[collect] push job task ({job_task_vo.job_task_id})"
                        )
                        job_task_mgr.push_job_task(task)

                except Exception as e:
                    _LOGGER.error(
                        f"[collect] Error to create job task ({job_vo.job_id}): {e}",
                        exc_info=True,
                    )
                    job_mgr.make_failure_by_vo(job_vo)

            self.collector_mgr.update_last_collected_time(collector_vo)
        else:
            # close job if no tasks
            job_mgr.make_success_by_vo(job_vo)

        return JobResponse(**job_vo.to_dict())

    def _get_tasks(
        self,
        params: dict,
        endpoint: str,
        collector_id: str,
        collector_provider: str,
        plugin_info: dict,
        secret_filter: dict,
        domain_id: str,
        collector_workspace_id: str = None,
    ) -> list:
        secret_mgr = SecretManager()
        collector_plugin_mgr = CollectorPluginManager()

        tasks = []
        secret_ids = self._get_secret_ids_from_filter(
            secret_filter,
            collector_provider,
            domain_id,
            params.get("secret_id"),
            collector_workspace_id,
        )

        for secret_id in secret_ids:
            secret_info = secret_mgr.get_secret(secret_id, domain_id)
            secret_data = secret_mgr.get_secret_data(secret_id, domain_id)

            _task = {
                "plugin_info": plugin_info,
                "secret_info": secret_info,
                "secret_data": secret_data,
                "domain_id": domain_id,
            }

            response = collector_plugin_mgr.get_tasks(
                endpoint,
                secret_data.get("data", {}),
                plugin_info.get("options", {}),
            )
            _LOGGER.debug(f"[get_tasks] sub tasks({collector_id}): {response}")
            _task["sub_tasks"] = response.get("tasks", [])
            tasks.append(_task)

        return tasks

    @staticmethod
    def _check_secrets(
        secret_mgr: SecretManager, secret_ids: list, provider: str, domain_id: str
    ) -> None:
        query = {
            "filter": [
                {"k": "secret_id", "v": secret_ids, "o": "in"},
                {"k": "provider", "v": provider, "o": "eq"},
            ],
            "count_only": True,
        }
        response = secret_mgr.list_secrets(query, domain_id)
        total_count = response.get("total_count", 0)

        if total_count != len(secret_ids):
            raise ERROR_INVALID_PARAMETER(
                key="secret_filter.secrets",
                reason=f"secrets are not found: {', '.join(secret_ids)}",
            )

    @staticmethod
    def _check_service_accounts(
        identity_mgr: IdentityManager,
        service_account_ids: list,
        provider: str,
        domain_id: str,
    ) -> None:
        query = {
            "filter": [
                {
                    "k": "service_account_id",
                    "v": service_account_ids,
                    "o": "in",
                },
                {"k": "provider", "v": provider, "o": "eq"},
            ],
            "count_only": True,
        }

        response = identity_mgr.list_service_accounts(query, domain_id)
        total_count = response.get("total_count", 0)

        if total_count != len(service_account_ids):
            raise ERROR_INVALID_PARAMETER(
                key="secret_filter.service_accounts",
                reason=f"service accounts are not found: {', '.join(service_account_ids)}",
            )

    @staticmethod
    def _check_schemas(
        identity_mgr: IdentityManager,
        schema_ids: list,
        provider: str,
        domain_id: str,
    ) -> None:
        query = {
            "filter": [
                {
                    "k": "schema_id",
                    "v": schema_ids,
                    "o": "in",
                },
                {"k": "provider", "v": provider, "o": "eq"},
            ],
            "count_only": True,
        }

        response = identity_mgr.list_schemas(query, domain_id)
        total_count = response.get("total_count", 0)

        if total_count != len(schema_ids):
            raise ERROR_INVALID_PARAMETER(
                key="secret_filter.schemas",
                reason=f"schemas are not found: {', '.join(schema_ids)}",
            )

    def _validate_secret_filter(
        self,
        identity_mgr: IdentityManager,
        secret_mgr: SecretManager,
        secret_filter: dict,
        provider: str,
        domain_id: str,
    ) -> None:
        if "secrets" in secret_filter:
            self._check_secrets(
                secret_mgr, secret_filter["secrets"], provider, domain_id
            )

        if "service_accounts" in secret_filter:
            self._check_service_accounts(
                identity_mgr, secret_filter["service_accounts"], provider, domain_id
            )

        if "schemas" in secret_filter:
            self._check_schemas(
                identity_mgr, secret_filter["schemas"], provider, domain_id
            )

        if "exclude_secrets" in secret_filter:
            self._check_secrets(
                secret_mgr, secret_filter["exclude_secrets"], provider, domain_id
            )

        if "exclude_service_accounts" in secret_filter:
            self._check_service_accounts(
                identity_mgr,
                secret_filter["exclude_service_accounts"],
                provider,
                domain_id,
            )

        if "exclude_schemas" in secret_filter:
            self._check_schemas(
                identity_mgr, secret_filter["exclude_schemas"], provider, domain_id
            )

    def _update_collector_plugin(
        self,
        endpoint: str,
        updated_version: str,
        plugin_info: dict,
        collector_vo: Collector,
    ) -> Collector:
        collector_plugin_mgr = CollectorPluginManager()
        plugin_response = collector_plugin_mgr.init_plugin(
            endpoint, plugin_info.get("options", {})
        )

        if updated_version:
            plugin_info["version"] = updated_version

        plugin_info["metadata"] = plugin_response.get("metadata", {})

        collector_vo = self.collector_mgr.update_collector_by_vo(
            {"plugin_info": plugin_info}, collector_vo
        )

        self.delete_collector_rules(collector_vo.collector_id, collector_vo.domain_id),

        collector_rules = plugin_info["metadata"].get("collector_rules", [])
        self.create_collector_rules_by_metadata(
            collector_rules,
            collector_vo.collector_id,
            collector_vo.resource_group,
            collector_vo.domain_id,
            collector_vo.workspace_id,
        )

        return collector_vo

    def _get_secret_ids_from_filter(
        self,
        secret_filter: dict,
        provider: str,
        domain_id: str,
        secret_id: str = None,
        workspace_id: str = None,
    ) -> list:
        secret_manager: SecretManager = self.locator.get_manager(SecretManager)

        query = {
            "filter": self._make_secret_filter(
                secret_filter, provider, secret_id, workspace_id
            )
        }

        response = secret_manager.list_secrets(query, domain_id)

        return [
            secret_info.get("secret_id") for secret_info in response.get("results", [])
        ]

    @check_required(["hour"])
    def scheduled_collectors(self, params: dict) -> Tuple[QuerySet, int]:
        """Search all collectors in this schedule.
        This is global search out-of domain.

        Args:
            params(dict): {
                'hour': 'int',        # required
            }

        Returns:
            results (list)
            total_count (int)
        """

        collector_mgr: CollectorManager = self.locator.get_manager(CollectorManager)
        query = {
            "filter": [
                {"k": "schedule.state", "v": "ENABLED", "o": "eq"},
                {"k": "schedule.hours", "v": params["hour"], "o": "contain"},
            ]
        }
        return collector_mgr.list_collectors(query)

    @staticmethod
    def _get_plugin_from_repository(plugin_id: str) -> dict:
        repo_mgr = RepositoryManager()
        return repo_mgr.get_plugin(plugin_id)

    @staticmethod
    def create_collector_rules_by_metadata(
        collector_rules: list,
        collector_id: str,
        resource_group: str,
        domain_id: str,
        workspace_id: str = None,
    ):
        collector_rule_mgr = CollectorRuleManager()

        for collector_rule_params in collector_rules:
            collector_rule_params.update(
                {
                    "collector_id": collector_id,
                    "rule_type": "MANAGED",
                    "resource_group": resource_group,
                    "workspace_id": workspace_id,
                    "domain_id": domain_id,
                }
            )

            collector_rule_mgr.create_collector_rule(collector_rule_params)

    @staticmethod
    def delete_collector_rules(collector_id: str, domain_id: str) -> None:
        collector_rule_mgr = CollectorRuleManager()
        old_collector_rule_vos = collector_rule_mgr.filter_collector_rules(
            collector_id=collector_id, rule_type="MANAGED", domain_id=domain_id
        )
        old_collector_rule_vos.delete()

    @staticmethod
    def _make_secret_filter(
        secret_filter: dict,
        provider: str,
        secret_id: str = None,
        workspace_id: str = None,
    ) -> list:
        _filter = [{"k": "provider", "v": provider, "o": "eq"}]

        if secret_id:
            _filter.append({"k": "secret_id", "v": secret_id, "o": "eq"})

        if workspace_id:
            _filter.append({"k": "workspace_id", "v": workspace_id, "o": "eq"})

        if secret_filter.get("state") == "ENABLED":
            if secrets := secret_filter.get("secrets"):
                _filter.append({"k": "secret_id", "v": secrets, "o": "in"})

            if service_accounts := secret_filter.get("service_accounts"):
                _filter.append(
                    {"k": "service_account_id", "v": service_accounts, "o": "in"}
                )

            if schemas := secret_filter.get("schemas"):
                _filter.append({"k": "schema", "v": schemas, "o": "in"})

            if exclude_secrets := secret_filter.get("exclude_secrets"):
                _filter.append({"k": "secret_id", "v": exclude_secrets, "o": "not_in"})

            if exclude_service_accounts := secret_filter.get(
                "exclude_service_accounts"
            ):
                _filter.append(
                    {
                        "k": "service_account_id",
                        "v": exclude_service_accounts,
                        "o": "not_in",
                    }
                )

            if exclude_schemas := secret_filter.get("exclude_schemas"):
                _filter.append({"k": "schema", "v": exclude_schemas, "o": "not_in"})

        return _filter

    @staticmethod
    def _convert_plugin_provider_to_categories(plugin_info: dict) -> list:
        categories = []
        supported_providers = plugin_info.get("capability", {}).get(
            "supported_providers", []
        )

        if supported_providers:
            # Multi providers
            categories.extend(supported_providers)
        elif provider := plugin_info.get("provider"):
            # Single provider
            categories.append(provider)

        return categories

    @staticmethod
    def _get_plugin_providers(provider: str, plugin_info: dict) -> str:
        supported_providers = plugin_info.get("capability", {}).get(
            "supported_providers", []
        )

        if supported_providers:
            # Multi providers
            if provider in supported_providers:
                return provider
            else:
                raise ERROR_INVALID_PARAMETER(
                    key="provider", reason=f"Not supported provider: {provider}"
                )
        else:
            # Single provider
            return provider if provider else plugin_info.get("provider")

    @staticmethod
    def _check_schedule(schedule: dict) -> None:
        if schedule.get("state") == "ENABLED":
            if hours := schedule.get("hours"):
                if len(hours) > 2:
                    raise ERROR_INVALID_PARAMETER(
                        key="schedule.hours", reason="Maximum 2 hours can be set."
                    )
