# Generated operator module (ephemeral)
from typing import Dict, Any
class GCContentAgent:
    def run(self, params: Dict[str, Any], seed: str) -> Dict[str, Any]:
        seq = params.get("seq", "")
        if not seq:
            return {"_shard_id": params.get("_shard_id", 0), "gc": 0.0}
        seq = seq.upper()
        g = seq.count("G")
        c = seq.count("C")
        gc = (g + c) / max(len(seq), 1)
        return {"_shard_id": params.get("_shard_id", 0), "gc": gc}
