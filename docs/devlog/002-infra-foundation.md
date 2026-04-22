# 002 — Fundação da Infraestrutura

**Data:** 2026-04-19
**Status:** concluído

## O que foi feito

Com o planejamento definido, hora de colocar a base no lugar antes de seguir.
A ordem importa: contratos primeiro, infraestrutura depois, e aí código por cima.

Itens concluídos nessa fase inicial:

- `shared/schemas.py` — contratos Pydantic compartilhados entre API e Worker
- `docker-compose.yml` — Postgres, Redis, Qdrant, Langfuse v3, Flower
- `infra/postgres/init.sql` — schema inicial com tabela de tasks e triggers
- `.env.example` — variáveis de ambiente documentadas

Também foi aqui que migrei projeto migrou de `requirements.txt` para `pyproject.toml` com `uv`.

## Decisões tomadas

**`AgentState` como `TypedDict`, não `BaseModel`** — o LangGraph usa `TypedDict`
para inferir o schema do estado do grafo. Com `BaseModel` haveria incompatibilidade
na compilação do grafo. Os contratos de API continuam como `BaseModel`, sendo cada um
no contexto certo.

**Langfuse v3** — a versão anterior usava container único. A v3 separou em
`langfuse` (web + API) e `langfuse-worker` (processamento assíncrono interno).
Ambos dependem de Postgres e Redis — que já estavam no Compose.
Detalhe: o Flower monitora apenas os workers Celery do projeto,
não os workers internos do Langfuse.

**uv em vez de pip** — primeira vez usando. Depois de fazer uma pesquisa sobre
gerenciadores de dependências, optei por ele, pois: Gerencia venv automaticamente,
resolve dependências mais rápido e o `pyproject.toml` é padrão PEP 621.
O `uv.lock` e o `.python-version` (pinado em 3.10) são commitados,
garantindo reprodutibilidade em qualquer ambiente.

**`.env` na raiz, fora do Docker** — o Compose lê automaticamente o `.env`
na mesma pasta do `docker-compose.yml`. O arquivo real fica no `.gitignore`,
o `.env.example` vai pro repo como template.

## Problemas encontrados

Nenhum bloqueante novamente. A única atenção foi verificar as variáveis de ambiente
do Langfuse v3 diretamente na documentação oficial antes de escrever o Compose,
elas mudaram em relação à v2 e qualquer informação desatualizada quebraria
a subida do serviço.

## Próximo passo

API Gateway — FastAPI com os endpoints de submissão e consulta de tasks,
configuração do Celery e Dockerfile.