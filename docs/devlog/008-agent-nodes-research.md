# 008 — Agent Nodes: Research

**Data:** 2026-04-28
**Status:** concluído

## O que foi feito

Implementação do nó de research com IA real, o nó que de fato gera a resposta
para o usuário. É o mais custoso do grafo em tempo e tokens, e o mais impactante
na qualidade do output final.

Arquivos criados/alterados:

- `worker/agents/research.py`
- `worker/graph.py` — utilização do research criado

## Decisões tomadas

**Seleção dinâmica de modelo via `router_decision`** — o router já classificou
a complexidade da tarefa. O research usa essa decisão:
- `simple` → `ROUTER_MODEL` (3b, rápido e barato)
- `complex` → `TASK_MODEL` (configurável, pode ser um modelo maior)

Trocar o modelo de tarefa é só alterar a env var `TASK_MODEL`, zero mudança de código.

**Contexto de revisão injetado nas iterações subsequentes** — se `iterations > 0`,
o research recebe o output anterior como `assistant` e a crítica do critique como
novo `user`. O modelo sabe o que gerou antes e o que precisa melhorar.
Sem isso, cada iteração seria independente, sem aprendizado entre ciclos.

**`temperature=0.7`** — diferente do router (temperature=0), o research precisa
de alguma criatividade para gerar respostas ricas. 0.7 é um equilíbrio entre
coerência e variedade. O router classifica, o research cria.

## Primeiro teste com IA real no research

**Prompt:** *"What are the main differences between transformer and state space
models like Mamba for sequence modeling?"*

**Resultado:**
- Router: `complex` ✅
- Iteração 0: resposta inicial gerada (~36s)
- Critique stub: forçou `NEEDS_REVISION` sem enviar feedback real
- Iteração 1: revisão gerada (~39s)
- Critique stub: forçou `APPROVED`
- Total: **91.2 segundos**

**Breakdown de tempo:**
```text
Router      ~10s   (1 chamada ao Ollama)
Research 0  ~36s   (geração inicial)
Research 1  ~39s   (revisão)
Critique     <1ms  (stub)
Output       <1ms  (stub)
─────────────────
Total       ~91s
```

## O "auto-critique" involuntário

O fenômeno mais interessante do teste: o critique stub não enviou nenhum
feedback real, apenas disparou o gatilho de revisão (`NEEDS_REVISION`).
Mesmo assim, o Llama 3.2 3b produziu isso na iteração 1:

> *"I have revised my response to address the critique by:*
> *Providing a clearer structure and organization,*
> *Using more concise language and bullet points for easier reading..."*

O modelo **alucionou a crítica**. Como não recebeu feedback concreto, inventou
o que provavelmente estava errado na primeira versão e se corrigiu com base nisso.
Por acidente, funcionou, a segunda resposta ficou visivelmente mais estruturada.

Isso revela dois comportamentos importantes do modelo:
1. Ele é sensível ao contexto de revisão mesmo sem feedback explícito
2. O instruction-tuning do Llama inclui padrões de auto-avaliação que emergem
   quando o contexto sugere revisão

Quando o critique real entrar (próximo nó), o feedback vai ser concreto,
e a qualidade da revisão deve melhorar significativamente.

## Próximo passo

- `worker/agents/critique.py` — avaliação real com Ollama
- Com critique real, o "auto-critique" involuntário vira auto-critique deliberado