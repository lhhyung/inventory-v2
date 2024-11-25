from spaceone.core.pygrpc.server import GRPCServer
from .region import Region

_all_ = ["app"]

app = GRPCServer()
app.add_service(Region)