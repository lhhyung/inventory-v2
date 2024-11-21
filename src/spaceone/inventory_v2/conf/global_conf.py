# System Token
TOKEN = ""

DATABASE_AUTO_CREATE_INDEX = True
DATABASES = {
    "default": {
        "db": "inventory-v2",
        "host": "localhost",
        "port": 27017,
        "username": "",
        "password": "",
    }
}

CACHES = {
    "default": {},
    "local": {
        "backend": "spaceone.core.cache.local_cache.LocalCache",
        "max_size": 128,
        "ttl": 300,
    },
}

HANDLERS = {
    # "authentication": [{
    #     "backend": "spaceone.core.handler.authentication_handler:SpaceONEAuthenticationHandler"
    # }],
    # "authorization": [{
    #     "backend": "spaceone.core.handler.authorization_handler:SpaceONEAuthorizationHandler"
    # }],
    # "mutation": [{
    #     "backend": "spaceone.core.handler.mutation_handler:SpaceONEMutationHandler"
    # }],
    # "event": []
}

# Log Settings
LOG = {"filters": {"masking": {"rules": {}}}}

CONNECTORS = {
    "SpaceConnector": {
        "backend": "spaceone.core.connector.space_connector:SpaceConnector",
        "endpoints": {
            "board": "grpc://board:50051",
            "config": "grpc://config:50051",
            "cost_analysis": "grpc://cost-analysis:50051",
            "identity": "grpc://identity:50051",
            "monitoring": "grpc://monitoring:50051",
            "file_manager": "grpc://file-manager:50051",
            "secret": "grpc://secret:50051"
        },
    }
}

# Scheduler Settings
QUEUES = {}
SCHEDULERS = {}
WORKERS = {}
TOKEN_INFO = {}
