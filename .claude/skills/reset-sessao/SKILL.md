---
name: reset-sessao
description: Uso do facilitador. Devolve a pasta da sessão do treinamento ao estado inicial e esvazia trama_silver e trama_gold.
disable-model-invocation: true
allowed-tools: Bash(bash preparacao/reset_sessao.sh:*)
---

# Reset da sessão DS-101

1. Avise em uma linha o que vai ser apagado:
   - a pasta `sessao-ds101/`, recriada a partir de `sessao_template/`;
   - a memória e o histórico do Claude Code dessa pasta;
   - todas as tabelas e views de `trama_silver` e `trama_gold`.

   Lembre que é preciso fechar antes qualquer sessão do Claude Code aberta em `sessao-ds101/`.
2. Rode, a partir da raiz do treinamento:
   ```bash
   bash preparacao/reset_sessao.sh -y
   ```
   Use `-y`, porque a confirmação interativa do script não funciona pelo Claude.
3. Relate o resultado:
   - **Deu certo:** a saída tem as três linhas com ✔ (pasta, memória e histórico, silver e gold). Confirme em uma frase.
   - **Falhou:** mostre a mensagem de erro e o próximo passo que o próprio script indica, sem tentar corrigir por conta própria:
     - acesso ao gcloud: comandos `gcloud auth ...`, que o usuário roda com `! <comando>`;
     - `GCP_PROJECT` não definido: editar o `.env.local`, que você não deve abrir;
     - `trama_raw` ausente: rodar `bash preparacao/setup/run_setup.sh`.
