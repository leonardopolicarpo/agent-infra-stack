# 006 — Graph Skeleton (State Machine)

**Data:** 2026-04-25
**Status:** concluído

## O que foi feito

Com a infra de execução (Worker + Celery) validada, implementei o "cérebro" do agente.
O foco não foi a inteligência (LLM) ainda, mas a orquestração do fluxo de dados
e a lógica de repetição (loops).

Arquivos criados/alterados:
- `worker/graph.py` — definição do `StateGraph`, nós, arestas e lógica condicional.
- `worker/tasks.py` — integração do ponto de entrada do worker com a invocação do grafo.

## Decisões tomadas

**Desenvolvimento via "Stubs" (Mocks)** — Os nós (`router`, `research`, etc.)
foram criados como funções puras que apenas manipulam o dicionário de estado.
Isso permite validar toda a arquitetura de roteamento e a máquina de estados sem
gastar tokens ou processamento de GPU. Se o fluxo está certo com mocks,
trocar pela IA é apenas um detalhe de implementação.

**Arestas Condicionais para Loops de Refinamento** — O uso de `add_conditional_edges` no
nó de `critique` é o que transforma o script linear em um agente cíclico.
A lógica decide se o output está pronto ou se deve voltar para o nó de pesquisa.

**Controle de "Hard Stop" no Grafo** — Implementada uma verificação de segurança no roteador condicional.
Se o agente entrar em loop infinito por falha de convergência da IA, o grafo força a saída após 3 iterações.
Em sistemas autônomos, o "prejuízo" de uma resposta ruim é menor que o custo de um loop infinito.

**Mapeamento de Contrato no Entry Point** — O worker recebe um `TaskInput` (Pydantic) e precisa
converter para um `AgentState` (TypedDict). Essa tradução ocorre no `tasks.py`, garantindo que o grafo
seja agnóstico à forma como a task chegou (se via API, CLI ou outro worker).

## Ciclo de vida da execução (LangGraph)

```text
[ START ] 
    │
    ▼
[ Nó: Router ] ──► Decide se a tarefa exige pesquisa (complex)
    │
    ▼
[ Nó: Research ] ◄──┐ (Loop de Refinamento)
    │               │
    ▼               │
[ Nó: Critique ] ───┘ Se "NEEDS_REVISION"
    │
    ▼ Se "APPROVED" ou Max Iterations
    │
[ Nó: Output ] ──► Formata a resposta final
    │
    ▼
[ END ]
```

## Problemas encontrados

**Persistência do Estado Final** — O LangGraph retorna o estado completo após o `invoke()`.
Foi necessário garantir que o `tasks.py` extraísse especificamente o `final_output` para
salvar no Postgres, evitando poluir o banco de dados com metadados internos do grafo que
pertencem apenas ao ciclo de vida da execução.

## Próximo passo (Phase 4)

- Implementação do nó de `router` com Ollama (`llama3.2:3b`).
- Sistema de prompts para classificação de intenção.