import typer
from ..dsl.schema import load_yaml
from ..compiler import compile_job
from ..runtime.local import run_ir as run_ir_local
from ..runtime.backends.cloud_sandbox import run_ir_cloud as run_ir_cloud
from ..artifacts.store import put_json


app = typer.Typer(help="MRP CLI")


@app.command()
def compile(path: str):
    job = load_yaml(path)
    ir, manifest, policy = compile_job(job)
    print("IR/manifest compiled.")
    print(put_json({"ir": ir.manifest, "manifest": manifest, "policy": policy}))


@app.command()
def run(path: str, backend: str = "local"):
    job = load_yaml(path)
    ir, _, _ = compile_job(job)
    if backend == "cloud_sandbox":
        result = run_ir_cloud(ir)
    else:
        result = run_ir_local(ir)
    print(result["run_digest"])


@app.command()
def replay(run_digest: str):
    print("Replay stub (Sprint 2+)")


if __name__ == "__main__":
    app()


