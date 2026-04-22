# 003 — API Gateway

**Data:** 2026-04-22
**Status:** concluido

## O que foi feito

Construção da camada de entrada do sistema. A API não processa nada —
ela recebe, persiste e delega. Essa separação é intencional.

Arquivos criados:

- `api/config.py` — settings via pydantic-settings, defaults funcionam sem `.env`
- `api/celery_app.py` — configuração do Celery com broker e backend Redis
- `api/routers/tasks.py` — `POST /task` e `GET /task/{id}`
- `api/routers/health.py` — `GET /health` com verificação real de Postgres e Ollama
- `api/main.py` — aplicação FastAPI com lifespan e registro de routers
- `api/Dockerfile` — build com uv, context definido na raiz do projeto

## Decisões tomadas

**`config.py` por serviço, não global** — API e Worker rodam em containers separados
com dependências próprias. Um `config.py` na raiz seria acoplamento desnecessário.
Cada serviço sabe apenas o que precisa saber.

**`task_acks_late=True` no Celery** — a task só é confirmada como recebida após
o worker terminar de processá-la. Se o worker cair no meio, ela volta automaticamente
para a fila. Sem isso, uma falha no worker significa task perdida silenciosamente.

**`worker_prefetch_multiplier=1`** — cada worker pega uma task por vez.
Agentes LLM são 'pesados', deixar o worker pegar várias tasks antecipadamente
causaria timeout e contenção de memória.

**`cast(FastAPI, request.app)`** — o `request.app` do Starlette retorna `Any`.
O cast não faz nada em runtime, mas diz ao type checker que `app.state.pool` existe.
Sem isso o linter reclama de acesso a atributo em tipo desconhecido.
Gosto de seguir esse padrão.

**Health check com verificação real** — `/health` não retorna só `{"status": "ok"}`.
Verifica ativamente o Postgres (`SELECT 1`) e o Ollama (`/api/tags`).
Um health check que não verifica nada é só ruído. (auto crítica)

**`redirect_slashes=False` no FastAPI** — por padrão o FastAPI redireciona
`/task` para `/task/` com 307. Desabilitar evita que o curl e outros clientes
percam o body do POST no redirect.

**Commits atômicos por responsabilidade** — cada arquivo foi um commit separado
com mensagem no padrão conventional commits. O histórico do repositório
conta a história do desenvolvimento.

## Problemas encontrados

**Build context do Dockerfile** — `COPY ../shared` não funciona no Docker
porque o build context não permite navegar pra fora do diretório.
Solução: definir `context: .` no Compose e ajustar os caminhos no Dockerfile
para `COPY api/` e `COPY shared/`.

**`uvicorn` não encontrado no container** — o `uv sync` instala no `.venv`
local mas o CMD chamava `uvicorn` direto sem ativar o venv.
Solução: usar `.venv/bin/uvicorn` no CMD do Dockerfile.

**`celery[redis]` faltando** — o Celery instalado sem o extra `[redis]` não
inclui o `redis-py`, que o kombu precisa para conectar ao broker.
`AttributeError: 'NoneType' object has no attribute 'Redis'` foi o sintoma.
Solução: `uv add "celery[redis]"`.

**Ollama inacessível pelo container** — o Ollama escutava só em `127.0.0.1`,
invisível para o Docker. Solução: adicionar `OLLAMA_HOST=0.0.0.0` no
`override.conf` do systemd e reiniciar o serviço.

**Porta 5432 já alocada** — container órfão de sessão anterior segurava a porta.
Solução: `docker compose down` libera as portas. E alteração pora 5443.
Porta default estava alocada em outro projeto.

## Próximo passo

Worker — Celery + LangGraph (Phase 3 do roadmap).