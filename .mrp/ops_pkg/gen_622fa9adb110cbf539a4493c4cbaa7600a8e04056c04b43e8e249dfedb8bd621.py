from typing import Dict, Any, List
class AvgReducer:
    def run(self, inputs: List[Dict[str, Any]], seed: str) -> Dict[str, Any]:
        vals = [x.get("gc", 0.0) for x in inputs]
        avg = sum(vals) / max(len(vals), 1)
        return {"avg_gc": avg}
