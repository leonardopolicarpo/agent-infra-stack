# 010 — Worker Isolation & Per-Task Graph Instantiation

**Data:** 2026-04-29
**Status:** concluído

## O que foi feito

Refatoração da inicialização do LangGraph dentro do ciclo de vida do worker.
A instância compilada do grafo foi removida do escopo global do módulo e movida para
o escopo local da task do Celery. Além da mudança de código, foi feito um estudo
aprofundado sobre concorrência no Celery e protocolos de rede para embasar a decisão.

Arquivos criados/alterados:
- `worker/graph.py` — remoção da instância global `graph = build_graph()`.
- `worker/tasks.py` — instanciação e compilação do grafo localmente dentro da função `run_agent()`.

## Problemas encontrados (Teóricos e Futuros)

**Risco de Contaminação Cruzada (Cross-task Contamination):**
Ao compilar o `StateGraph` globalmente, todos os processos/threads do worker Celery compartilhavam
o mesmo objeto em memória. Embora o LangGraph seja desenhado para ter o estado fluindo através
do `.invoke()`, inicializações globais são um anti-pattern em sistemas concorrentes. Se qualquer
dependência com estado (como uma conexão de banco ou um logger acoplado) fosse introduzida,
teríamos *race conditions* ou vazamento de dados de uma task para outra.

**Incompatibilidade com a Phase 5 (Memória):**
Para introduzir os checkpoints de memória (PostgresSaver), o grafo precisa de um identificador
único de thread. Um grafo global dificultaria o isolamento e o gerenciamento limpo do `RunnableConfig`
para cada execução simultânea.

## Decisões tomadas

**Isolamento de Memória por Task:** 
A chamada `graph = build_graph()` foi movida para o interior do bloco `try` em `run_agent`.
Agora, quando o Celery inicia a task, o grafo nasce, executa, e morre junto com ela,
permitindo que o *Garbage Collector* do Python limpe a memória com segurança.

**Trade-off de Latência aceito:** 
Estudando os bastidores do LangGraph, ficou claro que compilar o grafo é uma operação barata
(basicamente mapeamento de dicionários e validação de TypedDicts). O custo em microssegundos para
instanciar o grafo a cada chamada é totalmente irrelevante frente à latência de 25 segundos
(tempo atual atingido nos últimos testes) da inferência das LLMs, e compensa infinitamente pela
segurança arquitetural.

## Resultado

O worker agora é 100% *stateless* e seguro para escalar verticalmente (aumentando a concorrência
do Celery no mesmo container) sem risco de colisão de dados entre tarefas. A arquitetura agora
está pavimentada para receber persistência de estado.

## Próximos passos

- Iniciar a fase 5 (Memory Layers).
- Implementar o `PostgresSaver` no LangGraph utilizando o próprio `task_id` como `thread_id` para garantir o checkpointing da conversa no banco de dados.