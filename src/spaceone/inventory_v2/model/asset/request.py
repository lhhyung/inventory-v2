from typing import Union, Literal, List
from pydantic import BaseModel

__all__ = [
    "AssetCreateRequest",
    "AssetUpdateRequest",
]


class AssetCreateRequest(BaseModel):
    pass


class AssetUpdateRequest(BaseModel):
    pass
