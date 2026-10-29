# Boas práticas · visualização e design

Estas regras valem para o caderno, o relatório executivo e a dash. Onde uma entrega pede algo diferente, o arquivo dela diz.

---

**V1 · Escolha o gráfico pela mensagem.**
Regra: use comprimento e posição, que o olho compara sem esforço, e evite pizza, rosca, gauge e 3D.
Como aplicar: barras horizontais para comparar categorias, linha para série no tempo, barras empilhadas a 100% ou lado a lado para composição, dispersão para relação entre duas medidas. Exemplo neutro: comparar o custo de três canais pede barras, não três fatias.
Fonte: [NN/g, Dashboards: Making Charts and Graphs Easier to Understand](https://www.nngroup.com/articles/dashboards-preattentive/); [Stephen Few, Save the Pies for Dessert (PDF)](https://www.perceptualedge.com/articles/visual_business_intelligence/save_the_pies_for_dessert.pdf).

**V2 · Comece em cinza e use uma única cor de destaque.**
Regra: a cor chama a atenção para onde está a mensagem.
Como aplicar: todas as séries em cinza e só a que sustenta a mensagem colorida. Na dash, deixe a cor para o que passou do limiar. Não dê uma cor a cada canal sem motivo.
Fonte: [Storytelling with Data, why to use color sparingly](https://www.storytellingwithdata.com/blog/2021/1/11/the-most-important-dataviz-decision-you-make); [Storytelling with Data, power pairing: color + words](https://www.storytellingwithdata.com/blog/2019/7/10/power-pairing-color-words).

**V3 · Dê ao gráfico um título que diz a mensagem e um subtítulo que descreve o dado.**
Regra: o título tem até cerca de dez palavras e o subtítulo segue o molde "o que é, recorte, período".
Como aplicar: título "A região Sul cresceu o dobro das outras". Subtítulo "Receita por região, 1 a 30 de um mês". No caderno, o título pode ser apenas descritivo.
Fonte: [UK Analysis Function, Data visualisation: charts](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/).

**V4 · Não dependa só de cor.**
Regra: a informação precisa sobreviver para quem não distingue cores ou imprime em preto e branco.
Como aplicar: acrescente ícone, texto, rótulo direto no fim da linha ou padrão de preenchimento. Garanta contraste de 4,5:1 para texto e 3:1 para elementos gráficos.
Fonte: [W3C, Understanding SC 1.4.1 Use of Color](https://w3.org/WAI/WCAG22/Understanding/use-of-color.html); [UK Analysis Function, Making charts accessible](https://analysisfunction.civilservice.gov.uk/support/communicating-analysis-old/making-charts-accessible-dataconnect22/).

**V5 · Torne o gráfico acessível para leitores de tela.**
Regra: todo gráfico desenhado em `<canvas>` precisa de descrição e de uma versão em texto.
Como aplicar: use `role="img"` e `aria-label` com a frase-mensagem, e coloque uma tabela com os mesmos números logo abaixo.
Fonte: [Chart.js, Accessibility](https://www.chartjs.org/docs/latest/general/accessibility.html).

**V6 · Formate números e datas em pt-BR.**
Regra: separador de milhar é o ponto, decimal é a vírgula, e a moeda leva o prefixo R$.
Como aplicar: `R$ 1.234,56`, `12,3%`, `30/09/2026` ou `30 set`. No navegador, `Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'})` e a opção `locale: 'pt-BR'` do Chart.js. Em Python, o Babel oferece `format_currency(v, 'BRL', locale='pt_BR')`; teste valores redondos, pois há um erro conhecido com múltiplos exatos de um milhão.
Fonte: [MDN, Intl.NumberFormat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat); [Chart.js, CoreChartOptions (locale)](https://www.chartjs.org/docs/latest/api/interfaces/CoreChartOptions.html); [Babel, Numbers](https://babel.pocoo.org/en/latest/api/numbers.html); [Babel, issue 879](https://github.com/python-babel/babel/issues/879).

**V7 · Use a precisão que a decisão exige, e não mais.**
Regra: casas decimais em excesso dão falsa sensação de exatidão e poluem a leitura.
Como aplicar: custo por aquisição sem centavos no relatório, percentuais com uma casa, valores grandes em milhares ou milhões com a unidade no título.
Fonte: [Stephen Few, Common Pitfalls in Dashboard Design (PDF)](https://www.perceptualedge.com/articles/Whitepapers/Common_Pitfalls.pdf).

**V8 · Evite eixo duplo.**
Regra: dois eixos Y no mesmo gráfico sugerem correlações que o desenho inventa.
Como aplicar: rotule as séries diretamente, faça dois gráficos alinhados com o mesmo eixo X, ou converta para a mesma unidade, por exemplo uma razão em porcentagem.
Fonte: [Storytelling with Data, be gone dual y-axis!](https://www.storytellingwithdata.com/blog/2016/2/1/be-gone-dual-y-axis); [Datawrapper, Why not to use two axes](https://www.datawrapper.de/blog/dualaxis).

**V9 · Nunca tire a média de razões.**
Regra: agregue como razão de somas.
Como aplicar: o custo por aquisição do período é a soma do gasto dividida pela soma das conversões, e não a média dos valores diários ou por campanha. A mesma regra vale para cobertura e taxa de conversão.
Fonte: [HR Exchange Network, Averaging Ratios and the Perils of Aggregation](https://www.hrexchangenetwork.com/hr-tech/articles/averaging-ratios-and-the-perils-of-aggregation); [Metabase Discussion, ratio of sums](https://discourse.metabase.com/t/how-to-aggregate-by-weighted-average-of-i-e-ratio-of-sums-rather-than-sum-of-ratios/8334).

**V10 · Anote os eventos na série temporal.**
Regra: marque no próprio gráfico as datas em que algo mudou.
Como aplicar: uma linha vertical para um momento e uma faixa sombreada para um intervalo, sempre com um rótulo curto. No Chart.js, use `chartjs-plugin-annotation` (tipos `line` e `box`). Com Altair, use camadas `mark_rule` e `mark_rect`.
Fonte: [Datawrapper, What to consider when using text in data visualizations](https://www.datawrapper.de/blog/text-in-data-visualizations); [chartjs-plugin-annotation (GitHub)](https://github.com/kurkle/chartjs-plugin-annotation).

**V11 · Use ponte (waterfall) para decompor a diferença entre dois números.**
Regra: a ponte mostra quanto cada causa explica da variação total.
Como aplicar: parta do valor inicial, adicione as barras de cada causa e termine no valor final. Use cor de destaque na causa principal e cinza nas demais.
Fonte: [Wikipedia, Waterfall chart](https://en.wikipedia.org/wiki/Waterfall_chart).

**V12 · Use slopegraph ou barras pareadas para antes e depois.**
Regra: para comparar dois momentos por categoria, desenhe as duas medidas lado a lado.
Como aplicar: uma linha por categoria ligando o valor da esquerda ao da direita. Uma troca de ordem entre categorias aparece como cruzamento de linhas.
Fonte: [Storytelling with Data, more on slopegraphs](https://www.storytellingwithdata.com/blog/2014/03/more-on-slopegraphs).

**V13 · Mantenha cada gráfico limpo: sem moldura, grade pesada nem legenda distante.**
Regra: tudo o que não carrega informação compete com o que carrega.
Como aplicar: remova bordas e sombras, deixe a grade em cinza claro e rotule as séries perto dos dados. Mantenha o eixo das barras começando em zero.
Fonte: [Tufte, sparklines e data-ink](https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/).
