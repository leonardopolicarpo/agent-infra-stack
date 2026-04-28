# 007 — Agent Nodes: Router

**Data:** 2026-04-28
**Status:** concluído

## O que foi feito

Com o grafo validado via stubs, hora de plugar IA de verdade no primeiro nó.
O router foi escolhido como ponto de partida por ser o mais crítico arquiteturalmente:
é ele que decide qual modelo vai ser usado nos próximos nós, e consequentemente
o custo e a latência de cada execução.

Arquivos criados/alterados:

- `worker/agents/router.py` — classificação de complexidade via Ollama
- `worker/graph.py` — utilização do router criado

## Decisões tomadas

**System prompt em inglês** — modelos instruction-tuned respondem de forma mais
consistente em inglês, especialmente para tarefas de classificação com output
controlado. O prompt do usuário pode ser em qualquer idioma, o router classifica
independente disso.

**Output controlado: apenas "simple" ou "complex"** — o modelo tem tendência
a adicionar pontuação, explicações ou variações ("Complex.", "it's complex").
O `strip().lower()` normaliza, e o fallback pra `"complex"` garante que qualquer
resposta inesperada vai pro caminho mais seguro, uma vez que é melhor processar
como complexo do que ignorar uma tarefa que precisava de atenção.

**`temperature=0`** — classificação é uma tarefa determinística. Criatividade
zero, consistência máxima. O modelo deve sempre dar a mesma resposta pro mesmo input.

**Instância do LLM dentro do nó, não global** — evita problemas de estado
compartilhado entre workers no modelo prefork do Celery. Cada execução cria
sua própria instância — custo desprezível, segurança garantida.

## Validação end-to-end

Primeiro teste com IA real no grafo. O resultado foi exato:

```text
POST /task {"prompt": "O que é quantização de modelos de linguagem?"}
→ task_id: 25ea37c4-a23b-40ca-9752-524fabeeebc5

Worker logs:
  HTTP Request: POST http://host.docker.internal:11434/api/chat 200 OK
  [ROUTER] decision=complex task=25ea37c4-...
  [NODE] Research executando (iteração 0)   ← stub
  [NODE] Critique avaliando o research      ← stub
  [NODE] Research executando (iteração 1)   ← stub
  [NODE] Critique avaliando o research      ← stub
  [NODE] Output gerando resposta final      ← stub
  Task succeeded in 5.710s

GET /task/25ea37c4-...
→ status: done
→ output: {
    "answer": "FINAL ANSWER: Mocked research for: ..." (stub),
    "decision": "complex",
    "iterations": 2
  }
```

**~5.6s** foram gastos exclusivamente na chamada ao Ollama no router.
Os stubs executaram em milissegundos. Isso vai mudar quando research e critique
também chamarem o modelo, número real estará nos benchmarks.

## Fluxo atual do grafo

```text
[ Router ] ← IA real (llama3.2:3b via Ollama)
    │
    ▼
[ Research ] ← stub
    │
    ▼
[ Critique ] ← stub
    │
    ▼ APPROVED (após 2 iterações forçadas)
    │
[ Output ] ← stub
```

## Próximo passo

- `worker/agents/research.py` — geração de resposta real com Ollama
- Modelo selecionado dinamicamente pelo `router_decision` (simple → 3b, complex → task model)