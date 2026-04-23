# 004 — Infra Fixes: Langfuse

**Data:** 2026-04-23
**Status:** concluído

## O que foi feito

Após subir o Compose completo pela primeira vez, o Langfuse ficou em restart loop.
Investigação via `docker logs aas_langfuse` revelou dois problemas distintos,
resolvidos em sequência.

## Problemas encontrados

**Langfuse v3 requer ClickHouse**
O Langfuse v3 migrou o armazenamento de traces pro ClickHouse por questões de
performance em escala. Isso não estava na documentação que havia consultado inicialmente.
O erro era claro: `CLICKHOUSE_URL is not configured`.

O ClickHouse é 'pesado', imagem de ~1GB, consumo de RAM significativo em idle.
Num setup com 16GB compartilhados entre CPU e iGPU, não faz sentido.
Decisão: downgrade para Langfuse v2, que funciona só com Postgres.
Para portfolio, v2 entrega tudo que preciso: traces, custo de tokens, latência por nó.

**Schema do Postgres não estava vazio**
Após o downgrade pra v2, novo erro: `P3005 - The database schema is not empty`.
O Prisma do Langfuse exige banco limpo para rodar as 271 migrations iniciais.
O problema: o `init.sql` do projeto já criava as tabelas (`tasks`, triggers)
antes do Langfuse tentar migrar, então o banco nunca estava vazio.

Solução: banco separado para o Langfuse (`langfuse_db`) criado via `init.sql`,
enquanto o projeto continua usando o `agent_db`.
Cada serviço com seu próprio banco, com isso, menos acoplamento, migrations isoladas.

## Decisões tomadas

**Langfuse v2 em vez de v3** — suficiente pro portfolio, sem overhead do ClickHouse.
Quando o projeto for pra produção real com volume de traces alto, a migração pra v3
faz sentido. Por enquanto, v2 + Postgres resolve.

**`langfuse_db` separado do `agent_db`** — decisão que deveria ter sido tomada
desde o início. Misturar schemas de serviços diferentes no mesmo banco é má prática
independente do ambiente.

**Remoção do `langfuse-worker`** — serviço exclusivo da v3, não existe na v2.
E o container órfão removido com `--remove-orphans`.

## Próximo passo

Agora sim: Worker — Celery + LangGraph (Phase 3 do roadmap).