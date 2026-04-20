# Roadmap

> This roadmap is the actual build plan, followed commit by commit.
> Status updates happen here as each phase completes.

---

## Phase 1 — Foundation

Project structure, contracts and infrastructure baseline.

- [x] Repository setup and README overview
- [x] Shared Pydantic schemas (API ↔ Worker contracts)
- [x] `docker-compose.yml` — Postgres, Redis, Qdrant, Langfuse, Flower
- [x] Postgres init schema (tasks table + triggers)
- [x] `.env.example` with all required variables

---

## Phase 2 — API Gateway `[in progress]`

FastAPI service — task submission and status polling.

- [x] `POST /task` — enqueue and return `task_id` immediately (202)
- [x] `GET /task/{id}` — return status + result
- [ ] `GET /health` — basic health check
- [ ] Celery app configuration (broker, backend, serialization)
- [ ] API Dockerfile

---

## Phase 3 — Worker Core

Celery worker and LangGraph graph skeleton.

- [ ] Celery task entry point (`run_agent`)
- [ ] Task lifecycle: `pending → running → done/failed`
- [ ] LangGraph graph definition (nodes + edges + loop logic)
- [ ] Worker Dockerfile

---

## Phase 4 — Agent Nodes

Individual nodes of the graph.

- [ ] `router` — classify task as simple/complex using lightweight model
- [ ] `research` — generate response, model selected by router decision
- [ ] `critique` — approve or request revision
- [ ] `output` — format final response
- [ ] Loop logic: iterate until APPROVED or max iterations reached

---

## Phase 5 — Memory Layers

Dual-layer memory architecture.

- [ ] Short-term: PostgreSQL via LangGraph `PostgresSaver`
  - Per-step checkpoint, agent survives worker crash
- [ ] Long-term: Qdrant + `nomic-embed-text`
  - `recall_memory` node — semantic search before task starts
  - `save_memory` node — upsert summary after task completes

---

## Phase 6 — Observability

Langfuse self-hosted integration.

- [ ] LangGraph callback handler for Langfuse
- [ ] Per-node trace: time, token count, model used
- [ ] Router decision visible in traces
- [ ] Iteration count tracked per task
- [ ] Add `langfuse_trace_id` column to tasks table (migration)

---

## Phase 7 — Tools

External capabilities for the agent.

- [ ] Web search (DuckDuckGo via `langchain-community`)
- [ ] Python interpreter (isolated via subprocess + timeout)
- [ ] PDF reader (pymupdf)

---

## Phase 8 — Documentation & Benchmarks

Real numbers and written decisions.

- [ ] `docs/architecture-decisions.md` — full ADR writeup
- [ ] `docs/hardware-challenges.md` — AMD Vega 7 + Vulkan journey
- [ ] `docs/benchmarks.md` — tokens/sec, latency per node, model comparison
- [ ] How-to-run section in README
- [ ] Smoke test script

---

## Future — Beyond v1

Ideas for after the core is solid. Not committed yet.

- [ ] Model upgrade path: test `qwen2.5:7b-q4_K_M` as task model
- [ ] Horizontal worker scaling (multiple Celery workers)
- [ ] Guardrails layer (NeMo Guardrails or Llama Guard)
- [ ] MoE routing experiments
- [ ] Non-transformer architecture exploration (TTT, LFM)
- [ ] Dedicated benchmark comparing transformer vs alternative architectures on same hardware