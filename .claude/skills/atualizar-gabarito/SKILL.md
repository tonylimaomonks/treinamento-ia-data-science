---
name: atualizar-gabarito
description: Uso do facilitador. Atualiza o gabarito (CSVs, relatório HTML e GABARITO.md) com os números do último setup do BigQuery.
disable-model-invocation: true
allowed-tools: Bash(bash preparacao/gabarito/relatorio/rodar_queries.sh:*), Bash(python3 preparacao/gabarito/relatorio/gen_data.py:*), Read(preparacao/gabarito/**), Edit(preparacao/gabarito/GABARITO.md)
---

# Atualizar o gabarito do DS-101

Use depois de um `/setup-bq`. O setup recalcula o `trama_gabarito` no BigQuery, mas a foto local (`results/*.csv`, `relatorio_DS-101.html` e `GABARITO.md`) continua com a data antiga.

1. Avise em uma linha o que vai ser sobrescrito:
   - os `results/*.csv`;
   - o `data.json` e o `relatorio_DS-101.html`;
   - os números do `GABARITO.md`.
2. Rode, a partir da raiz do treinamento e com timeout de 10 minutos:
   ```bash
   bash preparacao/gabarito/relatorio/rodar_queries.sh
   ```
   A saída deve ter uma linha `✔ rNN_...` para cada uma das 9 queries. Se falhar, mostre a query em que parou e a mensagem de erro, e pare. Não tente corrigir por conta própria:
   - acesso ao gcloud: comandos `gcloud auth ...`, que o usuário roda com `! <comando>`;
   - `GCP_PROJECT` não definido: editar o `.env.local`, que você não deve abrir;
   - tabela de `trama_gabarito` ausente: rodar `/setup-bq` antes.
3. Rode:
   ```bash
   python3 preparacao/gabarito/relatorio/gen_data.py
   ```
   Se der erro de parse ou de validação, mostre a mensagem e pare.
4. Atualize o `preparacao/gabarito/GABARITO.md` com os CSVs de `preparacao/gabarito/relatorio/results/`:
   - **Datas no topo:** use o `r09_contexto.csv` (setup de `data_ref`, janela de `janela_inicio` a `janela_fim`). Os 4 dias do P1 também saem do `dias_sem_ingestao_web`.
   - **Dash legada:** use o `r07_dash_legada.csv` para vendas, variação e CPA por canal. Recalcule o total e o múltiplo do CPA do Meta.
   - **Régua unificada:** use as linhas `regua = unificada` do `r06_veredito_cpa.csv`.
   - **P2:** use o `r03_bloco0_utm.csv`, que traz as UTMs do Meta fora do padrão e a fração no período B.
   - **P3:** use o `r04_plataforma_por_campanha.csv`, que traz a fração de conversão no app por canal em A e em B.
   - **P4:** use o `r05_cobertura_join_verba.csv`, que traz a fração da verba do TikTok sem `campaign_name`, o valor no período B e a cobertura do join por verba.
   - **Cascata:** use o `r08_cascata_meta.csv`. Recalcule os Δ e a frase de leitura (efeito real e cada parcela de medição, além da porcentagem do efeito real).

   Troque só os números e as datas. A estrutura, o texto e o veredito ficam como estão. O formato também se mantém: R$ com vírgula decimal, ponto de milhar e sinal de menos `−`. Os parâmetros do setup, como o "Parâmetro: 25%" do P2, não mudam.
5. Confira se a história se manteve:
   - na régua unificada, o Meta continua quase estável;
   - o TikTok continua o canal mais caro;
   - o efeito real continua minoria na cascata.

   Se algum desses pontos se inverteu, a frase do veredito deixa de valer. Avise o usuário e não reescreva o veredito por conta própria.
6. Relate em poucas linhas:
   - a data nova;
   - os números principais de antes e de depois (vendas web do Meta de A para B, CPA unificado do Meta e o efeito real da cascata);
   - qualquer alerta.

   Lembre que o HTML pode ser aberto com `open preparacao/gabarito/relatorio/relatorio_DS-101.html`.
