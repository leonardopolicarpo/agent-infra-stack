# 009 — Agent Nodes: Critique

**Data:** 2026-04-28
**Status:** concluído

## O que foi feito

Implementação do nó de critique com IA real — o avaliador do grafo.
É ele que decide se o research foi bom o suficiente ou se precisa de revisão,
transformando o pipeline linear num agente cíclico de verdade.

Arquivos criados/alterados:

- `worker/agents/critique.py`
- `worker/graph.py` — utilização do critique criado

## Decisões tomadas

**Sempre `ROUTER_MODEL` (modelo leve)** — critique é julgamento, não criação.
Não precisa de criatividade, só de consistência. Usar o modelo leve aqui
reduz custo e latência sem perda de qualidade na avaliação.

**Output controlado: `APPROVED` ou `NEEDS_REVISION: [motivo]`** — o
`route_after_critique` depende desse formato. O system prompt é explícito:
"start your reply with APPROVED or NEEDS_REVISION". Qualquer output fora
do padrão cai no fallback pra `APPROVED`, segurança contra loop infinito
por falha de parsing.

**`temperature=0`** — mesma lógica do router. Avaliação é determinística.
O modelo deve chegar à mesma conclusão dado o mesmo input.

**Critérios explícitos no system prompt** — relevância, completude, clareza
e precisão. Sem critérios explícitos o modelo avalia de forma vaga e inconsistente.
Com critérios, o feedback de `NEEDS_REVISION` vem com motivo específico,
o que o research vai usar pra melhorar na próxima iteração.

## Resultado: impacto imediato e brutal

Mesmo prompt, antes e depois do critique real:

```text
                  Stub          Real
─────────────────────────────────────
Tempo total       91.2s         43.1s
Iterações         2             1
Qualidade         boa           boa
─────────────────────────────────────
Redução           —             -53%
```

O critique aprovou na primeira iteração — a resposta do research já estava
boa o suficiente. O stub forçava sempre 2 iterações independente da qualidade.
Com IA real, iterações desnecessárias não acontecem.

**Breakdown do teste com critique real:**
```text
Router      ~5s    (classificou: complex)
Research 0  ~33s   (gerou resposta inicial)
Critique    ~5s    (avaliou: APPROVED)
Output      <1ms   (stub)
─────────────────
Total       ~43s
```

## Qualidade da resposta — 3b surpreende

A resposta aprovada pelo critique estava bem estruturada:
seções claras, bullet points, comparativo direto, conclusão objetiva.
Um modelo de 3B parâmetros, rodando 100% em iGPU AMD via Vulkan,
entregando output de qualidade num pipeline multi-agente completo.

## O que muda com modelos maiores

Com `TASK_MODEL` apontando pra um 7b ou 8b quantizado:
- Qualidade do research sobe significativamente
- Critique provavelmente aprova mais rápido (menos revisões)
- Tempo por iteração aumenta, mas iterações totais caem
- Tradeoff documentado nos benchmarks quando disponível

## Output Node

Último nó da Phase 4 — sem LLM, sem complexidade.

Recebe o `research_output` aprovado pelo critique e entrega limpo.
Os prefixos de debug (`FINAL ANSWER:`, `(Approved)`) foram removidos,
eram úteis com stubs, mas poluem a resposta real.

Decisão consciente de não chamar o modelo aqui: o research gerou,
o critique aprovou, o output só formata. Custo zero, latência zero.

## Próximo passo

- Após output: fase 5 — memória (short-term + long-term)