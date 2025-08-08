from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AgentBase(ABC):
    @abstractmethod
    def run(self, params: Dict[str, Any], seed: str) -> Dict[str, Any]:
        ...


class ReducerBase(ABC):
    @abstractmethod
    def run(self, inputs: List[Dict[str, Any]], seed: str) -> Dict[str, Any]:
        ...


class ProducerBase(ABC):
    @abstractmethod
    def run(self, result: Dict[str, Any], seed: str) -> Dict[str, Any]:
        ...


