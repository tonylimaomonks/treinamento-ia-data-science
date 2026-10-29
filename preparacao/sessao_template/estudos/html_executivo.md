# Boas práticas · HTML executivo (relatório para cliente ou comitê)

O relatório executivo é uma peça explicativa. Quem lê tem poucos minutos e não vai refazer a análise. Por isso ele não é uma cópia do caderno de investigação com menos gráficos: é outra peça, com outro trabalho. Segundo Cole Nussbaumer Knaflic, executivos "não podem ser obrigados a fazer toda a exploração necessária" para achar a conclusão sozinhos.

---

## Conteúdo

**E1 · Comece pela resposta, como na pirâmide de Minto.**
Regra: a primeira frase da página é a conclusão ou a decisão recomendada, e o contexto vem depois.
Como aplicar: abra com uma frase do tipo "Recomendamos lançar a coleção nova em março, e não em fevereiro". Abaixo, três ou quatro argumentos, um por causa, cada um com um gráfico ou número. Metodologia e contexto ficam no fim.
Fonte: [Management Consulted, The Pyramid Principle](https://managementconsulted.com/pyramid-principle/); [Slideworks, The Pyramid Principle](https://slideworks.io/resources/the-pyramid-principle-mckinsey-toolbox-with-examples).

**E2 · Responda ao "e daí?" com uma frase de ideia central.**
Regra: resuma a mensagem em uma frase completa, com o seu ponto de vista e o que está em jogo.
Como aplicar: escreva "Se fizermos X com base em Y, perdemos Z". Teste a frase em voz alta: se alguém perguntar "e daí?", ela ainda não está pronta.
Fonte: [Storytelling with Data, what's the Big Idea?](https://www.storytellingwithdata.com/blog/2014/02/whats-big-idea).

**E3 · Trate o resumo do topo como a única parte que todos vão ler.**
Regra: o resumo executivo tem título-mensagem, frases completas e a ação recomendada explícita.
Como aplicar: um título com a conclusão, um parágrafo curto (não uma lista de fragmentos) e uma linha com a ação, o responsável e o prazo. O resumo deve bastar sozinho para quem parar de ler ali.
Fonte: [Storytelling with Data, How to create an executive summary slide](https://www.storytellingwithdata.com/blog/2022/1/14/executive-summary-slides).

**E4 · Coloque o impacto em dinheiro.**
Regra: um achado só vira decisão quando o leitor vê quanto custa agir errado ou não agir.
Como aplicar: converta cada achado em reais e em conversões, usando o custo por aquisição calculado como razão de somas. Diga de onde vem o número e para qual período vale. Exemplo neutro: "manter o erro custaria cerca de R$ 100 mil por mês em verba mal alocada".
Fonte: [Monte Carlo, The Cost of Poor Data Quality](https://montecarlo.ai/blog-the-cost-of-poor-data-quality/).

**E5 · Traduza o achado técnico para linguagem de negócio.**
Regra: o texto principal não usa nome de tabela, de coluna, de job nem sigla interna.
Como aplicar: troque o mecanismo pelo efeito. Em vez de "a tabela X tem a coluna Y com tipo errado", escreva "o preço médio aparecia 10% acima do real, e por isso a margem parecia menor". Os termos técnicos só aparecem na seção de metodologia.
Fonte: [Monte Carlo, The Cost of Poor Data Quality](https://montecarlo.ai/blog-the-cost-of-poor-data-quality/).

**E6 · Recomende com dono e prazo, e diga o que ainda não se sabe.**
Regra: toda recomendação pede uma ação humana clara, e as ressalvas são honestas.
Como aplicar: uma tabela curta com as colunas "o quê", "quem" e "até quando". Em seguida, uma lista de ressalvas: o que os dados não permitem afirmar, o tamanho do período analisado e o que seria preciso para fechar cada dúvida.
Fonte: [Google SRE Book, cap. 6 Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/); [Slideworks, The Pyramid Principle](https://slideworks.io/resources/the-pyramid-principle-mckinsey-toolbox-with-examples).

---

## Gráficos e forma

**E7 · Mostre poucos gráficos, cada um com título-mensagem.**
Regra: entre três e quatro gráficos, um por argumento, cada um com um título que diz a conclusão e um subtítulo que descreve o dado.
Como aplicar: título como "O frete grátis trouxe clientes novos, mas não aumentou o ticket" e subtítulo "custo por aquisição por canal, período tal". Ao lado do gráfico, uma frase de leitura. Detalhes vão para a dash de acompanhamento.
Fonte: [Storytelling with Data, from dashboard to story](https://www.storytellingwithdata.com/blog/from-dashboard-to-story); [UK Analysis Function, Data visualisation: charts](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/).

**E8 · Use gráficos que explicam mudança: ponte (waterfall) e antes e depois.**
Regra: para explicar como se sai de um número a outro, decomponha a diferença em causas.
Como aplicar: uma ponte parte do valor inicial, soma ou subtrai o efeito de cada causa e chega ao valor final. Para comparar dois momentos por categoria, use barras pareadas ou slopegraph.
Fonte: [Wikipedia, Waterfall chart](https://en.wikipedia.org/wiki/Waterfall_chart); [Storytelling with Data, more on slopegraphs](https://www.storytellingwithdata.com/blog/2014/03/more-on-slopegraphs).

**E9 · Use uma cor de destaque e deixe o resto em cinza.**
Regra: a cor aponta onde está a mensagem.
Como aplicar: pinte de destaque só a barra ou a linha que sustenta o argumento do gráfico. O restante fica em cinza. Detalhes em `visualizacao_e_design.md`.
Fonte: [Storytelling with Data, why to use color sparingly](https://www.storytellingwithdata.com/blog/2021/1/11/the-most-important-dataviz-decision-you-make).

**E10 · Entregue uma página única, com dados embutidos.**
Regra: o arquivo abre sozinho, sem consultar banco nem servidor, e se lê em 2 minutos.
Como aplicar: um `.html` com a biblioteca de gráficos por CDN e os dados em um bloco JSON dentro da página. A ordem é resumo, gráficos, recomendações, ressalvas e metodologia. Cada gráfico tem uma tabela ou texto alternativo com os mesmos números.
Fonte: [UK Analysis Function, Publishing charts](https://analysisfunction.civilservice.gov.uk/support/communicating-analysis/introduction-to-data-visualisation-e-learning/module-10-publishing-charts/).

**E11 · Gere os números dos mesmos dados dos gráficos.**
Regra: o texto estático também não recebe número digitado à mão.
Como aplicar: o script que monta a página calcula as frases a partir dos mesmos CSVs que alimentam os gráficos, com números formatados em pt-BR. Assim, texto e gráfico nunca divergem.
Fonte: [Microsoft Learn, Smart narrative](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-smart-narrative).

---

## Checklist

- [ ] A primeira frase é a conclusão ou a decisão, antes de qualquer contexto.
- [ ] Existe uma frase de ideia central com o que está em jogo.
- [ ] O resumo do topo se lê em 2 minutos, em frases completas, com a ação explícita.
- [ ] O impacto aparece em reais e em conversões.
- [ ] Não há jargão técnico no texto principal.
- [ ] Há no máximo quatro gráficos, cada um com título-mensagem e subtítulo.
- [ ] Existe um gráfico que decompõe a diferença entre dois números, quando a análise pede.
- [ ] Uma só cor de destaque; nada de pizza, 3D ou eixo duplo.
- [ ] Indicadores são razão de somas, nunca média de razões.
- [ ] Números e datas estão em pt-BR, sem casas decimais a mais.
- [ ] As recomendações têm o quê, quem e até quando.
- [ ] As ressalvas dizem honestamente o que ainda não se sabe.
- [ ] A página é única, com dados embutidos e tabela acessível por gráfico.
- [ ] Todo número do texto vem dos mesmos dados dos gráficos.
