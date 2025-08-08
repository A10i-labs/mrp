import typer
from ..dsl.schema import load_yaml
from ..compiler import compile_job
from ..runtime.local import run_ir
from ..artifacts.store import put_json


app = typer.Typer(help="MRP CLI")


@app.command()
def compile(path: str):
    job = load_yaml(path)
    ir, manifest, policy = compile_job(job)
    print("IR/manifest compiled.")
    print(put_json({"ir": ir.manifest, "manifest": manifest, "policy": policy}))


@app.command()
def run(path: str, local: bool = True):
    job = load_yaml(path)
    ir, _, _ = compile_job(job)
    result = run_ir(ir)
    print(result["run_digest"])


@app.command()
def replay(run_digest: str):
    print("Replay stub (Sprint 2+)")


if __name__ == "__main__":
    app()


