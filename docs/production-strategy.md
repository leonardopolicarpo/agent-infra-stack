# Arquitetura de Produção e Escalabilidade

**Status:** Rascunho / Vivo
**Objetivo:** Documentar o design do sistema, as garantias de resiliência e as estratégias de migração de ambiente (Local ↔ Cloud ↔ Bare Metal).

## 1. Visão Geral: "Local by Choice, Cloud-Native by Design"

Embora o ambiente de desenvolvimento e testes deste projeto utilize recursos limitados (hardware local, iGPU AMD Vega 7 via Vulkan), a arquitetura foi desenhada com princípios de sistemas distribuídos **Cloud-Native**. Não há estado (state) preso à memória de aplicação. Cada componente é efêmero e substituível.

O sistema é construído em camadas estritas:
1. **API Gateway (Stateless):** Recebe, enfileira e responde. Não aguarda inferência.
2. **Message Broker:** Garante a entrega e o enfileiramento das tarefas.
3. **Workers (Consumers):** Consomem a fila, orquestram o grafo de IA e salvam o estado.
4. **Persistência / Memória:** Bancos de dados relacionais e vetoriais para estado e contexto.

## 2. Resiliência e Tolerância a Falhas

Em sistemas baseados em LLMs, a inferência é o gargalo de tempo e custo. Falhas de rede ou de hardware durante uma geração não podem resultar em perda de dados ou processamento duplicado desnecessário.

*   **Idempotência e Fila Segura:** O Celery está configurado com `task_acks_late=True` e `worker_prefetch_multiplier=1`. O worker só confirma a tarefa ao broker *após* a persistência final no banco. Se o container do worker for "morto" (OOM kill, spot instance interruption), a tarefa volta para a fila intacta.
*   **Checkpointing de Estado (LangGraph):** O ciclo de vida do agente não é linear. Utilizando o `PostgresSaver`, o estado do agente é salvo a cada transição de nó (`router` -> `research` -> `critique`). Se houver um *crash* no nó de `critique`, o worker substituto retomará a partir dali, com o contexto anterior carregado do banco de dados, sem precisar re-consultar a LLM para o `research`.

## 3. Estratégias de Deploy e Escala

A infraestrutura atual em `docker-compose` traduz-se diretamente para ambientes de produção.

### Opção A: Managed Cloud (AWS / GCP)
A migração para a nuvem exige **zero alterações no código Python**, apenas injeção de novas variáveis de ambiente.

| Componente Interno | AWS Equivalente | GCP Equivalente | Motivo da Migração |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | Amazon RDS / Aurora | Cloud SQL | Backups automatizados, Multi-AZ. |
| **Redis** | Amazon ElastiCache | Memorystore | Alta disponibilidade do broker. |
| **Qdrant** | Qdrant Cloud | Vertex Vector Search | Escala elástica de embeddings. |
| **FastAPI / Celery**| ECS Fargate / EKS | GKE / Cloud Run | Auto-scaling baseado em CPU/Fila. |
| **Ollama (Modelos)** | SageMaker / Bedrock | Vertex AI Models | Acesso a aceleradores (A100/H100) ou SaaS. |

### Opção B: Bare Metal / Servidores Próprios (Self-Hosted)
Para cenários de total privacidade de dados ou controle estrito de custos de hardware (FinOps).
*   **Process Management:** Substituição do Docker pelo `systemd`. A API e os Workers rodam em ambientes virtuais isolados (`uv`), gerenciados pelo sistema operacional com auto-restart.
*   **Performance Tuning:** Uso de `gunicorn` com `uvicorn` workers para a API tirar proveito de múltiplos núcleos. No Celery, ajuste do pool de concorrência baseado nas threads reais da CPU dedicada, evitando *context switching* excessivo.

## 4. Observabilidade (SRE Mindset)

Não basta o sistema funcionar, ele precisa ser auditável e mensurável.

*   **Tracing de LLM (Langfuse):** Cada execução do LangGraph gera um trace. Monitoro a latência exata de cada nó, o custo de tokens em tempo real e as decisões de roteamento. Isso permite otimizar prompts (ex: se o nó de `critique` reprova 80% das vezes na primeira iteração, o prompt de `research` precisa de ajustes).
*   **Métricas de Fila (Flower):** Monitoramento do *backlog* de tarefas e da saúde dos workers Celery.
*   **Health Checks Ativos:** O endpoint `/health` não é estático. Ele realiza "ping" real no Postgres e no serviço de inferência antes de reportar 200 OK ao Load Balancer.

## 5. Trade-offs e Decisões de Engenharia (ADRs)

*   **Por que Celery + Redis e não Kafka ou RabbitMQ?** Para o volume atual e natureza do processamento de LLMs, o Kafka traria um *overhead* operacional desnecessário. O Celery é nativo do ecossistema Python, maduro, e o Redis atua perfeitamente como broker in-memory rápido para este escopo.
*   **Por que Postgres para Checkpoints do LangGraph e não o próprio Redis?** O estado de um agente de IA pode se tornar um documento JSON complexo (histórico longo de mensagens). O Postgres oferece durabilidade rígida (ACID) e a possibilidade futura de realizar *queries* analíticas sobre os estados passados do agente, o que o Redis (focado em key-value em memória) dificultaria a longo prazo.