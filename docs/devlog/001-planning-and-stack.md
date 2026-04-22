# 001 — Planejamento e Definição da Stack

**Data:** 2026-04-18
**Status:** concluído

## O que foi feito

Ponto de partida: eu queria um projeto público que demonstrasse infraestrutura de IA,
já que o que faço no dia a dia não pode ser divulgado, seja trabalho e projetos pessoais.
A ideia não era criar apenas mais um chatbot com LangChain, mas queria era construir
algo que refletisse como sistemas de IA funcionam em produção.

Comecei pesquisando o que o mercado estava pedindo para vagas de AI/ML Engineer.
O padrão que apareceu: RAG, agentes, orquestração, serving. Mas a dor real das empresas
é infraestrutura, e foi aí que decidi o foco desse primeiro projeto.

Nessa etapa do processo, um dos momentos que utilizo IA, quis validar a direção e explorar possibilidades de arquitetura.
A sugestão inicial era boa conceitualmente, mas precisava de ajustes, especialmente
em relação ao hardware.

## Decisões tomadas

**vLLM fora do escopo inicial** — sem CUDA, sem vLLM. Simples assim.
Meu hardware é um Ryzen 5 5600G com Vega 7 integrada. ROCm não suporta oficialmente
iGPUs AMD, então o caminho foi o backend Vulkan do llama.cpp via Ollama.
Resultado: 100% GPU na iGPU. Documentado em breve em `hardware-challenges.md`.

**Ollama no host, não no Docker** — passthrough de iGPU AMD para container Docker
no Linux com Vulkan é frágil, inclusive fiz testes. Ollama roda no host com acesso total à GPU,
o Compose aponta para `host.docker.internal:11434`. Zero perda de performance e
zero dor de cabeça

**Microserviços desde o início** — sem script monolítico. API, Worker e Engine
são camadas separadas que podem escalar independentemente.

**Stack definida:**
- FastAPI — gateway assíncrono
- Celery + Redis — fila de tarefas com garantia de entrega
- LangGraph — orquestração com checkpointing nativo
- PostgreSQL — estado das tasks + checkpoints do LangGraph
- Qdrant — memória semântica de longo prazo
- Langfuse (self-hosted) — observabilidade de produção
- Ollama (Vulkan) — inferência local

## Problemas encontrados

Nenhum bloqueante nessa fase, foi planejamento apenas. Os problemas reais
vêm quando a infra sobe haha

## Próximo passo

Criar o repositório, escrever o README inicial e o roadmap.

> ps: as datas refletem a data que eu executei cada fase e nao do commit