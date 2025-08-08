from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class MapTask:
    operator: str
    shard_id: int
    params: Dict[str, Any]


@dataclass(frozen=True)
class ReduceTask:
    operator: str
    config: Dict[str, Any]


@dataclass(frozen=True)
class ProduceTask:
    operator: str
    config: Dict[str, Any]


@dataclass(frozen=True)
class IR:
    maps: List[MapTask]
    reduce: ReduceTask
    produce: ProduceTask
    manifest: Dict[str, Any]


