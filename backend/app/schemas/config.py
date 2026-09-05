from pydantic import BaseModel
from typing import Any, Dict


class ConfigItem(BaseModel):
    value: Any
    default: Any
    description: str
    # 이 설정이 환경변수로 재정의되고 있으면 그 변수명과 실제 적용 값.
    # (예: MUSIC_BASE_PATH 가 설정돼 있으면 library_path 는 저장돼도 무시된다)
    env_override: Any = None
    env_value: Any = None


class ConfigResponse(BaseModel):
    config: Dict[str, ConfigItem]


class ConfigUpdate(BaseModel):
    config: Dict[str, Any]
