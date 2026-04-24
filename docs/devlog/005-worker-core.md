# 005 — Worker Core

**Data:** 2026-04-24
**Status:** em andamento

## O que foi feito até agora

Com a API Gateway validada e a infra estável, início da construção do Worker,
que é a camada que de fato executa o agente.

Arquivos criados até o momento:

- `worker/config.py` — settings próprios do worker via pydantic-settings
- `worker/celery_app.py` — instância Celery separada da API
- `worker/tasks.py` — entry point com ciclo de vida completo da task

## Decisões tomadas

**`worker/config.py` separado do `api/config.py`** — cada serviço conhece apenas
o que precisa. O worker não precisa saber de `POSTGRES_URL` com `asyncpg`,
ele usa `psycopg` síncrono. A API não precisa saber de `ROUTER_MODEL` ou `QDRANT_URL`.
Nenhum acoplamento entre serviços.

**`pyproject.toml` único na raiz** — em produção real cada serviço teria seu próprio
`pyproject.toml` com deps isoladas e imagens menores. No momento, um único arquivo
na raiz simplifica o desenvolvimento sem custo real pro portfolio. Quando for pra
produção, separar é a evolução natural, e será documentado.

**`celery_app` separado em arquivo próprio** — evita importação circular entre
`tasks.py` e a configuração do Celery. O `tasks.py` importa de `.celery_app`,
não define a instância ele mesmo.

**`psycopg` síncrono no worker** — Decisão arquitetural baseada em três pontos:
- **Incompatibilidade de modelo:** Celery usa prefork pool nativamente, não um event loop.
- **Complexidade acidental:** Usar asyncpg exigiria instanciar event loops manualmente
(asyncio.run()) dentro da task, gerando boilerplate e dificultando o pooling de
conexões no Postgres.
- **Falso ganho:** A task é essencialmente bloqueante (vai aguardar a inferência/resposta
da IA). Liberar o thread do banco de forma assíncrona não libera o worker process.
O psycopg3 síncrono é a ferramenta certa pro ecossistema certo.

**`bind=True` no decorator da task** — necessário para acessar o contexto da task via self
e habilitar o uso do self.retry(). Isso viabiliza o uso de backoff nas retentativas.
Em vez de metralhar o sistema tentando rodar a task de novo imediatamente após um erro,
o backoff introduz um atraso inteligente (ex: falhou agora, tenta em 5 segundos; falhou de novo,
tenta em 10). Isso aumenta a resiliência do nosso worker.

**`max_retries=2` com `countdown=5`** — se o agente falhar, tenta mais 2 vezes
com 5 segundos de espera entre tentativas. Evita retry instantâneo que
provavelmente falharia pelo mesmo motivo.

**TODO intencional no `tasks.py`** — o grafo LangGraph ainda não existe.
O placeholder `"worker reached — graph not implemented yet"` permite testar
o ciclo de vida completo (`pending → running → done`) antes de adicionar
a complexidade do grafo. Cada camada validada antes de adicionar a próxima.

## Ciclo de vida da task

[ Cliente ]
     │
     ▼
  POST /task
     │
     ▼
[ API Gateway ]
     │
     ├──► Postgres: salva task (status = 'pending')
     └──► Redis: enfileira mensagem no broker
            │
            ▼
[ Celery Worker ] consome da fila
            │
            ├──► Postgres: atualiza task (status = 'running')
            │
            ▼
[ Execução do Agente / IA ]
            │
            ├──► SUCESSO:
            │      └──► Postgres: status = 'done', salva output final
            │
            └──► FALHA:
                   ├──► Postgres: status = 'failed', salva log de erro
                   └──► self.retry() com backoff (espera N segundos)
                          └──► Volta para a fila do Redis (até max_retries)

## Próximo passo

- Dockerfile do worker
- Testar ciclo de vida completo com worker rodando
- LangGraph graph skeleton (Phase 3)