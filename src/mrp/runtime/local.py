from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from ..ir.model import IR
from ..artifacts.store import put_json
import importlib


def _load(path: str):
    mod_name, cls_name = path.rsplit(":", 1) if ":" in path else path.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)


def run_ir(ir: IR, max_workers: int | None = None) -> Dict[str, Any]:
    seed = ir.manifest["seed"]
    Agent = _load(ir.manifest["operators"]["map"])
    Reducer = _load(ir.manifest["operators"]["reduce"])
    Producer = _load(ir.manifest["operators"]["produce"])

    agent = Agent()
    results: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(agent.run, t.params, seed): t.shard_id for t in ir.maps}
        for fut in as_completed(futs):
            results.append(fut.result())

    results_sorted = sorted(results, key=lambda r: r.get("_shard_id", 0))
    reduce_out = Reducer().run(results_sorted, seed)
    produce_out = Producer().run(reduce_out, seed)

    run_record = {"maps": results_sorted, "reduce": reduce_out, "produce": produce_out}
    run_digest = put_json(run_record)
    return {"run_digest": run_digest, "record": run_record}


