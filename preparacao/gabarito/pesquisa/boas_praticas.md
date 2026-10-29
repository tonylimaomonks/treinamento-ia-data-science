# Boas práticas para o relatório de veredito e a dash de acompanhamento · caso Trama Moda

Data: 2026-09-30

**Como usar este arquivo.** Ele reúne as práticas, com fonte, que devem guiar as duas entregas do caso. O relatório HTML (Chart.js) serve ao comitê de verba e à Head de Growth: é uma **peça de negócio, explicativa**. Ela dá a decisão primeiro, mostra quanto custaria errar, se lê em 2 minutos e fala sem jargão técnico. A dash em Streamlit sobre o BigQuery é a **visão de acompanhamento, exploratória**. É mais analítica, tem mais gráficos e mais detalhe, e serve para ver nos próximos dias se P1–P4 voltam a acontecer. Cada prática traz a regra em uma frase, como ela se aplica a este caso e a fonte. As marcações **[Relatório]**, **[Dash]** ou **[Ambos]** dizem a qual entrega a prática se aplica. Os limiares numéricos sugeridos são pontos de partida para calibrar com o dado real. Não vêm das fontes, e isso está dito em cada caso. No fim há dois checklists marcáveis e uma lista de conflitos entre fontes.

**A diferença entre as duas entregas, segundo as fontes.** Para Cole Nussbaumer Knaflic, dashboards servem para **explorar**: atualizam sozinhos, ligam várias visões e deixam o usuário filtrar. Uma **história explicativa** é outra peça, feita "para trazer os achados à luz e levar os outros a agir". Executivos "não podem ser obrigados a fazer toda a exploração necessária" para achar a conclusão sozinhos ([SWD, from dashboard to story](https://www.storytellingwithdata.com/blog/from-dashboard-to-story)). Por isso o relatório não deve ser uma cópia da dash com menos gráficos. Ele é outra peça, com outro trabalho.

---

## R1 · Conteúdo

**R1.1 [Relatório] Comece pela resposta, sustente com poucos argumentos e só então mostre o dado (pirâmide de Minto).**
Como se aplica: a primeira frase da página é a decisão, por exemplo "Recomendamos **não** cortar 40% da verba do Meta: a queda vista na dash antiga é, em sua maior parte, erro de medição". Abaixo vêm três ou quatro argumentos, um por causa: dados que sumiram por 4 dias, campanhas do Meta sem etiqueta, vendas que migraram para o app e verba do TikTok fora da conta. Cada argumento leva a um gráfico ou número. O contexto e a metodologia ficam por último.
Fonte: [Management Consulted, The Pyramid Principle](https://managementconsulted.com/pyramid-principle/); [Slideworks, The Pyramid Principle](https://slideworks.io/resources/the-pyramid-principle-mckinsey-toolbox-with-examples).

**R1.2 [Relatório] Resuma o "e daí?" em uma Big Idea: uma frase completa, com seu ponto de vista e o que está em jogo.**
Como se aplica: "Se cortarmos o Meta com base na dash antiga, tiramos verba do canal com CPA estável e a colocamos no mais caro (o TikTok), por causa de um erro de medição." O "o que está em jogo" é a verba que seria movida (40% do Meta) para um canal com CPA real maior. O relatório deve dar esse valor em reais e em conversões perdidas, calculado com o CPA unificado.
Fonte: [SWD, what's the Big Idea?](https://www.storytellingwithdata.com/blog/2014/02/whats-big-idea).

**R1.3 [Relatório] Trate o resumo executivo como a única coisa que o comitê vai ler: título-mensagem, frases completas e ação recomendada explícita.**
Como se aplica: o bloco do topo tem título com a conclusão, um parágrafo curto em frases completas (não uma lista de fragmentos) e a ação "manter a verba e reavaliar em N dias na régua unificada". Knaflic diz que esse resumo "pode ser a única coisa que sua audiência vai olhar".
Fonte: [SWD, How to create an executive summary slide](https://www.storytellingwithdata.com/blog/2022/1/14/executive-summary-slides).

**R1.4 [Relatório] Traduza cada achado técnico em impacto de negócio: tempo sem dado, número de ocorrências e custo.**
Como se aplica: o texto para o comitê não fala em P1–P4, INNER JOIN nem UTM. Troque "job SUCCESS com 0 linhas" por "por 4 dias a dash não recebeu nenhuma venda do site, sem que ninguém fosse avisado". Troque "UTM fora do template" por "1 em cada 4 campanhas do Meta ficou sem identificação e sumiu do relatório do Meta". Troque "INNER JOIN descarta spend" por "parte do gasto do TikTok não entrava na conta, então o TikTok parecia mais barato". O Monte Carlo mede o custo de dado ruim como *data downtime* = nº de incidentes × (tempo até detectar + tempo até resolver), mais o impacto de negócio por incidente. Aqui, o impacto seria a verba realocada por engano.
Fonte: [Monte Carlo, The Cost of Poor Data Quality](https://montecarlo.ai/blog-the-cost-of-poor-data-quality/).

**R1.5 [Relatório] Mostre só o dado que sustenta a mensagem e explique o "e daí?" em palavras ao lado do gráfico.**
Como se aplica: no máximo 3 ou 4 gráficos, um por argumento. Cada um tem uma frase de leitura ao lado, por exemplo "Somando site e app, o CPA do Meta ficou estável". Detalhes como a cobertura do join por dia ou a lista de templates de UTM vão para a dash, não para o relatório.
Fonte: [SWD, from dashboard to story](https://www.storytellingwithdata.com/blog/from-dashboard-to-story).

**R1.6 [Relatório] Feche com recomendações acionáveis, cada uma com dono e prazo, e com ressalvas honestas.**
Como se aplica: uma tabela curta com colunas "o quê / quem / até quando". Exemplos: alerta de volume no job de ingestão (Dados); padronizar o template de UTM com a agência (Mídia); incluir o app na régua oficial (BI); tratar o gasto do TikTok sem nome de campanha (Dados). As ressalvas dizem o que ainda não se sabe: por exemplo, se parte da migração para o app é venda incremental ou só troca de canal. A regra do SRE vale aqui: todo alerta ou recomendação deve pedir uma ação humana clara. O Minto pede que o leitor saia sabendo "a ação que deve acontecer em seguida".
Fontes: [Google SRE Book, cap. 6 Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/); [Slideworks, The Pyramid Principle](https://slideworks.io/resources/the-pyramid-principle-mckinsey-toolbox-with-examples).

**R1.7 [Dash] Monitore as dimensões clássicas de observabilidade: atualização (freshness), volume, esquema, distribuição e linhagem.**
Como se aplica: cada problema cai numa dimensão. P1 é volume e atualização (eventos web = 0; data do último evento). P2 é distribuição (a parcela de "unassigned" subiu). P3 é distribuição por plataforma (a parcela de pedidos do app subiu entre as campanhas do Meta). P4 é completude, ou seja, nulos em `campaign_name`. A dash deve ter pelo menos um indicador por dimensão.
Fonte: [Monte Carlo, What Is Data Observability? 5 Key Pillars](https://montecarlo.ai/blog-what-is-data-observability).

**R1.8 [Dash] Alerte por volume, não só por status do job: um job pode terminar em "sucesso" com dado vazio ou errado.**
Como se aplica: o KPI principal da aba P1 é a razão diária **pedidos rastreados ÷ pedidos do ERP**. Um alerta dispara quando ela cai abaixo de um piso, por exemplo 90%, que é um valor sugerido para calibrar. Nesse caso, os 4 dias com 0 linhas teriam aparecido como 0%. O Great Expectations tem `expect_table_row_count_to_be_between` para isso e recomenda usá-lo junto com um teste de atualização. O Monte Carlo trata como caso central o "bug que nunca lança exceção".
Fontes: [Great Expectations, expect_table_row_count_to_be_between](https://greatexpectations.io/legacy/v1/expectations/expect_table_row_count_to_be_between/); [Monte Carlo, Catching the bug that never throws an exception](https://montecarlo.ai/blog-catching-the-bug-that-never-throws-an-exception).

**R1.9 [Dash] Reconcilie com a fonte da verdade, com limiar de divergência explícito.**
Como se aplica: há três reconciliações. (a) Pedidos do ERP × pedidos rastreados (web + app), com piso de cobertura. (b) Gasto no conector do TikTok × gasto que sobra depois do join, com a **cobertura medida por verba** e não por linhas. O piso sugerido é 98%. (c) Parcela da verba do Meta com UTM reconhecida, com teto de "unassigned" sugerido de 5%. O Monte Carlo cita como referência um alerta quando o destino tem 5% menos que a origem.
Fontes: [Monte Carlo, Data Reconciliation (comparison monitors)](https://www.montecarlodata.com/blog-comparison-monitors/); [Monte Carlo, Comprehensive Guide to Data Reconciliation](https://montecarlo.ai/blog-data-reconciliation).

**R1.10 [Dash] Leve em conta a sazonalidade semanal nos limiares, e só alerte quando houver uma ação a tomar.**
Como se aplica: compare cada dia com o mesmo dia da semana anterior, ou com a mediana de 4 a 6 semanas, em vez de um número fixo. Pedidos de moda têm padrão de fim de semana. O Monte Carlo treina com até 6 semanas e modela a sazonalidade semanal para "uma queda de segunda-feira normal não acionar ninguém". O SRE recomenda que o que dispara alerta seja "simples e robusto", sem alertar só porque algo "parece estranho". Mostre um status de três cores (ok / atenção / falha) e diga ao lado o que fazer.
Fontes: [Monte Carlo docs, Metric Monitors](https://docs.getmontecarlo.com/docs/metric-monitors); [Google SRE Book, cap. 6](https://sre.google/sre-book/monitoring-distributed-systems/).

**Insights textuais gerados a partir do dado [Ambos].** O Power BI (Smart Narrative) gera frases com **valores dinâmicos** ligados às medidas, que se atualizam a cada refresh e a cada filtro ([Microsoft Learn, Smart narrative](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-smart-narrative)). Na dash, gere as frases a partir do mesmo DataFrame do gráfico, com template fixo e números formatados. Exemplo: "Ontem a cobertura ERP × rastreado foi de 97,4% (piso 90%)". Nunca escreva o número à mão. No relatório, que é estático, as frases podem ser redigidas, mas os números devem vir da mesma consulta que gerou os gráficos.

---

## R2 · Visualização e design

**R2.1 [Ambos] Escolha o gráfico pela mensagem, usando comprimento e posição, e evite pizza, rosca, gauge e 3D.**
Como se aplica: para comparar o CPA por canal na régua unificada, use barras horizontais. Para séries diárias (eventos, cobertura, % unassigned), use linha. Para comparar composição entre canais, use barras empilhadas a 100% ou barras lado a lado, não pizza. O NN/g recomenda barras, linhas e dispersão porque a leitura é pré-atentiva. Few mostra que barras comparam melhor que fatias.
Fontes: [NN/g, Dashboards: Making Charts and Graphs Easier to Understand](https://www.nngroup.com/articles/dashboards-preattentive/); [Stephen Few, Save the Pies for Dessert (PDF)](https://www.perceptualedge.com/articles/visual_business_intelligence/save_the_pies_for_dessert.pdf).

**R2.2 [Relatório] Use cascata (waterfall/bridge) para explicar como se sai de um número a outro.**
Como se aplica: é o gráfico principal do relatório. Ele parte da queda de −30% nas vendas web da dash antiga e mostra o quanto cada causa explica: +4 dias sem dado, +vendas que migraram para o app, +campanhas sem etiqueta. Chega ao número real na régua unificada. Um segundo waterfall pode fazer o mesmo com o CPA do Meta (2× → estável). A cascata é o formato consagrado para decompor a variação entre dois valores.
Fonte: [Wikipedia, Waterfall chart](https://en.wikipedia.org/wiki/Waterfall_chart).

**R2.3 [Relatório] Use slopegraph (ou barras pareadas) para o antes × depois por canal.**
Como se aplica: o CPA de Meta, TikTok e Google na "régua antiga" (esquerda) e na "régua unificada" (direita). A linha do TikTok subindo e a do Meta descendo mostram a inversão do ranking num só gráfico.
Fonte: [SWD, more on slopegraphs](https://www.storytellingwithdata.com/blog/2014/03/more-on-slopegraphs); [SWD, data storytelling example: before and after](https://www.storytellingwithdata.com/blog/2021/1/10/lets-improve-this-graph-yt9xj).

**R2.4 [Ambos] Comece em cinza e use uma única cor de destaque onde está a mensagem.**
Como se aplica: no relatório, o Meta fica na cor de destaque e os outros canais em cinza. Na dash, o cinza é o padrão e a cor fica para o que está fora do limiar (a faixa dos 4 dias sem dados, os dias com cobertura abaixo do piso). Não dê uma cor para cada canal sem motivo.
Fontes: [SWD, why to use color sparingly](https://www.storytellingwithdata.com/blog/2021/1/11/the-most-important-dataviz-decision-you-make); [SWD, power pairing: color + words](https://www.storytellingwithdata.com/blog/2019/7/10/power-pairing-color-words).

**R2.5 [Ambos] Escreva títulos que dão a mensagem, com um subtítulo que descreve o dado.**
Como se aplica: o título diz "O TikTok é o canal mais caro quando todo o gasto entra na conta". O subtítulo diz "CPA por canal, web + app, 1–30 set 2026". A diretriz do governo britânico pede um título-manchete de até cerca de 10 palavras e um subtítulo no formato [o que é o dado], [recorte], [período].
Fonte: [UK Analysis Function, Data visualisation: charts](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/).

**R2.6 [Ambos] Marque eventos na série temporal com anotações.**
Como se aplica: uma faixa sombreada nos 4 dias sem eventos web (P1). Uma linha vertical na data em que a agência trocou o template de UTM (P2). Uma linha na data de início do banner de 10% off no app (P3). No Chart.js, use `chartjs-plugin-annotation` (tipos `line` e `box` com `xMin`/`xMax`). No Streamlit com Altair, use camadas `mark_rule`/`mark_rect`.
Fontes: [Datawrapper, What to consider when using text in data visualizations](https://www.datawrapper.de/blog/text-in-data-visualizations); [chartjs-plugin-annotation (GitHub)](https://github.com/kurkle/chartjs-plugin-annotation).

**R2.7 [Ambos] Não dependa só de cor e garanta contraste de 4,5:1 para texto e 3:1 para elementos gráficos.**
Como se aplica: o status ok/atenção/falha leva ícone e texto além da cor. As linhas se distinguem também por rótulo direto no fim da linha, sem depender só da legenda. No Chart.js, o `<canvas>` recebe `role="img"` e `aria-label` com a frase-mensagem, e há uma tabela com os dados logo abaixo.
Fontes: [W3C, Understanding SC 1.4.1 Use of Color](https://w3.org/WAI/WCAG22/Understanding/use-of-color.html); [UK Analysis Function, Making charts accessible](https://analysisfunction.civilservice.gov.uk/support/communicating-analysis-old/making-charts-accessible-dataconnect22/); [Chart.js, Accessibility](https://www.chartjs.org/docs/latest/general/accessibility.html).

**R2.8 [Ambos] Formate números e datas em pt-BR, com precisão compatível com a decisão.**
Como se aplica: `R$ 1.234,56`, `12,3%`, `30/09/2026` ou `30 set`. No HTML, use `Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'})` e a opção `locale: 'pt-BR'` do Chart.js. No Python, o Babel tem `format_currency(v, 'BRL', locale='pt_BR')`, mas há um bug conhecido com múltiplos exatos de 1.000.000, então teste esse caso. Evite excesso de casas decimais, que é um dos 13 erros de Few: o CPA vai sem centavos no relatório, e percentuais com uma casa.
Fontes: [MDN, Intl.NumberFormat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat); [Chart.js, CoreChartOptions (locale)](https://www.chartjs.org/docs/latest/api/interfaces/CoreChartOptions.html); [Babel, Numbers](https://babel.pocoo.org/en/latest/api/numbers.html); [Babel issue #879](https://github.com/python-babel/babel/issues/879); [Few, Common Pitfalls in Dashboard Design (PDF)](https://www.perceptualedge.com/articles/Whitepapers/Common_Pitfalls.pdf).

**R2.9 [Ambos] Evite eixo duplo: rotule direto, separe em dois gráficos alinhados ou converta para a mesma unidade.**
Como se aplica: "gasto × CPA" ou "eventos × pedidos do ERP" não devem dividir um gráfico com dois eixos Y. Na dash, faça dois gráficos empilhados com o mesmo eixo X de datas, ou mostre a razão (cobertura em %) num eixo só.
Fontes: [SWD, be gone dual y-axis!](https://www.storytellingwithdata.com/blog/2016/2/1/be-gone-dual-y-axis); [Datawrapper, Why not to use two axes](https://www.datawrapper.de/blog/dualaxis).

**R2.10 [Ambos] Nunca tire a média de razões: agregue como razão de somas.**
Como se aplica: o CPA do período é `Σ gasto ÷ Σ conversões`, nunca a média dos CPAs diários ou por campanha. A cobertura do join é `Σ gasto que casou ÷ Σ gasto total`, e não a média das coberturas diárias. As views no BigQuery devem expor numerador e denominador, e a razão é calculada no último passo.
Fontes: [HR Exchange Network, Averaging Ratios and the Perils of Aggregation](https://www.hrexchangenetwork.com/hr-tech/articles/averaging-ratios-and-the-perils-of-aggregation); [Metabase Discussion, ratio of sums](https://discourse.metabase.com/t/how-to-aggregate-by-weighted-average-of-i-e-ratio-of-sums-rather-than-sum-of-ratios/8334).

---

## R3 · Layout e técnica

**R3.1 [Dash] Organize em pirâmide: KPIs no topo, tendências no meio e detalhe embaixo, com o mais importante no canto superior esquerdo.**
Como se aplica: a primeira linha tem 4 `st.metric`, um por problema: cobertura ERP × rastreado (P1), % de verba do Meta em unassigned (P2), % de pedidos do Meta no app (P3) e cobertura por verba do TikTok (P4). Embaixo vêm as séries diárias, e no rodapé as tabelas de detalhe. O NN/g mostra que a leitura segue o padrão em F, e o Tableau recomenda pôr a visão mais importante no canto superior esquerdo.
Fontes: [NN/g, F-Shaped Pattern](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/); [Tableau, Best Practices for Effective Dashboards](https://help.tableau.com/current/pro/desktop/en-us/dashboards_best_practices.htm).

**R3.2 [Dash] Limite o número de visões por tela e use abas para aprofundar.**
Como se aplica: a aba "Visão geral" tem os 4 KPIs e 2 ou 3 gráficos. Depois vem uma aba por problema (P1, P2, P3, P4), cada uma com 2 ou 3 gráficos e uma tabela, e uma aba "Sobre os dados". O Tableau recomenda de 2 a 3 visões por dashboard. Few define dashboard como algo que cabe "numa única tela", para ser lido de relance. O Looker avisa acima de 25 tiles.
Fontes: [Tableau, Best Practices](https://help.tableau.com/current/pro/desktop/en-us/dashboards_best_practices.htm); [Few, Information Dashboard Design (sumário)](https://www.perceptualedge.com/images/Dashboard_Outline.pdf); [Looker, Considerations when building performant dashboards](https://cloud.google.com/looker/docs/best-practices/considerations-when-building-performant-dashboards).

**R3.3 [Dash] Use `st.set_page_config(layout="wide")` e distribua os KPIs com `st.columns`.**
Como se aplica: `st.set_page_config(page_title="Saúde da medição · Trama Moda", layout="wide")` e depois `c1, c2, c3, c4 = st.columns(4)`. O layout `"wide"` usa a largura inteira da tela, e o `"centered"` limita a uma coluna fixa.
Fonte: [Streamlit, st.set_page_config](https://docs.streamlit.io/develop/api-reference/configuration/st.set_page_config).

**R3.4 [Dash] Use `st.metric` com `delta`, `delta_color` e sparkline, escolhendo `"inverse"` quando cair é bom.**
Como se aplica: para cobertura, `delta_color="normal"` (subir é bom). Para % unassigned e CPA, `delta_color="inverse"` (cair é bom). A documentação cita justamente "uma redução de custo" como exemplo. Use `chart_data=` com os últimos 14 dias para a mini-série, `border=True` e `help=` com a definição do KPI e o limiar.
Fonte: [Streamlit, st.metric](https://docs.streamlit.io/develop/api-reference/data/st.metric).

**R3.5 [Dash] Cacheie as consultas com `st.cache_data(ttl=...)` compatível com a atualização das views.**
Como se aplica: as views são diárias, então `@st.cache_data(ttl="1h")` ou `ttl=3600` evita reconsultar o BigQuery a cada clique. O tutorial oficial de BigQuery usa `ttl=600`. O padrão é `ttl=None`, ou seja, nunca expira, e a documentação de conexões recomenda sempre definir um `ttl` em produção. Mostre na tela "dados atualizados em ..." com o `MAX(data)` da view.
Fontes: [Streamlit, st.cache_data](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data); [Streamlit, Connect to BigQuery](https://docs.streamlit.io/develop/tutorials/databases/bigquery); [Streamlit, Connecting to data](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data).

**R3.6 [Dash] Controle o custo do BigQuery: `maximum_bytes_billed`, colunas explícitas e views pequenas.**
Como se aplica: `bigquery.QueryJobConfig(maximum_bytes_billed=...)` faz uma consulta acima do limite falhar **sem cobrança**. Não use `SELECT *`. Leia as views diárias já agregadas (materializadas), não as tabelas de eventos. `LIMIT` em tabela não clusterizada não reduz os bytes lidos. Use dry run para estimar o custo antes.
Fontes: [BigQuery, Best practices for controlling costs](https://docs.cloud.google.com/bigquery/docs/best-practices-costs); [Python client, QueryJobConfig](https://docs.cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.job.QueryJobConfig).

**R3.7 [Dash] Saiba que `st.tabs` executa todas as abas por padrão e use `on_change="rerun"` se alguma for pesada.**
Como se aplica: com cache, rodar as 5 abas é barato. Se uma aba de detalhe (por exemplo, a tabela de campanhas sem nome do TikTok) ficar lenta, use `st.tabs(..., on_change="rerun")` e `if tab.open:`. Para atualização automática, `st.fragment(run_every="10m")` só reexecuta o trecho necessário.
Fontes: [Streamlit, st.tabs](https://docs.streamlit.io/develop/api-reference/layout/st.tabs); [Streamlit, st.fragment](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment).

**R3.8 [Dash] Poucos filtros, globais, na barra lateral, e com padrões que já respondem à pergunta.**
Como se aplica: período (padrão: últimos 14 dias), canal e plataforma (web/app/ambos). Os filtros ficam no `st.sidebar` e valem para todas as abas. O Looker recomenda filtros compartilhados que alimentam vários tiles com uma consulta só, e períodos padrão curtos.
Fonte: [Looker, Considerations when building performant dashboards](https://cloud.google.com/looker/docs/best-practices/considerations-when-building-performant-dashboards).

**R3.9 [Dash] Teste a app com `streamlit.testing.v1.AppTest` no pytest.**
Como se aplica: `at = AppTest.from_file("app.py").run()`, depois `assert not at.exception` e `assert len(at.metric) == 4`. Mude um filtro com `at.sidebar.selectbox[0].set_value("app").run()`. Rode com dados de fixture, sem BigQuery, trocando a função de consulta. Os secrets de `.streamlit/` ficam disponíveis quando o pytest roda na pasta que os contém.
Fonte: [Streamlit, Get started with app testing](https://docs.streamlit.io/develop/concepts/app-testing/get-started).

**R3.10 [Relatório] Faça uma página única e autossuficiente, com dados embutidos e tabela acessível para cada gráfico.**
Como se aplica: um só `.html` com o Chart.js carregado de CDN e os dados num `<script>` JSON embutido, sem chamadas ao BigQuery. A ordem é: resumo executivo, a cascata, antes × depois, recomendações com dono e prazo, ressalvas e metodologia. Cada gráfico tem título-mensagem no corpo da página, não dentro da imagem, e uma tabela ou texto alternativo com os mesmos números. Para o executivo, Knaflic sugere o layout "um visual e bastante texto com espaço em branco".
Fontes: [UK Analysis Function, Publishing charts](https://analysisfunction.civilservice.gov.uk/support/communicating-analysis/introduction-to-data-visualisation-e-learning/module-10-publishing-charts/); [SWD, executive summary slides](https://www.storytellingwithdata.com/blog/2022/1/14/executive-summary-slides); [Tufte, sparklines e data-ink](https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/).

---

## Extra · Databricks: dashboards "como código" e pelo CLI

O que as fontes confirmam:

1. **Os AI/BI dashboards eram os "Lakeview dashboards".** A API ainda usa o nome `lakeview` ([Databricks, Use dashboard APIs](https://docs.databricks.com/aws/en/dashboards/tutorials/dashboard-crud-api)).
2. **O dashboard é um arquivo `.lvdash.json`** que pode ser exportado, versionado no Git e importado em outro workspace ([Databricks, Automate dashboards](https://docs.databricks.com/aws/en/dashboards/automate)).
3. **Os bundles têm um recurso `dashboards`.** O nome atual é *Declarative Automation Bundles*; o antigo, *Databricks Asset Bundles*, aparece na URL do blog. Os campos são `display_name`, `file_path` (o `.lvdash.json` local), `warehouse_id`, `embed_credentials` e `parent_path`. O suporte chegou na **CLI v0.232.0** ([Databricks, Bundle resources](https://docs.databricks.com/aws/en/dev-tools/bundles/resources); [Release notes](https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles)).
4. **Comandos da CLI confirmados** ([Databricks, bundle command group](https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands)):
   - `databricks bundle generate dashboard --existing-path <caminho>` (ou `--existing-id`) gera o YAML e o `.lvdash.json` de um dashboard que já existe;
   - `databricks bundle generate dashboard --resource <chave> --watch` puxa continuamente as edições feitas na UI para o arquivo local;
   - `databricks bundle validate` valida a configuração;
   - `databricks bundle deploy` publica. `--force` sobrescreve o remoto quando ele diverge do local; sem o flag, a divergência gera erro.
5. **API REST** ([Databricks, Use dashboard APIs](https://docs.databricks.com/aws/en/dashboards/tutorials/dashboard-crud-api)): `POST /api/2.0/lakeview/dashboards` (cria o rascunho, com o JSON no campo `serialized_dashboard`), `PATCH .../{id}`, `POST .../{id}/published` (publica), `DELETE .../{id}/published` (despublica) e `DELETE .../{id}` (manda para a lixeira).
6. **Também existem** Terraform, a tarefa de dashboard nos Lakeflow Jobs (refresh agendado) e Git folders para CI/CD ([Databricks, Automate dashboards](https://docs.databricks.com/aws/en/dashboards/automate)). O blog oficial de 03/03/2026 descreve o fluxo branch → revisão → deploy por ambiente ([Databricks blog, How to ship AI/BI Dashboard changes safely](https://www.databricks.com/blog/tutorial-how-ship-aibi-dashboard-changes-safely-scale-databricks-asset-bundles)).

O que **não** foi confirmado nas páginas lidas: a sintaxe exata de um grupo `databricks lakeview ...` na CLI. A página da API não mostra comandos de CLI. Um resumo de busca afirma que a CLI cobre list/get/create/publish, e existe a página de referência `lakeview-embedded`, mas não verifiquei a do grupo `lakeview`. Na fala, prefira citar `databricks bundle generate dashboard` e `databricks bundle deploy`.

Frase para a fala: "No Databricks, o dashboard é um `.lvdash.json` versionado. Declaramos no bundle e publicamos com `databricks bundle deploy`. Aqui simulamos o mesmo fluxo como código com Streamlit: o app é um `.py` no Git, lê as views do BigQuery e tem teste automatizado."

---

## Checklist para o relatório (visão de negócio, comitê de verba)

- [ ] A primeira frase é a decisão ("não cortar 40% do Meta") e vem antes de qualquer contexto (Minto).
- [ ] Há uma Big Idea de uma frase, com o que está em jogo em R$ e em conversões.
- [ ] O resumo executivo se lê em 2 minutos, em frases completas, com a ação recomendada explícita.
- [ ] Nenhum jargão técnico no texto principal: P1–P4, JOIN, UTM, job e view viram linguagem de negócio. Os termos técnicos só aparecem na metodologia.
- [ ] Cada causa é traduzida em impacto: tempo sem dado, verba afetada, efeito no CPA.
- [ ] No máximo 3 ou 4 gráficos, cada um com título-mensagem e subtítulo descritivo.
- [ ] Há uma cascata do −30% (dash antiga) até o número real na régua unificada.
- [ ] Há um antes × depois (slopegraph ou barras pareadas) do CPA por canal, régua antiga × unificada.
- [ ] Uma cor de destaque; o resto em cinza. Nada de pizza, 3D ou eixo duplo.
- [ ] O CPA é calculado como Σ gasto ÷ Σ conversões, nunca como média de CPAs.
- [ ] Números e datas em pt-BR (R$ 1.234, 12,3%, 30/09/2026), sem precisão excessiva.
- [ ] Recomendações em tabela com o quê, dono e prazo.
- [ ] As ressalvas dizem honestamente o que ainda não se sabe (por exemplo, incrementalidade do app e período curto).
- [ ] É uma página única e autossuficiente: dados embutidos, sem consultas externas; cada `<canvas>` tem `role="img"`, `aria-label` e uma tabela com os números.
- [ ] Há um link ou menção à dash de acompanhamento para quem quiser o detalhe.

## Checklist para a dash (visão de acompanhamento, Growth e comitê)

- [ ] `layout="wide"`, título claro e "dados atualizados em ..." (MAX(data) da view) no topo.
- [ ] Primeira linha com 4 `st.metric` (P1 cobertura ERP × rastreado, P2 % unassigned no Meta, P3 % de pedidos do Meta no app, P4 cobertura por verba do TikTok), com `delta`, sparkline e `help` com a definição e o limiar.
- [ ] `delta_color="inverse"` nos KPIs em que cair é bom (unassigned, CPA).
- [ ] Um status ok / atenção / falha por KPI, com ícone e texto, não só cor.
- [ ] Alerta de volume (pedidos rastreados ÷ ERP abaixo do piso), independente do status do job.
- [ ] Indicador de atualização: dias desde o último evento web e desde o último evento app.
- [ ] Cobertura do join do TikTok medida por verba (Σ gasto que casou ÷ Σ gasto) e uma tabela do gasto sem `campaign_name`.
- [ ] Limiares comparados com o mesmo dia da semana ou com a mediana de 4 a 6 semanas, e registrados na aba "Sobre os dados".
- [ ] Séries diárias com anotação dos eventos: faixa dos 4 dias sem dado, troca do template de UTM, início do banner do app.
- [ ] Uma aba por problema (P1–P4) com 2 ou 3 gráficos cada, mais uma visão geral e uma aba "Sobre os dados".
- [ ] Filtros globais na barra lateral (período padrão de 14 dias, canal, plataforma).
- [ ] Insights em texto gerados do mesmo DataFrame do gráfico, com números formatados em pt-BR.
- [ ] Razões calculadas como razão de somas nas views, que expõem numerador e denominador.
- [ ] `@st.cache_data(ttl=...)` nas consultas; `maximum_bytes_billed` no `QueryJobConfig`; sem `SELECT *`; leitura apenas das views diárias.
- [ ] Testes com `AppTest`: a app roda sem exceção, mostra os 4 metrics e responde aos filtros, com dados de fixture.

---

## Conflitos entre fontes

- **Quantos elementos por tela.** O Tableau recomenda de 2 a 3 visões por dashboard. O Looker só avisa a partir de 25 tiles, por desempenho. Few pede que tudo caiba numa tela. Não achei fonte de referência para a regra "5 a 9 elementos", que parece vir da ideia popular de "7 ± 2". Decisão sugerida: a visão geral fica com 4 KPIs e 2 ou 3 gráficos, e o resto vai para as abas.
- **Uma tela só × abas.** A definição de Few (tudo numa tela, de relance) contrasta com o uso de `st.tabs`. Uma forma de conciliar: a aba "Visão geral" cumpre o papel da tela única, e as abas por problema são para investigar.
- **Limiar fixo × limiar aprendido.** O Monte Carlo defende limiares aprendidos por ML, com sazonalidade, e diz que limiares fixos geram falsos positivos. O SRE do Google pede que o que aciona alerta seja "simples e robusto". Para um treinamento com poucas semanas de dado, use limiares fixos e explícitos, comparando com o mesmo dia da semana.
- **Eixo duplo.** A SWD e o Datawrapper recomendam evitar. O Flourish ([Dual axis charts](https://flourish.studio/blog/dual-axis-charts/)) admite o uso com cuidado. Aqui a recomendação é evitar, porque a audiência não é técnica.
- **`ttl` do cache.** O padrão do `st.cache_data` é `ttl=None`, que nunca expira. O tutorial usa 600 s, e a documentação de conexões recomenda sempre definir um `ttl`. Siga a recomendação e alinhe o `ttl` à frequência das views.
