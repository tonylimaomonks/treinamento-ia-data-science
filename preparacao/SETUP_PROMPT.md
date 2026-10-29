# Reproduzir o treinamento DS-101 no seu GCP

Abra o Claude Code **na pasta `preparacao/`** (e não na `sessao-ds101/`) e cole o prompt abaixo. Ele instala o que faltar, configura o seu projeto e sobe a base inteira. Custo estimado: centavos de dólar (a base tem poucos MB).

---

```
Quero reproduzir o treinamento DS-101 (Trama Moda) no meu GCP. Leia o CLAUDE.md e o
setup/run_setup.sh antes de começar e siga estes passos, parando para me pedir o que
for interativo:

1. Verifique se `gcloud` e `bq` estão instalados. Se não estiverem, me diga o comando de
   instalação para o meu sistema operacional (no macOS: `brew install --cask google-cloud-sdk`)
   e espere eu rodar.
2. Peça para eu rodar `! gcloud auth login` e `! gcloud auth application-default login`.
   Depois liste meus projetos (`gcloud projects list`) e me pergunte qual usar. Ele precisa
   ter billing habilitado: no sandbox, partições com mais de 60 dias expiram e a janela do caso tem 90.
3. Rode `gcloud auth application-default set-quota-project <projeto>` e confirme que a API
   do BigQuery está habilitada (`gcloud services enable bigquery.googleapis.com`).
4. Copie o .env para .env.local (o .env.local fica só na minha máquina) e preencha nele
   GCP_PROJECT="<projeto>". Se eu tiver mais de uma config no gcloud
   (gcloud config configurations list), preencha também CLOUDSDK_ACTIVE_CONFIG_NAME.
   Não mexa no .env, que é genérico. O DATA_REF fica vazio (= hoje).
5. Rode `bash setup/run_setup.sh`. Ele confere o acesso antes de começar: se a conta não
   acessar o projeto, ele mostra os comandos de login. Nesse caso, peça para eu rodá-los. Se algum ASSERT do 09_checagens.sql falhar, me mostre
   qual falhou e o volume diário que o 00_recon_thelook.sql imprimiu antes de mexer em
   qualquer parâmetro.
6. Crie um venv em app/.venv, instale app/requirements.txt e me diga como subir a dash
   de referência (gabarito/dash/app.py).
7. Gere a pasta da sessão com `bash reset_sessao.sh -y`. Ela é criada em ../sessao-ds101/
   a partir de sessao_template/, já com o meu projeto e o caminho desta máquina.

Não abra nem me mostre nada de trama_gabarito ou do gabarito/: eu quero resolver o caso.
```

---

## Token do Jira (para a skill `/jira-preencher`)

Só é preciso se você for criar ou comentar o card no Jira durante o caso.

1. Gere um API token em **https://id.atlassian.com/manage-profile/security/api-tokens** ("Create API token"). Ele só aparece uma vez: copie na hora.
2. Cole no `preparacao/.env.local`, na linha `JIRA_API_TOKEN=""`, **editando o arquivo no seu editor**. Não cole o token no chat do Claude.
3. Antes de abrir o Claude na sessão, carregue as variáveis: `source ../preparacao/setup/config.env`.

O `.env.local` nunca vai no pacote, e o Claude da sessão não consegue lê-lo (a pasta `preparacao/` é bloqueada). Ele só enxerga a variável de ambiente.

## Depois do setup: fazer o caso

```bash
cd ../sessao-ds101
source ../preparacao/setup/config.env && source ../preparacao/app/.venv/bin/activate
claude
```

Siga o `roteiro/PROMPTS_DEMO.md` a partir do Ato 0. Para recomeçar do zero, rode `bash reset_sessao.sh -y` de novo (ou `/reset-sessao` num Claude aberto na raiz).

## O que o setup cria

| Dataset | Conteúdo |
|---|---|
| `trama_raw` | Bronze do caso: pedidos, eventos web, eventos app, spend, campanhas e log de ingestão |
| `trama_legacy` | A dash atual da Growth (com os erros dela) |
| `trama_silver` / `trama_gold` | Vazios: é onde você constrói a solução |
| `trama_setup` | Parâmetros e verdade oculta. **Não olhe se quiser resolver sozinho** |
| `trama_gabarito` | A solução de referência. **Idem** |
