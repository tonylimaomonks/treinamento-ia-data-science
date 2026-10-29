# CLAUDE.md alvo · como a sessão deve ficar ao fim do Ato 0

O `/init` gera a parte de cima: o contexto da demanda, a partir do `PEDIDO.md`. O bloco **"Regras de trabalho do time"** abaixo é colado pelo Tony no prompt 0.5 do roteiro. É ele que transforma um `CLAUDE.md` genérico no jeito de trabalhar da área.

---

## Regras de trabalho do time (colar no prompt 0.5)

```markdown
## Regras de trabalho (não negociáveis)
1. **Custo primeiro:** toda query nova roda antes com `--dry_run`. Queries reais sempre com `--maximum_bytes_billed=1000000000` (1 GB).
2. **Nunca inferir enum a partir de amostra.** Para saber quais valores uma coluna assume, rode um "bloco 0" (`SELECT col, COUNT(*) ... GROUP BY`) na tabela real.
3. **Não cravar mecanismo sem dado intermediário.** Toda hipótese vem com o teste que a refutaria. Se o teste refutar, registre a refutação.
4. **Cada iteração de query é um arquivo novo** em `queries/` (`q01_recon.sql`, `q02_bloco0_utm.sql`...). O resultado vai para `results/`, com o mesmo basename (`q01_recon.csv`).
5. **Nunca transcrever número à mão** no relatório: CSV → `relatorio/gen_data.py` → JSON → `const D` no HTML.
6. **Não misturar réguas:** conversão web e app comparadas na mesma atribuição (último clique por campanha, nas duas pontas).
7. **Materializar os dados:** toda análise deixa CSV no grão fino, JSON agregado e um README curto.
8. **Nada destrutivo:** proibido `bq rm` e `DROP` fora de `trama_silver`/`trama_gold`.
9. **Escopo de dados:** só os datasets listados no `PEDIDO.md`.
10. **Entrega nova começa pelas boas práticas:** antes de planejar o caderno, o HTML executivo ou a dash, leia o arquivo correspondente em `estudos/`. O plano cita a prática que sustenta cada decisão. Se `estudos/` não cobrir o tema, pesquise com fonte (link) antes de planejar.
11. **Três entregas, três públicos:** o caderno da investigação é para nós (técnico e visual). O HTML executivo é para o cliente: abre com a decisão e o impacto em verba, sem jargão. A dash é o acompanhamento diário, com um bloco por problema monitorado, e é testada com `streamlit.testing.v1.AppTest` antes da entrega.
12. **Caderno da investigação:** `investigacao/caderno.html` cresce a cada achado, com uma seção por hipótese: a pergunta, o arquivo da query, o resultado em gráfico ou tabela, o teste que refutaria e o veredito (CONFIRMADA / REFUTADA / PARCIAL). Os números vêm dos CSVs de `results/`, e `investigacao/build.py` regera o HTML inteiro a cada atualização.
13. **Modelos:** a sessão principal roda no Opus, que orquestra, planeja e sintetiza. Todo subagente é lançado com o modelo Sonnet, a não ser que eu peça outro.

## Convenções de modelagem
- Mídia paga: `REGEXP_CONTAINS(LOWER(medium), r'(^|[,_])(cpc|cpm|ppc|paid)([,_]|$)')`.
- Source canônico: dicionário explícito (ex.: `fb`/`ig`/`facebook`/`instagram`/`meta` → `meta`). O `else` cai em `unassigned`, que é monitorável.
- CPA/ROAS são **medidas agregadas** (`SUM(spend)/NULLIF(SUM(conv),0)`), nunca média de razões.
- Join spend × conversão por `date + campaign_name` é `FULL OUTER`, com `match_status` (`matched` / `spend_only` / `conv_only`). A cobertura se mede **por verba**, não por número de campanhas.
```

---

## Permissões (prompt 0.6) → `.claude/settings.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(bq ls:*)", "Bash(bq show:*)", "Bash(bq head:*)", "Bash(bq query:*)",
      "Bash(python3:*)", "Bash(mkdir:*)", "Bash(streamlit run:*)",
      "WebSearch", "WebFetch"
    ],
    "deny": ["Bash(bq rm:*)", "Bash(gcloud projects delete:*)"]
  }
}
```

Ponto a explicar: `settings.json` é do **time** (vai para o repo), e `settings.local.json` é **pessoal**. A trava que impede a sessão de ler `preparacao/` mora no `settings.local.json` da sessão, que já vem pronto.

## Memória (prompt 0.7) → auto memory da sessão

O Claude deve salvar, na auto memory do projeto (`~/.claude/projects/<pasta>/memory/`):
- o projeto GCP e os datasets de leitura e escrita;
- o prazo (quinta, fim do dia) e o comitê (sexta);
- depois do prompt J1: **a key do card no Jira**. É ela que permite fechar o card no fim, depois de dois `/clear`.
