from pydantic import BaseModel
from typing import Any, Dict


class ConfigItem(BaseModel):
    value: Any
    default: Any
    description: str


class ConfigResponse(BaseModel):
    config: Dict[str, ConfigItem]


class ConfigUpdate(BaseModel):
    config: Dict[str, Any]
