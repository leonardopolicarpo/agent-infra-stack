# Contexto e Motivações

## Por que esse projeto existe

Trabalho com IA há um tempo - RLHF, otimização de modelos, pipelines de treinamento.
O problema é que boa parte do que faço não pode ser divulgado. Então decidi construir
projetos do zero, públicos, que demonstre na prática e já com a intenção
real de evoluir isso pra produção em seguida.

Não é um projeto de estudo. É um projeto que começa como portfolio e termina rodando.

## O que eu queria demonstrar

Muitos dos projetos de agentes é um script ou um conjunto deles em Python, monolítico
com LangChain e uma chamada pra API da OpenAI, algum modelo local.
Funciona, mas não escala e não reflete como sistemas de IA funcionam em produção.

Minha ideia aqui foi: separar as camadas desde o início.
O modelo não sabe da fila. A fila não sabe da memória. A API não espera o agente terminar.
Cada peça pode escalar de forma independente. Gosto sempre de pensar em escalabilidade
desde o ínicio, pois a ideia era simular isso mesmo.

## Por que essa stack

Fiz uma pesquisa antes, nenhuma decisão foi por acaso: Cada decisão tem um motivo:

**FastAPI** — assíncrono por natureza, ideal pra um gateway que só enfileira e responde.
Não faz sentido bloquear uma thread esperando um agente que pode levar minutos.

**Celery + Redis** — fila de tarefas battle-tested. O `task_acks_late` garante que nenhuma
task se perde se o worker cair no meio da execução. Simples, confiável e conhecido pelo mercado.

**LangGraph** — grafos cíclicos com checkpointing nativo. O agente pode ser interrompido
e retomado exatamente de onde parou. Isso não é detalhe, é o que separa um sistema robusto
de um que perde estado a cada falha.

**PostgreSQL** — para os checkpoints do LangGraph e para o ciclo de vida das tasks.
Relacional, confiável, sem surpresas.

**Qdrant** — memória semântica de longo prazo. O agente não começa cada task do zero,
ele consulta o histórico relevante antes de executar. RAG sobre as próprias interações passadas.

**Langfuse (self-hosted)** — observabilidade real. Não dá pra otimizar o que você não mede.
Custo de tokens por nó, latência por step, decisão do roteador; tudo visível.

**Ollama** — inferência local com API compatível com OpenAI (muito usada no mercado).
Troca de modelo sem tocar código.

## O hardware

Ryzen 5 5600G. Vega 7 integrada. 16GB de RAM compartilhada entre CPU e GPU.

Não é um servidor com A100. Foi uma escolha consciente mostrar
que dá pra construir infraestrutura sem depender de hardware caro.

O caminho não foi trivial, ROCm não suporta oficialmente iGPUs AMD, o vLLM estava fora
de questão sem CUDA. A solução foi o backend Vulkan do llama.cpp via Ollama.
100% GPU. Documentado em `hardware-challenges.md`.

## Pra onde vai

Essa é a primeira camada. O objetivo depois é explorar arquiteturas além do transformer
no mesmo hardware limitado — MoE, TTT, LFM. Ver o que roda bem, o que não roda,
e documentar tudo com números reais.