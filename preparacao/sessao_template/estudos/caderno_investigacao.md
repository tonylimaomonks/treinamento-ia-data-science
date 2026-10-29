# Boas práticas · caderno de investigação (HTML de trabalho)

O caderno é a página que os analistas abrem durante a investigação para ver o que os agentes estão encontrando. Ele serve para explorar e decidir o próximo passo, não para convencer ninguém. Para Cole Nussbaumer Knaflic, o material exploratório deixa o usuário filtrar e comparar, enquanto o material explicativo leva o leitor a uma conclusão. Este arquivo trata do primeiro caso. O segundo está em `html_executivo.md`.

---

## Estrutura

**C1 · Uma seção por hipótese, sempre na mesma ordem.**
Regra: cada hipótese ocupa uma seção com a sequência pergunta, query ou arquivo, resultado, teste que refutaria e veredito.
Como aplicar: escreva a pergunta em uma frase, cite o arquivo da query, mostre o resultado em um gráfico ou tabela, diga qual resultado derrubaria a hipótese e termine com o veredito. Use sempre o mesmo molde, para o analista achar cada parte sem procurar.
Fonte: [Wikipedia, Analysis of competing hypotheses](https://en.wikipedia.org/wiki/Analysis_of_competing_hypotheses).

**C2 · Escreva o teste que refutaria a hipótese antes de olhar o resultado.**
Regra: uma hipótese só é útil se existir um resultado que a contradiga.
Como aplicar: na seção, preencha o campo "o que refutaria isto" antes de rodar a query. Exemplo neutro: "se a receita caiu só em um dos dois canais, a hipótese de queda geral não se sustenta". Depois de rodar, diga se o teste foi passado.
Fonte: [Wikipedia, Falsifiability](https://en.wikipedia.org/wiki/Falsifiability).

**C3 · Use três vereditos, e só três: CONFIRMADA, REFUTADA ou PARCIAL.**
Regra: o veredito precisa ser inequívoco e vir acompanhado da evidência que o sustenta.
Como aplicar: use PARCIAL quando a hipótese explica só uma fatia do efeito e diga qual fatia, em número e em porcentagem do total. Não use "talvez" nem "provável". Se faltar dado, registre a pergunta que ficou aberta.
Fonte: [Wikipedia, Analysis of competing hypotheses](https://en.wikipedia.org/wiki/Analysis_of_competing_hypotheses).

**C4 · Mantenha uma linha do tempo dos achados no topo da página.**
Regra: o leitor que chega no meio da investigação precisa ver o que já foi descoberto, em ordem.
Como aplicar: uma lista curta com data ou hora, hipótese, veredito e uma frase com o achado. Cada item leva um link âncora para a seção correspondente. Atualize a lista a cada nova conclusão.
Fonte: [Turing Way, Reproducible research](https://book.the-turing-way.org/reproducible-research/reproducible-research.html).

---

## Números e rastreabilidade

**C5 · Gere todo número a partir dos CSVs, nunca digite à mão.**
Regra: um número escrito à mão envelhece e não tem dono. Um número gerado do arquivo pode ser refeito.
Como aplicar: um script lê os CSVs exportados das queries e produz o HTML, inclusive as frases de texto, com template fixo e valores formatados. Se o dado mudar, rode o script de novo e a página inteira se atualiza.
Fonte: [Turing Way, Reproducible research](https://book.the-turing-way.org/reproducible-research/reproducible-research.html).

**C6 · Dê rastreabilidade a cada resultado: link para o arquivo da query e para o CSV.**
Regra: quem vê um gráfico precisa chegar à consulta que o produziu em um clique.
Como aplicar: abaixo de cada resultado, escreva o caminho do arquivo `.sql` e do CSV, e registre a data e o período analisado. Guarde as queries na pasta do projeto, com nomes que digam o que calculam.
Fonte: [Turing Way, Reproducible research](https://book.the-turing-way.org/reproducible-research/reproducible-research.html).

**C7 · Reconcilie o dado analisado com a fonte da verdade antes de interpretar.**
Regra: antes de explicar uma variação, confirme que o dado está completo em relação ao sistema de origem.
Como aplicar: compare o total de pedidos, receita ou gasto da tabela analisada com o sistema de origem, por dia. Se a diferença passar de um limiar definido de antemão, registre como achado e não como detalhe de rodapé.
Fonte: [Monte Carlo, Comprehensive Guide to Data Reconciliation](https://montecarlo.ai/blog-data-reconciliation).

**C8 · Meça cobertura de join por valor, não por contagem de linhas.**
Regra: um join que perde 2% das linhas pode perder muito mais que 2% do dinheiro.
Como aplicar: calcule a soma do valor (gasto ou receita) que casou dividida pela soma do valor total, por dia. Liste o que ficou de fora, ordenado por valor. Prefira left join com indicador de casamento a inner join, para ver o que sumiu.
Fonte: [Monte Carlo, Data Reconciliation (comparison monitors)](https://www.montecarlodata.com/blog-comparison-monitors/).

**C9 · Agregue indicadores como razão de somas.**
Regra: o custo por aquisição do período é a soma do gasto dividida pela soma das conversões, nunca a média dos valores diários.
Como aplicar: exporte numerador e denominador nos CSVs e calcule a razão só no último passo. Use a mesma regra para taxas de conversão e cobertura.
Fonte: [HR Exchange Network, Averaging Ratios and the Perils of Aggregation](https://www.hrexchangenetwork.com/hr-tech/articles/averaging-ratios-and-the-perils-of-aggregation).

---

## Gráficos e leitura

**C10 · Prefira gráficos exploratórios simples: barras, linhas e tabelas.**
Regra: no caderno o gráfico existe para o analista ver um padrão, então deve ser rápido de ler e de trocar.
Como aplicar: use linha para série diária, barras para comparar canais e tabela quando o número exato importa. Não gaste tempo com estilo. Siga as regras de `visualizacao_e_design.md` no que for barato.
Fonte: [NN/g, Dashboards: Making Charts and Graphs Easier to Understand](https://www.nngroup.com/articles/dashboards-preattentive/).

**C11 · Olhe o dado de várias formas antes de concluir: distribuição, série e quebra por dimensão.**
Regra: a análise exploratória pede que você examine o dado por ângulos diferentes antes de formar uma explicação.
Como aplicar: para cada métrica em questão, veja a série por dia, a quebra por canal ou plataforma e a distribuição dos valores, inclusive nulos e categorias raras. Registre no caderno o que cada visão mostrou, mesmo quando nada apareceu.
Fonte: [NIST, Exploratory Data Analysis](https://www.itl.nist.gov/div898/handbook/eda/eda.htm).

**C12 · Marque no gráfico as datas em que algo mudou.**
Regra: uma série sem eventos marcados convida a explicações falsas.
Como aplicar: desenhe linhas ou faixas nas datas de mudanças conhecidas (lançamento, troca de configuração, campanha). Quando um achado coincide com uma data marcada, escreva isso na seção, mas trate como pista e não como prova.
Fonte: [Datawrapper, What to consider when using text in data visualizations](https://www.datawrapper.de/blog/text-in-data-visualizations).

**C13 · Escreva para o analista: título com o que o gráfico mostra e uma linha de leitura.**
Regra: todo gráfico do caderno tem um título descritivo e uma frase dizendo o que o analista deve olhar.
Como aplicar: título no formato "o que é o dado, recorte, período" e, abaixo, a frase "repare que...". A conclusão fica no veredito da hipótese, não no título do gráfico.
Fonte: [UK Analysis Function, Data visualisation: charts](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/).

**C14 · Separe exploração de explicação: o que for conclusão vai para o relatório.**
Regra: o caderno pode ser longo e cheio de becos sem saída. O relatório executivo não.
Como aplicar: ao fechar uma hipótese como CONFIRMADA ou PARCIAL, marque-a como candidata ao relatório. As REFUTADAS ficam no caderno, porque documentam o que já foi descartado.
Fonte: [Storytelling with Data, from dashboard to story](https://www.storytellingwithdata.com/blog/from-dashboard-to-story).

---

## Checklist rápido

- [ ] Toda hipótese tem pergunta, query, resultado, teste que refutaria e veredito.
- [ ] Os vereditos são CONFIRMADA, REFUTADA ou PARCIAL, nunca algo vago.
- [ ] Há uma linha do tempo dos achados no topo, com links.
- [ ] Nenhum número foi digitado à mão: tudo vem dos CSVs.
- [ ] Cada resultado aponta para o arquivo da query e para o CSV.
- [ ] A reconciliação com a fonte da verdade foi feita antes da interpretação.
