from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, List
import yaml
import orjson


class MapSpec(BaseModel):
    operator: str
    shards: List[Dict[str, Any]] = Field(default_factory=list)


class ReduceSpec(BaseModel):
    operator: str
    config: Dict[str, Any] = Field(default_factory=dict)


class ProduceSpec(BaseModel):
    operator: str
    config: Dict[str, Any] = Field(default_factory=dict)


class JobSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str = "v0"
    job_id: str
    map: MapSpec
    reduce: ReduceSpec
    produce: ProduceSpec


def load_yaml(path: str) -> JobSpec:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return JobSpec.model_validate(data)


def normalize_json(data: Any) -> bytes:
    return orjson.dumps(data, option=orjson.OPT_SORT_KEYS)


