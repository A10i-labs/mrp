import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig
import importlib.util
import json as _json
from ..local import _load
from ...ir.model import IR
from ...artifacts.store import put_json
from datetime import datetime
import os


def _require_daytona_key() -> str:
    load_dotenv()  # load from .env if present
    api_key = os.environ.get("DAYTONA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DAYTONA_API_KEY is not set. Ensure it is present in the environment or in .env."
        )
    return api_key


def _resolve_module_source(mod_name: str) -> str:
    # Try .mrp/ops_pkg first
    if mod_name.startswith("ops_pkg."):
        rel = mod_name.split("ops_pkg.", 1)[1] + ".py"
        p = Path(".mrp/ops_pkg/") / rel
        return p.read_text()
    # Fallback to local module file
    spec = importlib.util.find_spec(mod_name)
    if not spec or not spec.origin:
        raise RuntimeError(f"Cannot locate source for module {mod_name}")
    return Path(spec.origin).read_text()


def _daytona_remote_run(client: Daytona, entrypoint: str, payload: Any, seed: str) -> Dict[str, Any]:
    # Build a self-contained code string that defines the class and executes it
    mod_name, cls_name = entrypoint.split(":", 1)
    module_source = _resolve_module_source(mod_name)
    payload_json = _json.dumps(payload)
    code = f"""
import json
# --- embedded module source start ---
{module_source}
# --- embedded module source end ---
payload = json.loads({payload_json!r})
seed = {seed!r}
Cls = eval({cls_name!r})
out = Cls().run(payload, seed)
print(json.dumps(out))
"""
    sandbox = client.create()
    try:
        resp = sandbox.process.code_run(code)
        if getattr(resp, "exit_code", 1) != 0:
            raise RuntimeError(f"Remote execution failed: {resp.exit_code} {getattr(resp, 'result', '')}")
        text = str(resp.result)
        # Parse the last JSON line to ignore any preceding prints
        for line in reversed(text.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                return _json.loads(line)
            except Exception:
                continue
        raise RuntimeError(f"Remote execution did not yield JSON. Output head: {text[:200]}")
    finally:
        print("Deleting sandbox")
        sandbox.delete()


def run_ir_cloud(ir: IR) -> Dict[str, Any]:
    api_key = _require_daytona_key()
    # Ensure generated operators are importable
    ops_pkg_root = Path(".mrp").resolve()
    if ops_pkg_root.exists():
        root = str(ops_pkg_root)
        if root not in sys.path:
            sys.path.insert(0, root)
    client = Daytona(DaytonaConfig(api_key=api_key))
    seed = ir.manifest["seed"]
    map_entry = ir.manifest["operators"]["map"]
    reduce_entry = ir.manifest["operators"]["reduce"]
    produce_entry = ir.manifest["operators"]["produce"]

    # Simulate remote maps (sequential for now; backend will parallelize later)
    map_results: List[Dict[str, Any]] = []
    for t in ir.maps:
        out = _daytona_remote_run(client, map_entry, t.params, seed)
        map_results.append(out)

    results_sorted = sorted(map_results, key=lambda r: r.get("_shard_id", 0))
    # Reduce locally per PRD (deterministic aggregation)
    Reducer = _load(reduce_entry)
    reduce_out = Reducer().run(results_sorted, seed)
    Producer = _load(produce_entry)
    # Write outputs into a dedicated dir
    output_dir = Path(".mrp/outputs") / ir.manifest.get("job_id", "job") / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    cwd = os.getcwd()
    try:
        os.chdir(output_dir)
        produce_out = Producer().run(reduce_out, seed)
    finally:
        os.chdir(cwd)

    run_record = {
        "backend": "cloud_sandbox",
        "output_dir": str(output_dir),
        "maps": results_sorted,
        "reduce": reduce_out,
        "produce": produce_out,
    }
    run_digest = put_json(run_record)
    return {"run_digest": run_digest, "record": run_record}


