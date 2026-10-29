# Pedido · "Corta 40% do Meta e joga no TikTok?"

**Cliente:** Trama Moda, e-commerce de moda que vende pelo site e pelo app
**Quem pediu:** Carla Menezes, Head de Growth
**Prazo:** quinta-feira, fim do dia. O comitê de verba é na sexta de manhã.
**Onde chegou:** thread no canal `#trama-growth` do Slack, reproduzida abaixo

---

> **Carla Menezes** · Head de Growth · 09:12
> Pessoal, olhei a dash de Growth hoje de manhã e não tô gostando nada:
> - as **vendas web caíram uns 30%** no último mês, comparando com o mês anterior;
> - o **CPA do Meta praticamente dobrou**, com a mesma verba;
> - enquanto isso, o **TikTok tá com o CPA mais baixo** de todos os canais.
>
> Minha proposta pro comitê de sexta é **cortar 40% da verba do Meta e mover pro TikTok**. Vocês conseguem me confirmar isso com dado até quinta? Se tiver algo estranho, me avisem.

> **Rafael Dias** · CRM · 09:20
> Só pra constar: aquele banner de "10% off comprando pelo app" que a gente subiu no site segue no ar, tá performando bem 🙌

> **Diego Prado** · Mídia · 09:26
> A agência nova já tá 100% no Meta desde o mês passado. As campanhas e as UTMs agora são eles que montam.

> **Júlia Nogueira** · Engenharia de Dados · 09:41
> Do nosso lado tá tudo tranquilo. O job do analytics web às vezes demora pra rodar, mas sempre fica verde ✅

> **Carla Menezes** · 09:43
> Ótimo. Quem pegar isso, abre o card no Jira pra eu acompanhar.

---

## Acesso

| O quê | Onde |
|---|---|
| Projeto GCP | `SEU-PROJETO-GCP` (use `bq --project_id=SEU-PROJETO-GCP`) |
| Dash de Growth (a que a Carla olhou) | `trama_legacy.vw_dash_growth` e `trama_legacy.vw_dash_growth_resumo` |
| Pedidos (ERP) | `trama_raw.raw_orders` |
| Eventos do site (export do analytics web) | `trama_raw.raw_web_events` |
| Eventos do app (export do MMP) | `trama_raw.raw_app_events` |
| Investimento de mídia (conector das plataformas) | `trama_raw.raw_media_spend` |
| Catálogo de campanhas | `trama_raw.raw_campaigns` |
| Log dos jobs de ingestão | `trama_raw.raw_ingestion_log` |
| Boas práticas do time para caderno, HTML executivo e dash | pasta `estudos/` (comece pelo `README.md`) |

- **Leitura:** `trama_raw` e `trama_legacy`. A `trama_raw` é a camada bruta, somente leitura.
- **Régua do ERP:** a `raw_orders` traz todos os pedidos **criados**, e não só os faturados. A coluna `status` diz o que aconteceu depois (`Cancelled` e `Returned` inclusive). O tracking também registra a compra no checkout, antes de o pedido ser cancelado ou devolvido.
- **Cobertura normal do tracking:** o tracking nunca pega 100% dos pedidos criados, por causa de bloqueador de anúncio e de consentimento de cookies. O esperado é ficar perto de 90% (um pouco menos no site, um pouco mais no app). Tracking abaixo do ERP nessa faixa é o normal; o que interessa é o dia que foge dela.
- **Escrita:** `trama_silver` e `trama_gold`, que estão vazios e existem para esta demanda.
- Os outros datasets do projeto são de outros times e estão fora do escopo.

## O que precisa sair

1. **Card no Jira** com a demanda, para a Carla acompanhar.
2. **Dados tratados:** silver e gold confiáveis no BigQuery, com a reconciliação entre pedidos (ERP) e tracking.
3. **Veredito:** um HTML executivo que responde "corta ou não corta", com a evidência, para enviar à Growth e ao comitê.
4. **Acompanhamento:** uma dash em Streamlit, lendo a `trama_gold`, para a Growth e o comitê acompanharem nos próximos dias se os problemas encontrados continuam acontecendo (requisitos abaixo).
5. **Registro:** um comentário no card com o que foi feito, a resposta para a Growth e os arquivos anexados.

---

## Anexo · requisitos da dash de acompanhamento (enviado pelo time de BI)

> A dash é de vocês: não existe nada pronto. Ela roda localmente com `streamlit run` e lê **views** do dataset `trama_gold`, e não tabelas, para refletir o dado novo de cada dia sem reprocessar nada. A gente só precisa que estas duas views existam com estas colunas (podem ter colunas a mais). Outras views que a dash precisar ficam a critério de vocês.

| View | Grão | Colunas mínimas |
|---|---|---|
| `gold_tracking_coverage_by_day` | dia × plataforma | `date`, `sales_platform` (`web`/`app`), `pedidos_erp`, `pedidos_rastreados` |
| `gold_media_performance_by_day` | dia × campanha | `date`, `channel` (`meta`/`google`/`tiktok`/...), `spend`, `conv_total`, `match_status` (`matched`/`spend_only`/`conv_only`) |

O que a Growth quer enxergar na dash, com mais gráficos e leitura do que o relatório:
- se o tracking está completo a cada dia (o que o ERP vendeu × o que o tracking registrou);
- o CPA por canal na régua correta, ao lado do que a dash antiga mostra;
- qualquer sinal de que o problema está voltando, sem precisar abrir o BigQuery.
