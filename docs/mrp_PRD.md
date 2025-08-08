# Agentic MRP Build Plan (Ray + Docker)

This document captures the step-by-step plan for prioritization, monorepo design, boundaries, and implementation.

## What to build first (priorities)

### 1. Compiler + Policy (MVP-critical)

* YAML DSL schema, parser/normalizer (reject unknowns), IR (MapTask\[], ReduceTask, ProduceTask)
* Determinism: canonical ordering, seed derivation, numeric policy
* Policy checks: caps (workers/time/mem), no-egress default, allowlisted agents/sinks, budget estimate
* Exit criteria: compile(query) → {IR, manifest, policy\_report}; fails closed

### 2. Runtime Library (Local → Ray)

* API to run IR on local threadpool (dev), then Ray (fan-out)
* Checkpointed map outputs to content-addressed store; deterministic reduce; gated produce
* Exit criteria: small MRP job runs with 2 agents, 1 reducer, 1 producer; reproducible

### 3. Operator Registry + SDK

* Agent/Reducer/Producer base classes + versioned metadata; allowlist + pinned digests
* Exit criteria: operators register, lint, and run under IR planner with pinned versions

### 4. Cost/Quota Governor + Observability

* Compile-time budgets; runtime concurrency caps + kill switch; OpenTelemetry + Prometheus
* Exit criteria: budget breach aborts; per-shard cost/latency tracked; replay from artifacts

### 5. (Deferred) K8s Isolation & Produce Sinks

* Dropped from MVP; to be reintroduced for hard sandboxing in future phases

## Monorepo strategy

* One repo for now: enables atomic refactors across compiler, runtime, SDK, operators
* Future split: possible boundaries include compiler, runtime, sdk, operators, console, infra

## Monorepo layout (Python-first)

```
mrp/
├─ docs/                      # ADRs, DSL spec, operator contracts
├─ .github/workflows/         # CI config
├─ tools/                     # pre-commit, codegen, schema checks
├─ infra/                     # infra setup (Ray only for MVP)
├─ packages/
│  ├─ dsl/                    # schema, parser, validator, normalizer
│  ├─ ir/                     # IR model and planner
│  ├─ policy/                 # safety, cost, determinism rules
│  ├─ runtime/                # Runner API, backends: local, ray
│  ├─ sdk/                    # AgentBase, ReducerBase, ProducerBase
│  ├─ registry/               # operator registry metadata and signatures
│  ├─ artifacts/              # content-addressed store and hashing
│  ├─ evaluator/              # optional evaluation step before produce
│  └─ cli/                    # CLI interface (compile/run/replay)
├─ services/
│  ├─ coordinator/            # API to compile, plan, submit
│  └─ console/                # CLI or web UI (later phase)
├─ operators/                 # agents, reducers, producers (pinned)
├─ examples/                  # toy jobs, determinism tests
└─ tests/                     # unit and integration tests
```

## Tooling

* Python 3.12 with uv, ruff, mypy, pytest, hypothesis
* Docker images pinned by digest; Ray for execution
* Content-addressing: BLAKE3 over normalized JSON
* Release mgmt: changesets, trunk-based dev, pre-commit

## Contracts and boundaries

* Compiler → Runtime: IR.json + manifest.json
* Runtime → Artifacts: {shard\_id → output\_digest} + logs/metrics
* Operators → Registry: operator.yaml (name, version, image, schema)
* Produce → Sinks: sink.yaml + ACL/schema; only produce may write

## Key decisions

* Language: Python-first; Go/Rust deferred
* Numeric policy: Decimal or math.fsum; no unordered FP ops
* Sandbox: Docker only for MVP, no network, pinned deps
* Budgets: per-job quotas; default kill at 120% of estimate
* Seeds: derived from (dsl\_version, job\_id, inputs\_digest, versions)

## CI/CD and testing

* Pipelines: lint → typecheck → unit tests → replay tests → Ray tests → image build
* Determinism CI: replay N previous runs → assert output digest match
* Security: image scans, pinned deps, SBOM, signed containers
* Policy-as-tests: admission test coverage for invalid jobs

## Minimal infra

* Dev: local runner + Ray local + MinIO + SQLite
* Team: Ray cluster, S3, DynamoDB, OTEL stack
* Prod: Optional future K8s integration for hardened produce

## Sprint plan

### Sprint 1 — Compiler & Local Runner

* DSL schema + validator; IR model; seed and numeric policy
* Local runner backend; 2 agents, 1 reducer, 1 producer
* Exit: mrp compile + mrp run --local → reproducible digests

### Sprint 2 — Ray Backend, Registry, Governor

* Ray backend; caching; operator registry + signatures
* Compile-time budget estimator; runtime caps; OpenTelemetry
* Exit: 1k-shard Ray job runs; budget kills enforced; metrics visible

