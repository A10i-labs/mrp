# Daytona, the Sandbox

Let’s design the cloud-sandbox E2E without code. Below is exactly what to add or change so your current Sprint-1 compiler/run pipeline can execute map tasks in Daytona, then reduce and produce locally.

# High-level flow (no code)

1. compile YAML → IR, manifest, policy (unchanged)
2. runtime picks backend: local or cloud\_sandbox
3. map phase: each shard is executed in a Daytona sandbox; results stream back
4. reduce phase: deterministic, local
5. produce phase: local, gated by policy
6. artifacts: execution record includes per-shard remote logs/outputs and a final reduce/produce summary

# New/updated folders and files

## config

* config/profiles/daytona.yaml
  runtime backend defaults, region, instance class, timeout, retries, concurrency, cost caps
* config/allowlists/egress.yaml
  allow Daytona API domain only when backend = cloud\_sandbox
* config/security/sandbox\_profile.yaml
  limits for cpu/mem/gpu, no network inside user code unless explicitly enabled

## packages: runtime and backend

* src/mrp/runtime/backends/**init**.py
  registry of runnable backends: local, cloud\_sandbox
* src/mrp/runtime/backends/cloud\_sandbox.py
  orchestrates Daytona jobs per shard, handles retries, collects stdout/stderr, exit codes
* src/mrp/runtime/executors.py
  thin dispatcher that routes map tasks to selected backend; reduce/produce remain local
* src/mrp/runtime/result\_merge.py
  stable ordering merge of remote map outputs; checksum verification
* src/mrp/runtime/retry.py
  retry policy and classification (retryable vs permanent) for remote runs
* src/mrp/runtime/metrics.py
  timers, counters, cost estimates for remote runs; per-shard tracing ids

## packages: sandbox packaging and contracts

* src/mrp/sandbox/packager.py
  builds a minimal, content-addressed package for a map task: generated operator code, its deps manifest, shard payload
* src/mrp/sandbox/contracts.py
  defines the run contract: entrypoint signature, input/output schema for remote execution
* src/mrp/sandbox/runner\_stub/
  tiny on-sandbox launcher files that import the generated operator and execute the shard; captured as text assets by packager

## packages: artifacts and lineage

* src/mrp/artifacts/remote\_index.py
  maps shard\_id → {sandbox\_id, start/end time, exit\_code, stdout\_digest, output\_digest}
* src/mrp/artifacts/uploaders.py
  optional hook to upload large stdout/logs if needed later (kept local for now)
* src/mrp/lineage/run\_record.py
  one place to assemble the final execution JSON including remote shards

## CLI updates

* src/mrp/cli/args.py
  adds --backend flag (local|cloud\_sandbox) and --profile daytona
* src/mrp/cli/commands/run\_cloud.py
  wires compile artifact + profile to executors dispatcher

## policy

* src/mrp/policy/egress.py
  enforces that egress is only to Daytona endpoints when backend = cloud\_sandbox
* src/mrp/policy/budgets.py
  adds per-shard max runtime and cluster concurrency gates for cloud runs

## IR changes

* src/mrp/ir/model.py
  add fields:

  * execution\_backend: local or cloud\_sandbox (default local)
  * sandbox\_profile\_ref: pointer to config/security/sandbox\_profile.yaml
  * packaging: mode = inline\_code or ops\_pkg\_ref (from generated operator)
* src/mrp/ir/validation.py
  ensures that when backend = cloud\_sandbox, map operator is pure, no produce in map, and egress policy is compatible

## examples

* examples/jobs/cloud\_toy.yaml
  same toy job, but with execution\_backend: cloud\_sandbox on map; local reduce/produce
* examples/jobs/cloud\_generated.yaml
  generated map operator with a few shards to prove remote execution path
* examples/inputs/shards/\*.json
  simple payloads used by cloud examples

## docs

* docs/cloud\_backend.md
  how the cloud\_sandbox backend works, packaging, retry model, and limits
* docs/runbooks/daytona\_e2e.md
  operator’s guide for running the cloud example end-to-end; expected outputs and where to inspect them

## tests

* tests/cloud/test\_cloud\_packager.py
  asserts package is content-addressed and reproducible
* tests/cloud/test\_cloud\_dispatch.py
  simulates Daytona API with a stub; verifies retries and result collection
* tests/cloud/test\_reduce\_integration.py
  runs map remotely (stubbed), then reduce locally; verifies deterministic aggregation
* tests/cloud/test\_policy\_guardrails.py
  ensures egress windows and budgets are enforced by backend selection

# Minimal changes to current flow

1. compile path
   keep as-is. Only extend IR to carry execution\_backend and sandbox\_profile\_ref. Compiler sets backend from YAML or default to local.

2. run path
   cli passes backend to executors; executors routes map to cloud backend if requested; reduce/produce stay local.

3. artifact shape
   augment the run artifact with:

   * backend: cloud\_sandbox
   * per\_shard: sandbox\_id, attempt\_count, start\_ts, end\_ts, exit\_code, stdout\_digest, output\_digest
   * reduce\_input\_order\_digest: checksum proving stable ordering of map outputs
   * policy\_enforcement: egress\_allowlist\_version, sandbox\_profile\_version
   * costs: estimated and actual (if available)

4. policy enforcement
   before dispatching the first shard, validate allowlists and budgets; refuse to run if Daytona key missing or egress not allowed by policy.

5. packaging boundary
   generated operators are already materialized to .mrp/ops\_pkg. Packager builds a self-contained runnable unit per shard referencing that code. No new codegen changes required.

6. sandbox lifecycle
   cloud backend is responsible to create sandbox, run, collect, and delete per shard; concurrency controlled by profile; retries with jitter.

# YAML deltas (design only)

* job level:

  * execution\_backend: cloud\_sandbox
  * backend\_profile: daytona
* policy overrides (optional):

  * max\_concurrency\_map: N
  * shard\_timeout\_s: T
  * max\_retries: R

# Acceptance criteria for the new E2E

* running mrp run examples/jobs/cloud\_toy.yaml with backend cloud\_sandbox produces:

  * per-shard remote execution records and outputs in artifacts
  * local reduce output identical across replays
  * produce output identical across replays
  * strict cleanup of sandboxes with no stragglers

## Sample Daytona code

```python

import os
import sys
from dotenv import load_dotenv
from daytona import Daytona, DaytonaConfig

load_dotenv()

def main() -> None:
    api_key = os.environ.get("DAYTONA_API_KEY")
    if not api_key:
        print(
            "DAYTONA_API_KEY is not set. Ensure it is present in the environment or in .env at the repo root.",
            file=sys.stderr,
        )
        sys.exit(1)

    config = DaytonaConfig(api_key=api_key)
    daytona_client = Daytona(config)

    sandbox = daytona_client.create()
    response = sandbox.process.code_run('print("Hello World from code!!")')
    if getattr(response, "exit_code", 1) != 0:
        print(f"Error: {response.exit_code} {response.result}", file=sys.stderr)
        sys.exit(response.exit_code or 1)
    else:
        print(str(response.result))

    # Delete the sandbox
    sandbox.delete()

if __name__ == "__main__":
    main()


```
