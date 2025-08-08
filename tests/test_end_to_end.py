from mrp.dsl.schema import load_yaml
from mrp.compiler import compile_job
from mrp.runtime.local import run_ir
from mrp.artifacts.store import digest_json


def test_toy_job_reproducible():
    job = load_yaml("examples/jobs/toy.yaml")
    ir1, _, _ = compile_job(job)
    out1 = run_ir(ir1)["record"]
    ir2, _, _ = compile_job(job)
    out2 = run_ir(ir2)["record"]
    assert digest_json(out1) == digest_json(out2)