### Sprint 3 — Side-Effect Gating and Replay

* Gated produce sinks; audit trail; deterministic replays
* Optional CLI tooling for inspect/replay; basic observability
* Exit: one-click replay from stored artifacts; side-effects gated

## Governance

* ADRs: 1-pagers in /docs/adrs (DSL, policy, sandbox)
* Codeowners: compiler (A), runtime (B), operators (C), infra (D)
* Operator intake: validate schema, reproducibility, test vectors

## Splitting strategy

* Split only when necessary (operators, console, etc.)
* Preserve compiler/runtime/SDK interfaces to support clean extraction

# Sprints

 Here's a breakdown of your implementation plan into **granular, actionable TODOs** — each with **low-to-moderate complexity (2–3 points)**, ready to be added to Jira or executed one-by-one in your dev workflow.

---

## ✅ Sprint 1: Compiler & Local Runner

### Theme: Get from YAML to IR and run a small job locally

#### 🧩 DSL & Compiler

1. [x] Define initial YAML schema for MRP jobs (Map → Reduce → Produce)
2. [x] Implement Pydantic-based validator that rejects unknown fields
3. [x] Build normalization logic for canonical ordering of shards and config
4. [x] Generate deterministic seed from (DSL version, job\_id, input hash)
5. [x] Add compiler that converts YAML → IR (MapTask\[], ReduceTask, ProduceTask)

#### 🧠 IR Representation

6. [x] Define `MapTask`, `ReduceTask`, and `ProduceTask` dataclasses
7. [x] Serialize IR to JSON + manifest snapshot (operator versions, digests)

#### ⚙️ Runtime (Local Threadpool)

8. [x] Implement local runner using Python `concurrent.futures.ThreadPoolExecutor`
9. [x] Create mock AgentBase, ReducerBase, ProducerBase with test behavior
10. [x] Implement output digesting using BLAKE3 (JSON-stable serialization)

#### 🧪 Test & Replay

11. [x] Run a toy job end-to-end: 2 map agents → reduce → produce → JSON
12. [x] Store run artifact manifest and verify deterministic replay

---

## 🚀 Sprint 2: Ray Backend + Registry + Cost Policies

### Theme: Execute jobs at scale using Ray; add safety + cost controls

#### ⚡ Ray Integration

13. [ ] Set up basic Ray runner backend with Task support
14. [ ] Support running MapTasks on Ray with async checkpointing
15. [ ] Implement Ray-based ReduceTask with stable ordered inputs

#### 🧱 Operator Registry

16. [ ] Define `operator.yaml` schema for agents/reducers/producers
17. [ ] Implement registry loader and signature validation
18. [ ] Add allowlist enforcement based on pinned operator digests

#### 💵 Cost Governance

19. [ ] Estimate compile-time cost: shards × operator weight
20. [ ] Enforce max budget during execution (kill switch trigger)
21. [ ] Add concurrency limits and shard retry caps

#### 📈 Observability

22. [ ] Add OpenTelemetry spans for each Map/Reduce/Produce phase
23. [ ] Expose Prometheus metrics: per-shard latency, retries, failures

#### 🧪 Replay

24. [ ] Store artifact digests per run and replay command (`mrp replay --run-id X`)
25. [ ] Confirm byte-for-byte output identity with original run

---

## 🧪 Sprint 3: Produce Phase Gating + Evaluation

### Theme: Gate and log all side-effects, enable replay and QA

#### ✅ Produce Phase

26. [ ] Implement sink.yaml contract to describe side-effect destinations
27. [ ] Create JSON and Parquet producers with write audit logs
28. [ ] Enforce policy: only produce phase can write externally

#### 🔍 Evaluation Layer

29. [ ] Add optional LLM-evaluator stub for output scoring (post-reduce)
30. [ ] Gate produce step based on evaluator result or rules (e.g., 90%+)

#### 🧾 Auditing + Replay

31. [ ] Store full manifest of: inputs, IR, operator versions, image digests
32. [ ] Implement `mrp inspect` CLI to explore a run and download outputs

---

## 🧭 Bonus (Parallel Tasks)

These can be done in parallel or as stretch goals:

* [ ] Set up content-addressable object store (MinIO or S3)
* [ ] Bootstrap minimal CLI: `mrp compile`, `mrp run`, `mrp replay`
* [ ] Create golden output test cases for 2–3 example jobs
* [ ] Define test harness to simulate shard failures and verify retry logic
* [ ] Setup pre-commit hooks: ruff, mypy, pytest, code formatting

---

Let me know if you’d like these exported to a Jira-style `.csv`, markdown checklist, or auto-populated into GitHub issues (if you want to wire that up).
