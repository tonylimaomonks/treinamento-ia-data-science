---
name: setup-bq
description: Uso do facilitador. Cria ou recria a base do treinamento no BigQuery. Aceita uma data de referência opcional (AAAA-MM-DD).
disable-model-invocation: true
argument-hint: "[data_ref AAAA-MM-DD]"
allowed-tools: Bash(bash preparacao/setup/run_setup.sh:*), Bash(DATA_REF=* bash preparacao/setup/run_setup.sh:*)
---

# Setup do BigQuery do DS-101

Argumento recebido: `$ARGUMENTS`

1. Avise em uma linha:
   - o setup recria do zero, com `CREATE OR REPLACE`, as tabelas de `trama_setup`, `trama_raw`, `trama_legacy` e `trama_gabarito`;
   - ele cria `trama_silver` e `trama_gold` só se ainda não existirem, e não mexe no conteúdo deles (para esvaziar, use `/reset-sessao`);
   - a base fica ancorada na data de referência, com janela de 90 dias até o dia anterior.
2. Rode a partir da raiz do treinamento, com timeout de 10 minutos:
   - **Sem argumento** (data de hoje):
     ```bash
     bash preparacao/setup/run_setup.sh
     ```
   - **Com data em `AAAA-MM-DD`:**
     ```bash
     DATA_REF=<data> bash preparacao/setup/run_setup.sh
     ```
   - **Argumento que não é uma data nesse formato:** pare e pergunte, sem rodar.
3. Relate o resultado:
   - **Deu certo:** a saída termina com `✅ setup concluído`. Confirme em uma frase com o projeto e a data de referência que aparecem na primeira linha (`▶ projeto=...`) e cite qualquer alerta do `09_checagens.sql`.
   - **Falhou:** mostre em qual arquivo `▶ NN_...sql` parou e a mensagem de erro, sem tentar corrigir por conta própria:
     - acesso ao gcloud: comandos `gcloud auth ...`, que o usuário roda com `! <comando>`;
     - `GCP_PROJECT` não definido: editar o `.env.local`, que você não deve abrir.
