from typing import Dict, Any, List, Tuple
from blake3 import blake3
from .dsl.schema import JobSpec, normalize_json
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
    shards_sorted = sorted(job.map.shards, key=lambda s: blake3(normalize_json(s)).hexdigest())
    maps: List[MapTask] = [
        MapTask(operator=job.map.operator, shard_id=i, params=shard)
        for i, shard in enumerate(shards_sorted)
    ]
    reduce_task = ReduceTask(operator=job.reduce.operator, config=job.reduce.config)
    produce_task = ProduceTask(operator=job.produce.operator, config=job.produce.config)
    seed = derive_seed(job)
    manifest: Dict[str, Any] = {
        "job_id": job.job_id,
        "seed": seed,
        "operators": {
            "map": job.map.operator,
            "reduce": job.reduce.operator,
            "produce": job.produce.operator,
        },
    }
    policy_report: Dict[str, Any] = {
        "egress_allowed": False,
        "caps": {"workers": None, "time_s": None, "mem_mb": None},
        "status": "ok",
    }
    return IR(maps=maps, reduce=reduce_task, produce=produce_task, manifest=manifest), manifest, policy_report


