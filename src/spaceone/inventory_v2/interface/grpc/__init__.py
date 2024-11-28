from spaceone.core.pygrpc.server import GRPCServer
from .region import Region
from .collector import Collector

_all_ = ["app"]

app = GRPCServer()
app.add_service(Region)
app.add_service(Collector)
