from spaceone.core.pygrpc.server import GRPCServer
from .region import Region
from .collector import Collector
from .job import Job
from .job_task import JobTask
from .namespace_group import NamespaceGroup
from .namespace import Namespace

_all_ = ["app"]

app = GRPCServer()
app.add_service(Region)
app.add_service(Collector)
app.add_service(Job)
app.add_service(JobTask)
app.add_service(NamespaceGroup)
app.add_service(Namespace)