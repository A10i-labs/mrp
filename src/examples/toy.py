from typing import Dict, Any, List


class UppercaseAgent:
    def run(self, params: Dict[str, Any], seed: str) -> Dict[str, Any]:
        print(f"UppercaseAgent running with params: {params}")
        return {"_shard_id": params["_shard_id"], "text": str(params["text"]).upper()}


class ConcatReducer:
    def run(self, inputs: List[Dict[str, Any]], seed: str) -> Dict[str, Any]:
        print(f"ConcatReducer running with inputs: {inputs}")
        joined = "-".join([x["text"] for x in inputs])
        return {"joined": joined}


class JsonProducer:
    def run(self, result: Dict[str, Any], seed: str) -> Dict[str, Any]:
        return result


