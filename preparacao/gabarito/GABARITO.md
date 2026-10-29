# Gabarito DS-101 — só para o facilitador

> Números reais do setup de 2026-10-20 (`DATA_REF` vazio = dia da execução; janela 2026-07-22 → 2026-10-19). Gerado a partir de `relatorio/results/`.
> Rodou o setup de novo com outra data? Rode `relatorio/rodar_queries.sh` + `gen_data.py` e atualize esta página. Os ASSERTs garantem a história, mas os valores exatos mudam.

**Dash legada (`trama_legacy.vw_dash_growth_resumo`)**

| Canal | Vendas web A → B | Var. | CPA A → B | Var. |
|---|---|---|---|---|
| Meta | 719 → 361 | −50% | R$ 61,78 → R$ 122,24 | **1,98×** |
| Google | 569 → 441 | −22% | R$ 63,28 → R$ 82,15 | +30% |
| TikTok | 187 → 144 | −23% | R$ 80,51 → **R$ 32,31** | −60% |
| Outros | 542 → 564 | +4% | — | — |
| **Total** | **2.017 → 1.510** | **−25,1%** | | |

**Régua unificada (`trama_gabarito.veredito_cpa`: web + app, por campanha, sem os 4 dias quebrados nos dois períodos)**

| Canal | CPA A → B | Var. |
|---|---|---|
| Meta | R$ 52,50 → R$ 54,83 | +4,4% (efeito real pequeno) |
| Google | R$ 44,19 → R$ 42,95 | −2,8% |
| TikTok | R$ 70,34 → R$ 71,79 | +2,1% (o **mais caro**) |

## Os 4 problemas plantados

| # | O que é | Onde aparece | Query que revela |
|---|---|---|---|
| **P1** | 4 dias sem nenhum evento web (23/09, 01/10, 08/10, 16/10); o job ficou `SUCCESS` com 0 linhas, em ~3s | `raw_web_events`, `raw_ingestion_log` | Contagem diária × calendário; ERP × tracking por dia e plataforma |
| **P2** | UTMs do Meta no template novo da agência: `fb/cpc`, `ig/paid_social`, `Facebook/cpc`, `meta/cpc,cpc`. Parâmetro: 25%; observado: 23,4% das compras rastreadas do Meta no último mês (110 de 471) | `raw_web_events` | Bloco 0: `SELECT utm_source, utm_medium, COUNT(*) ... GROUP BY` |
| **P3** | Campanhas `trm_meta_web_*` passaram a converter no app (deep link): 14,9% → 32,5% da conversão. O banner "10% off no app" empurra os outros canais (Google 31% → 39%, TikTok 32% → 39%) | `raw_app_events.campaign` | Casar `campaign_name` entre web e app |
| **P4** | O conector do TikTok manda parte do spend sem `campaign_name` (20% → 75% da verba; R$ 17.863,40 no último mês). O INNER JOIN com o catálogo descarta essa verba: a cobertura do join por verba no último mês é 24,1% | `raw_media_spend` | Cobertura do join **por verba**, e não por número de campanhas |

## Controle positivo (bom momento para ensinar)
O **Google** também "piora" na dash legada (+30% de CPA, −22% de vendas web) sem ter P2 nem P4. Isso mostra que parte da queda é **comum a todos os canais** (P1 + migração pro app) e não é específica do Meta. É o mesmo raciocínio do "controle positivo" que usamos no diagnóstico de FTD.

## Veredito esperado (resposta para a Growth)
> Não cortar. A queda de vendas web e o "CPA dobrado" do Meta são, na maior parte, efeito de medição:
> (1) 4 dias em que o dado web não entrou, apesar do job verde;
> (2) UTMs da agência nova que a dash não reconhece;
> (3) venda que migrou para o app, que a dash não olha.
> Medindo web + app na mesma régua, o CPA do Meta ficou estável (+4,4%). O TikTok só parece barato porque a dash enxerga uma fração pequena da verba dele. Na régua certa, ele é o canal mais caro.
> **Próximos passos:** alerta de volume (e não só de status) na ingestão web; dicionário de UTM com `unassigned` monitorado; dash de Growth passando a somar o app; `campaign_id` no conector do TikTok.

## Cascata (tabela `trama_gabarito.veredito_cascata_meta`)
Degraus acumulados das "vendas web do Meta", do mês anterior até o último mês. Serve de base para o gráfico cascata do HTML executivo.

| Degrau | Vendas web Meta | Δ |
|---|---|---|
| Dash · mês anterior | 719 |  |
| Efeito real (volume Meta) | 667 | −52 |
| P3 · migração pro app | 531 | −136 |
| P1 · dias sem ingestão | 463 | −68 |
| Cobertura normal | 471 | +8 |
| P2 · UTM fora do padrão = Dash · último mês | 361 | −110 |

Leitura: dos −358 da dash, só −52 (15%) são efeito real. O resto é medição: app −136, ingestão −68 e UTM −110, com a cobertura normal do período em +8.
