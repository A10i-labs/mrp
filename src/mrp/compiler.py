from typing import Dict, Any, List, Tuple
from blake3 import blake3
from .dsl.schema import JobSpec, normalize_json
from pathlib import Path
import re
from .ir.model import IR, MapTask, ReduceTask, ProduceTask


def derive_seed(job: JobSpec) -> str:
    payload = normalize_json(
        {
            "dsl_version": job.version,
            "job_id": job.job_id,
            "map_shards": job.map.shards,
            "operators": {
                "map": job.map.operator,
                "reduce": job.reduce.operator,
                "produce": job.produce.operator,
            },
        }
    )
    return blake3(payload).hexdigest()


def compile_job(job: JobSpec) -> Tuple[IR, Dict[str, Any], Dict[str, Any]]:
    # Materialize any generated operators to content-addressed modules
    materialized: Dict[str, str] = {}

    def materialize_generated(kind: str, generated: Dict[str, Any] | None, fallback_operator: str | None) -> str:
        if generated and generated.get("code") and generated.get("entrypoint"):
            ops_dir = Path(".mrp/ops_pkg")
            ops_dir.mkdir(parents=True, exist_ok=True)
            code_bytes = generated["code"].encode("utf-8")
            code_digest = blake3(code_bytes).hexdigest()
            # Write to a module file using digest as name
            module_name = f"gen_{code_digest}"
            module_path = ops_dir / f"{module_name}.py"
            if not module_path.exists():
                module_path.write_bytes(code_bytes)
            # Replace module in entrypoint with our materialized module
            # If entrypoint is like "ops.gc:GCContentAgent", swap module to our module_name
            ep = generated["entrypoint"]
            ep_class = ep.split(":")[-1]
            # We add .mrp to sys.path at runtime, so import as 'ops_pkg.module:Class'
            resolved = f"ops_pkg.{module_name}:{ep_class}"
            materialized[kind] = resolved
            return resolved
        assert fallback_operator, f"{kind} must provide 'operator' or 'generated'"
        return fallback_operator

    shards_sorted = sorted(job.map.shards, key=lambda s: blake3(normalize_json(s)).hexdigest())
    maps: List[MapTask] = [
        MapTask(operator=materialize_generated("map", job.map.generated.model_dump() if job.map.generated else None, job.map.operator), shard_id=i, params=shard)
        for i, shard in enumerate(shards_sorted)
    ]
    reduce_op = materialize_generated("reduce", job.reduce.generated.model_dump() if job.reduce.generated else None, job.reduce.operator)
    produce_op = materialize_generated("produce", job.produce.generated.model_dump() if job.produce.generated else None, job.produce.operator)
    reduce_task = ReduceTask(operator=reduce_op, config=job.reduce.config)
    produce_task = ProduceTask(operator=produce_op, config=job.produce.config)
    seed = derive_seed(job)
    manifest: Dict[str, Any] = {
        "job_id": job.job_id,
        "seed": seed,
        "operators": {
            "map": materialized.get("map", job.map.operator),
            "reduce": materialized.get("reduce", job.reduce.operator),
            "produce": materialized.get("produce", job.produce.operator),
        },
    }
    policy_report: Dict[str, Any] = {
        "egress_allowed": False,
        "caps": {"workers": None, "time_s": None, "mem_mb": None},
        "status": "ok",
    }
    return IR(maps=maps, reduce=reduce_task, produce=produce_task, manifest=manifest), manifest, policy_report


