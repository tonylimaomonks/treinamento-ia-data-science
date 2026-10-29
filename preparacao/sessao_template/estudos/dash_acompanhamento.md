# Boas práticas · dash de acompanhamento e monitoramento

A dash de acompanhamento serve para ver, nos dias seguintes, se um problema voltou a acontecer. Ela é exploratória: tem mais detalhe e mais gráficos que o relatório executivo, e atualiza sozinha. A segunda metade deste arquivo trata da parte técnica de Streamlit sobre BigQuery.

---

## Conteúdo e alertas

**D1 · Organize em pirâmide: KPIs no topo, tendência no meio e detalhe embaixo.**
Regra: o mais importante fica no canto superior esquerdo, porque a leitura segue o padrão em F.
Como aplicar: a primeira linha tem um KPI por problema monitorado. Abaixo, as séries diárias. No rodapé, as tabelas de detalhe.
Fonte: [NN/g, F-Shaped Pattern](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/); [Tableau, Best Practices for Effective Dashboards](https://help.tableau.com/current/pro/desktop/en-us/dashboards_best_practices.htm).

**D2 · Dedique um bloco a cada problema monitorado.**
Regra: cada problema tem seu KPI, seu gráfico, sua tabela de detalhe e sua definição do limiar.
Como aplicar: uma aba ou seção por problema, cada uma com dois ou três gráficos e uma tabela. Cada bloco cobre uma dimensão de qualidade: atualização (freshness), volume, completude ou distribuição.
Fonte: [Monte Carlo, What Is Data Observability? 5 Key Pillars](https://montecarlo.ai/blog-what-is-data-observability).

**D3 · Alerte por volume, não só por status do processo.**
Regra: um processo pode terminar sem erro e ter entregue dado vazio ou errado.
Como aplicar: monitore a razão diária entre o que foi rastreado e o que a fonte da verdade registrou, e dispare o alerta abaixo de um piso. Combine com um teste de atualização (data do último registro).
Fonte: [Great Expectations, expect_table_row_count_to_be_between](https://greatexpectations.io/legacy/v1/expectations/expect_table_row_count_to_be_between/); [Monte Carlo, Catching the bug that never throws an exception](https://montecarlo.ai/blog-catching-the-bug-that-never-throws-an-exception).

**D4 · Reconcilie com a fonte da verdade, com limiar de divergência explícito.**
Regra: todo total importante da dash é comparado com o sistema de origem.
Como aplicar: mostre a cobertura (rastreado dividido por origem) e o piso aceitável. Para joins, meça a cobertura por valor (soma do que casou dividida pela soma total). Acompanhe também a parcela da categoria "não atribuído" do dicionário de canais e defina um teto.
Fonte: [Monte Carlo, Data Reconciliation (comparison monitors)](https://www.montecarlodata.com/blog-comparison-monitors/); [Monte Carlo, Comprehensive Guide to Data Reconciliation](https://montecarlo.ai/blog-data-reconciliation).

**D5 · Use limiares que respeitam a sazonalidade semanal.**
Regra: compare cada dia com o mesmo dia da semana anterior ou com a mediana de quatro a seis semanas.
Como aplicar: evite um número fixo único quando o volume tem padrão de fim de semana. Os valores de piso e teto sugeridos são pontos de partida a calibrar com o dado real. Alerte só quando houver uma ação a tomar.
Fonte: [Monte Carlo docs, Metric Monitors](https://docs.getmontecarlo.com/docs/metric-monitors); [Google SRE Book, cap. 6](https://sre.google/sre-book/monitoring-distributed-systems/).

**D6 · Mostre o status com ícone e texto, além da cor.**
Regra: ok, atenção e falha precisam ser distinguíveis sem enxergar cores.
Como aplicar: use um símbolo e uma palavra ao lado do valor, e diga em uma frase o que fazer quando o status não é ok.
Fonte: [W3C, Understanding SC 1.4.1 Use of Color](https://w3.org/WAI/WCAG22/Understanding/use-of-color.html).

**D7 · Anote os eventos nas séries e ofereça poucos filtros globais.**
Regra: a série com eventos marcados evita explicações falsas, e filtros demais confundem.
Como aplicar: faixas ou linhas nas datas de mudanças conhecidas. Filtros na barra lateral, valendo para todas as abas: período (padrão curto), canal e plataforma.
Fonte: [Datawrapper, What to consider when using text in data visualizations](https://www.datawrapper.de/blog/text-in-data-visualizations); [Looker, Considerations when building performant dashboards](https://cloud.google.com/looker/docs/best-practices/considerations-when-building-performant-dashboards).

**D8 · Calcule indicadores como razão de somas e gere os textos dos mesmos dados.**
Regra: nunca a média de razões diárias, e nunca um número digitado em frase.
Como aplicar: as views expõem numerador e denominador, e a razão é calculada no último passo. As frases de insight saem do mesmo DataFrame do gráfico, com número formatado.
Fonte: [HR Exchange Network, Averaging Ratios and the Perils of Aggregation](https://www.hrexchangenetwork.com/hr-tech/articles/averaging-ratios-and-the-perils-of-aggregation).

---

## Técnica de Streamlit e BigQuery

**D9 · Configure a página em modo largo e distribua os KPIs em colunas.**
Regra: `st.set_page_config(layout="wide")` deve ser a primeira chamada do Streamlit.
Como aplicar: defina `page_title` e o layout, depois use `st.columns(n)` para a linha de KPIs e `st.tabs` para separar os blocos.
Fonte: [Streamlit, st.set_page_config](https://docs.streamlit.io/develop/api-reference/configuration/st.set_page_config).

**D10 · Use `st.metric` com delta, sparkline, borda e ajuda.**
Regra: cada KPI mostra o valor, a variação, a mini-série e a definição.
Como aplicar: `delta=` com a variação, `delta_color="inverse"` quando cair é bom, `chart_data=` com os últimos dias, `border=True` e `help=` com a definição e o limiar.
Fonte: [Streamlit, st.metric](https://docs.streamlit.io/develop/api-reference/data/st.metric).

**D11 · Saiba que `st.tabs` executa todas as abas.**
Regra: por padrão o código de todas as abas roda a cada interação.
Como aplicar: com cache, isso é barato. Se alguma aba ficar pesada, use `on_change="rerun"` e `if tab.open:`. Para atualização periódica, `st.fragment(run_every=...)`.
Fonte: [Streamlit, st.tabs](https://docs.streamlit.io/develop/api-reference/layout/st.tabs); [Streamlit, st.fragment](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment).

**D12 · Cacheie as consultas com `st.cache_data` e `ttl`.**
Regra: o padrão `ttl=None` nunca expira, então defina um tempo compatível com a frequência das views.
Como aplicar: `@st.cache_data(ttl="1h")` na função de consulta. Mostre na tela "dados atualizados em ..." com a maior data da view.
Fonte: [Streamlit, st.cache_data](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data); [Streamlit, Connect to BigQuery](https://docs.streamlit.io/develop/tutorials/databases/bigquery).

**D13 · Controle o custo no BigQuery com `maximum_bytes_billed` e dry run.**
Regra: uma consulta acima do limite deve falhar sem cobrança.
Como aplicar: `QueryJobConfig(maximum_bytes_billed=...)`, colunas explícitas (sem `SELECT *`) e leitura de views diárias já agregadas. `LIMIT` não reduz bytes em tabela sem clusterização. Use `dry_run=True` para estimar o custo.
Fonte: [BigQuery, Best practices for controlling costs](https://docs.cloud.google.com/bigquery/docs/best-practices-costs); [Python client, QueryJobConfig](https://docs.cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.job.QueryJobConfig).

**D14 · Teste a app com `streamlit.testing.v1.AppTest`.**
Regra: a dash é código e precisa de teste automatizado.
Como aplicar: `at = AppTest.from_file("app.py").run()`, depois `assert not at.exception` e a contagem de métricas. Mude um filtro com `set_value(...).run()`. Troque a função de consulta por dados de fixture, sem chamar o BigQuery.
Fonte: [Streamlit, Get started with app testing](https://docs.streamlit.io/develop/concepts/app-testing/get-started).

---

## Checklist

- [ ] Layout largo, título claro e "dados atualizados em ..." no topo.
- [ ] Um KPI por problema na primeira linha, com delta, sparkline e `help`.
- [ ] `delta_color="inverse"` onde cair é bom.
- [ ] Status com ícone, texto e cor, e uma ação sugerida.
- [ ] Alerta de volume independente do status do processo.
- [ ] Indicador de atualização (dias desde o último registro).
- [ ] Cobertura de join medida por valor e tabela do que ficou de fora.
- [ ] Limiares por dia da semana ou mediana de semanas, documentados.
- [ ] Séries com eventos anotados.
- [ ] Filtros globais na barra lateral, com período padrão curto.
- [ ] Razões como razão de somas; textos gerados dos mesmos dados.
- [ ] `st.cache_data` com `ttl`, `maximum_bytes_billed` e sem `SELECT *`.
- [ ] Testes com `AppTest` usando dados de fixture.
