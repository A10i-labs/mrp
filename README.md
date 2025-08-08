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

### Quickstart

```bash
# Run toy example
mrp run examples/jobs/toy.yaml

# View artifact
ls .mrp/artifacts
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
