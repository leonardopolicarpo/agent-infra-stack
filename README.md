# 🏭 Agent Infra Stack

> Scalable multi-agent pipeline running on consumer hardware (AMD iGPU via Vulkan). Features LangGraph orchestration with persistent checkpointing, async task queue, dual-layer memory architecture, and self-hosted observability.

> 🚧 **Active development** — follow the commits to see it being built step by step.

---

## Overview

Most agent projects are monolithic Python scripts. This one isn't.

`agent-infra-stack` is a production-oriented multi-agent system designed around separation of concerns: the model doesn't know about the queue, the queue doesn't know about memory, and the API doesn't wait for the agent to finish. Each layer can scale independently.

Built as a portfolio showcase for **AI Infrastructure / ML Engineer** roles, with real architectural decisions documented along the way.

---

## Architecture

```text
Client
  │
  │  POST /task  →  returns task_id immediately (202)
  ▼
FastAPI ──► Redis Queue ──► Celery Worker
                                  │
                      ┌───────────▼────────────┐
                      │     LangGraph Graph    │
                      │                        │
                      │  recall_memory         │ ◄── Qdrant (long-term)
                      │       │                │
                      │    router              │     classify: simple/complex
                      │       │                │
                      │   research  ◄──────────┤     generate response
                      │       │                │
                      │   critique             │     approve or request revision
                      │       │                │
                      │   (loop until APPROVED or max iterations)
                      │       │                │
                      │    output              │
                      │       │                │
                      │  save_memory           │ ──► Qdrant (upsert)
                      └───────────┬────────────┘
                                  │
                             PostgreSQL
                          (results + checkpoints)
                                  │
                      GET /task/{id}  ◄── Client polling
```

---

## Stack

| Layer | Technology | Role |
|---|---|---|
| Inference | Ollama (Vulkan backend) | OpenAI-compatible API, AMD iGPU acceleration |
| Orchestration | LangGraph | Cyclic graph with native checkpointing |
| Task Queue | Redis + Celery | Async execution, ack-late (no task loss on crash) |
| Short-term Memory | PostgreSQL + LangGraph Checkpointer | Per-step state persistence, survives restarts |
| Long-term Memory | Qdrant + nomic-embed-text | Semantic RAG over past interactions |
| Observability | Langfuse (self-hosted) | Per-node traces, token cost, latency |
| API Gateway | FastAPI (async) | Immediate task_id response, status polling |
| Queue Monitor | Celery Flower | Real-time worker and task visibility |

---

## Key Design Decisions

**Why async task queue instead of streaming?**
Agents take time — sometimes minutes. A synchronous request would timeout or block. The client submits a task, gets a `task_id` immediately, and polls for the result. This is how production systems handle long-running inference.

**Why two memory layers?**
Short-term (PostgreSQL via LangGraph Checkpointer) holds the current graph state — every step is saved, so the agent resumes exactly where it stopped if the worker crashes. Long-term (Qdrant) holds semantic summaries of past tasks — the agent gets relevant context before starting new work without blowing up the context window.

**Why a router node?**
Not every task needs the largest model. A lightweight classifier (3b) decides complexity first. Simple tasks never reach the heavier model — direct inference cost reduction with no code changes needed to swap models.

**Why Ollama on the host instead of inside Docker?**
iGPU passthrough to Docker on Linux with AMD Vulkan is painful and fragile. Ollama runs on the host with full GPU access, Docker Compose points to `host.docker.internal:11434`. Clean separation, zero performance loss.

---

## Hardware

Running on a **Ryzen 5 5600G** (Vega 7 iGPU, 16GB shared RAM) with **100% GPU acceleration via Vulkan backend** (llama.cpp).

This matters: most setups assume CUDA. Getting full GPU acceleration on an AMD integrated GPU required working through ROCm limitations and finding the Vulkan path — documented in [`docs/hardware-challenges.md`](docs/hardware-challenges.md).

Models in use:
- `llama3.2:3b` — router and critique nodes (fast, low cost)
- `llama3.2:3b` — task node (same for now, swappable via env var)
- `nomic-embed-text` — embeddings for Qdrant

---

## Repository Structure

```text
agent-infra-stack/
├── docker-compose.yml        # Postgres, Redis, Qdrant, Langfuse, API, Worker
├── shared/                   # Pydantic schemas shared between API and Worker
├── api/                      # FastAPI gateway
│   ├── main.py
│   ├── celery_app.py
│   └── routers/tasks.py
├── worker/                   # Celery + LangGraph
│   ├── graph.py              # Graph definition and loop logic
│   ├── agents/               # router, research, critique, output nodes
│   └── memory/               # short_term (Postgres) + long_term (Qdrant)
├── infra/                    # DB init scripts
├── scripts/                  # Model pulling, smoke tests
└── docs/                     # Architecture decisions, challenges, benchmarks
```

---

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md)

---

## Documentation

| Doc | Content |
|---|---|
| [`docs/roadmap.md`](docs/roadmap.md) | Build plan and progress |
| [`docs/production-strategy.md`](docs/production-strategy.md) | Cloud-native design, scalability and resilience architecture |
| [`docs/architecture-decisions.md`](docs/architecture-decisions.md) | Why each tech was chosen |
| [`docs/hardware-challenges.md`](docs/hardware-challenges.md) | AMD iGPU + Vulkan setup journey |
| [`docs/benchmarks.md`](docs/benchmarks.md) | Real numbers — tokens/sec, latency per node |

---

<div align="center">
  Made with ❤️ by <a href="https://github.com/leonardopolicarpo">Leonardo Policarpo</a>
</div>