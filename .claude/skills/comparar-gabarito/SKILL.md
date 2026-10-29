---
name: comparar-gabarito
description: Uso do facilitador. Compara o que a sessão do treinamento produziu (gold no BigQuery, HTML e dash) com o gabarito, em uma rodada rápida e só de leitura.
disable-model-invocation: true
allowed-tools: Bash(bash preparacao/gabarito/comparar/comparar_sessao.sh:*)
---

# Comparar a sessão com o gabarito

Feito para rodar ao vivo: uma chamada só, e a resposta é curta. Não escreve nada no BigQuery nem em `sessao-ds101/`.

1. Rode a partir da raiz do treinamento, com timeout de 5 minutos:
   ```bash
   bash preparacao/gabarito/comparar/comparar_sessao.sh
   ```
   Se falhar por acesso ao gcloud, mostre os comandos `gcloud auth ...` que o script indica (o usuário roda com `! <comando>`) e pare.

   O script verifica:
   - **inventário:** o que existe em `trama_silver` e `trama_gold`;
   - **`gold_tracking_coverage_by_day`:** a soma da janela por plataforma e os dias divergentes, comparados com o gabarito, e se os dias com web zerado são exatamente os 4 dias sem ingestão (P1);
   - **`gold_media_performance_by_day`:** por canal e período, a verba, a fração `spend_only` (P4) e o CPA na régua do gabarito (web + app, sem os 4 dias quebrados);
   - **HTML da sessão:** quais números principais do gabarito aparecem no arquivo, entre vendas da dash, CPA unificado e degraus da cascata;
   - **dash:** se existe um app Streamlit e quais views da gold ele lê.

2. Não abra outros arquivos nem rode queries extras. A saída do script basta. Investigue só se o usuário pedir.

3. Responda em, no máximo, 8 linhas:
   - uma linha por bloco (cobertura, mídia, HTML, dash), com ✔, ⚠ ou ✘ e o motivo em poucas palavras;
   - para cada ✘ ou ⚠, cite o número da sessão e o do gabarito;
   - feche com um veredito: "a sessão está batendo" ou "o que corrigir primeiro".

   Para ler a saída:
   - A view não existir é normal antes do Ato 1. Diga em que ponto do roteiro ela deveria aparecer, e não trate como erro.
   - No HTML, `·` significa só que o número não foi encontrado. O HTML pode calcular os números no JS ou arredondar de outro jeito, então não diga que está errado. Diga quantos números foram encontrados e quais faltam.
   - No CPA, um ⚠ (diferença de até 10%) costuma vir de régua diferente, por exemplo quando a sessão não tirou os 4 dias quebrados. Aponte isso como hipótese.
