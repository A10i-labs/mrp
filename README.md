## MRP (Map → Reduce → Produce)

Minimal agentic MRP runtime and compiler (Sprint 1).

### Features

- YAML → IR compiler with deterministic seed and canonical ordering
- Local threadpool runner (maps → reduce → produce)
- Content-addressed artifacts (BLAKE3 over stable JSON)
- CLI: `mrp compile`, `mrp run`, `mrp replay` (stub)

### Requirements

- Python 3.12+

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Quickstart (compile → run)

```bash
# 1) Compile: emits IR + manifest + policy
mrp compile examples/jobs/toy.yaml
# prints COMPILE_DIGEST → inspect JSON
cat .mrp/artifacts/<COMPILE_DIGEST>.json

# 2) Run: executes the job, emits execution record
mrp run examples/jobs/toy.yaml
# prints RUN_DIGEST → inspect JSON
cat .mrp/artifacts/<RUN_DIGEST>.json
```

### Input (YAML) → Output (JSON)

- Input is a YAML job spec. Example (`examples/jobs/toy.yaml`):

```yaml
version: v0
job_id: toy-001
map:
  operator: "examples.toy:UppercaseAgent"
  shards:
    - { _shard_id: 0, text: "foo" }
    - { _shard_id: 1, text: "bar" }
reduce:
  operator: "examples.toy:ConcatReducer"
  config: { sep: "-" }
produce:
  operator: "examples.toy:JsonProducer"
  config: {}
```

- Compile produces a JSON artifact containing IR, manifest, and policy:

```bash
mrp compile examples/jobs/toy.yaml
# prints a digest like: 3038c2...a1
cat .mrp/artifacts/<COMPILE_DIGEST>.json
```

- Minimal shape of the compile artifact:

```json
{
  "ir": {
    "job_id": "toy-001",
    "operators": {
      "map": "examples.toy:UppercaseAgent",
      "reduce": "examples.toy:ConcatReducer",
      "produce": "examples.toy:JsonProducer"
    },
    "seed": "<deterministic-seed>"
  },
  "manifest": {
    "job_id": "toy-001",
    "operators": { "map": "...", "reduce": "...", "produce": "..." },
    "seed": "<deterministic-seed>"
  },
  "policy": {
    "status": "ok",
    "egress_allowed": false,
    "caps": { "workers": null, "time_s": null, "mem_mb": null }
  }
}
```

- Run produces a JSON artifact containing only the execution record:

```bash
mrp run examples/jobs/toy.yaml
# prints RUN_DIGEST
cat .mrp/artifacts/<RUN_DIGEST>.json
# => { "maps": [...], "reduce": {...}, "produce": {...} }
```

### Testing

```bash
pip install pytest
pytest -q
```

### Layout

- `src/mrp/*`: compiler, IR, runtime, SDK, CLI, artifacts
- `src/examples/*`: toy operators for Sprint 1
- `examples/jobs/*`: example job specs
- `docs/mrp_PRD.md`: plan and sprint checklist
