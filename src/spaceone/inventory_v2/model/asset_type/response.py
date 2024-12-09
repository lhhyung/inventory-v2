from typing import Union, Literal, List
from pydantic import BaseModel

__all__ = ["AssetTypeResponse"]

ResourceGroup = Literal["DOMAIN", "WORKSPACE"]


class AssetTypeResponse(BaseModel):
    pass
