from typing import Union, Literal, List
from pydantic import BaseModel

__all__ = []

Status = Literal['CANCELED', 'IN_PROGRESS', 'FAILURE', 'SUCCESS']
