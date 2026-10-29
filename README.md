# Treinamento DS-101 · como montar o ambiente no seu PC

Este pacote reproduz o treinamento de Claude Code em Data Science (caso fictício da **Trama Moda**). No fim deste guia você vai ter:

- o Claude Code instalado e autenticado;
- o `gcloud` e o `bq` ligados ao **seu** projeto no Google Cloud;
- a base do caso criada no seu BigQuery (custa centavos de dólar);
- um venv Python com Streamlit e o cliente do BigQuery;
- a pasta `sessao-ds101/` gerada e pronta para você resolver o caso.

Leva uns 20 a 30 minutos, a maior parte esperando instalação e login.

---

## 0. Como o pacote está organizado

```
treinamento-ia-data-science/
├── README.md            ← este arquivo
├── CLAUDE.md            ← regra da raiz: sessão e preparação não se misturam
├── .claude/skills/      ← comandos do facilitador (/reset-sessao, /setup-bq...)
├── preparacao/          ← material do facilitador (setup do BigQuery, gabarito, roteiro)
│   ├── .env             ← valores padrão (genérico, não edite)
│   ├── .env.local       ← você cria: seu projeto GCP e seus segredos
│   ├── setup/           ← scripts que criam a base no BigQuery
│   ├── app/             ← requirements do Streamlit (o venv fica aqui)
│   ├── sessao_template/ ← modelo da sessão (PEDIDO.md, estudos/ e a trava)
│   ├── reset_sessao.sh  ← gera a sessao-ds101/ a partir do modelo
│   └── SETUP_PROMPT.md  ← prompt para o Claude fazer este setup por você
└── sessao-ds101/        ← NÃO vem no pacote: você gera no passo 6
```

A `sessao-ds101/` é onde você resolve o caso. Ela não vem pronta: o `reset_sessao.sh` gera a pasta a partir do `sessao_template/`, já com o seu projeto e o caminho da sua máquina. Ela tem uma trava (hook) que impede o Claude de ler `preparacao/` e o gabarito, para você resolver o caso sem "colar".

> **Sistema operacional:** os scripts são em bash. Funcionam direto no macOS e no Linux. No Windows, use o **WSL** (Ubuntu) e siga os passos de Linux dentro dele.

---

## 1. Pré-requisitos

| Ferramenta | Para quê | Como conferir |
|---|---|---|
| Python ≥ 3.10 | Streamlit, scripts e testes | `python3 --version` |
| Google Cloud SDK (`gcloud` + `bq`) | Acesso ao BigQuery | `gcloud --version` e `bq version` |
| Claude Code | O próprio treinamento | `claude --version` |
| Um projeto no GCP **com billing** | Onde a base vai morar | console.cloud.google.com |

### 1.1 Python

- **macOS:** `brew install python@3.12`
- **Linux / WSL:** `sudo apt install python3 python3-venv python3-pip`

### 1.2 Google Cloud SDK

- **macOS:** `brew install --cask google-cloud-sdk`
- **Linux / WSL:** siga https://cloud.google.com/sdk/docs/install (pacote `google-cloud-cli` via apt).

O `bq` vem junto com o SDK. Feche e abra o terminal depois de instalar e confira com `bq version`.

### 1.3 Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash   # ou: npm install -g @anthropic-ai/claude-code
claude                                           # no primeiro uso, faz login no navegador
```

Documentação: https://docs.claude.com/en/docs/claude-code

### 1.4 Projeto no GCP

Você precisa de um projeto com **billing habilitado**. No modo sandbox (sem cartão), as partições com mais de 60 dias expiram, e a janela do caso tem 90 dias, então a base fica quebrada.

Se ainda não tiver um projeto, crie em https://console.cloud.google.com/projectcreate e vincule uma conta de faturamento. A base inteira tem poucos MB, e o custo do treinamento fica em centavos.

---

## 2. Ligar o seu PC ao BigQuery

Todos os comandos abaixo rodam no terminal. Troque `SEU-PROJETO-GCP` pelo ID do seu projeto (o ID, não o nome; veja com `gcloud projects list`).

### 2.1 Login

São **dois** logins diferentes, e os dois são necessários:

```bash
gcloud auth login                         # para o gcloud e o bq na linha de comando
gcloud auth application-default login     # para o Python (google-cloud-bigquery, Streamlit)
```

Cada um abre o navegador. Use a mesma conta Google, a que tem acesso ao projeto.

### 2.2 Apontar para o projeto

```bash
gcloud config set project SEU-PROJETO-GCP
gcloud auth application-default set-quota-project SEU-PROJETO-GCP
gcloud services enable bigquery.googleapis.com
```

### 2.3 Testar a conexão

```bash
bq --project_id=SEU-PROJETO-GCP query --use_legacy_sql=false 'SELECT 1 AS ok'
```

Se aparecer uma tabelinha com `ok = 1`, o BigQuery está ligado. Para testar também o lado Python (depois do passo 4):

```bash
python3 -c "from google.cloud import bigquery; print(list(bigquery.Client(project='SEU-PROJETO-GCP').query('SELECT 1').result()))"
```

> **Tem mais de uma conta Google no gcloud?** (por exemplo, a do trabalho e a pessoal). Crie uma config só para o treinamento e fixe ela no `.env.local` (passo 3):
>
> ```bash
> gcloud config configurations create treino
> gcloud auth login            # com a conta que acessa o projeto
> gcloud config set project SEU-PROJETO-GCP
> gcloud config configurations list
> ```

---

## 3. Configurar o `.env.local`

O `preparacao/.env` tem os valores padrão e não deve ser editado. Os valores da sua máquina ficam num `.env.local`, que nunca vai para o pacote.

```bash
cd treinamento-ia-data-science/preparacao
cp .env .env.local
```

Abra o `preparacao/.env.local` **no seu editor** e preencha:

```bash
GCP_PROJECT="SEU-PROJETO-GCP"
BQ_LOCATION="US"          # não mude: a base de origem (thelook_ecommerce) fica em US
DATA_REF=""               # vazio = hoje
# só se você criou uma config própria no passo 2:
CLOUDSDK_ACTIVE_CONFIG_NAME="treino"
JIRA_API_TOKEN=""         # opcional, ver passo 7
```

Para carregar essas variáveis em qualquer terminal:

```bash
source preparacao/setup/config.env     # a partir da raiz do pacote
```

---

## 4. Criar o venv do Python

```bash
cd treinamento-ia-data-science/preparacao
python3 -m venv app/.venv
app/.venv/bin/pip install -r app/requirements.txt
```

Isso instala Streamlit, `google-cloud-bigquery`, pandas, altair e o resto. A sessão usa esse mesmo venv.

---

## 5. Criar a base no BigQuery

Ainda em `preparacao/`:

```bash
bash setup/run_setup.sh
```

O script:

1. confere o acesso ao projeto (se faltar login, ele mostra os comandos e oferece rodá-los);
2. cria os datasets `trama_setup`, `trama_raw`, `trama_legacy`, `trama_silver`, `trama_gold` e `trama_gabarito`;
3. gera os dados a partir do dataset público `thelook_ecommerce`, ancorados na data de hoje (90 dias até ontem);
4. roda as checagens (`09_checagens.sql`), que garantem que a história do caso aparece nos dados.

Deu certo quando a saída termina com **`✅ setup concluído`**. Leva poucos minutos e pode ser rodado de novo quando quiser: ele recria tudo do zero.

Para fixar a data da base (por exemplo, para bater com outra pessoa): `DATA_REF=2026-10-02 bash setup/run_setup.sh`.

| Dataset | Conteúdo |
|---|---|
| `trama_raw` | Dados brutos do caso: pedidos, eventos web e app, mídia, campanhas e log de ingestão |
| `trama_legacy` | A dash atual da Growth (com os erros dela) |
| `trama_silver` / `trama_gold` | Vazios: é onde você constrói a solução |
| `trama_setup` / `trama_gabarito` | Parâmetros e solução. **Não abra se quiser resolver sozinho** |

---

## 6. Gerar a pasta da sessão

A partir da raiz do pacote:

```bash
bash preparacao/reset_sessao.sh -y
```

O script copia o `preparacao/sessao_template/` para `sessao-ds101/` e troca os placeholders pelos valores da sua máquina: o `SEU-PROJETO-GCP` do `PEDIDO.md` vira o `GCP_PROJECT` do seu `.env.local`, e o caminho da trava em `.claude/settings.local.json` vira o caminho real da pasta. Ele também deixa `trama_silver` e `trama_gold` vazios.

Deu certo quando aparecem três linhas com ✔ (pasta, memória e histórico, silver e gold). Ele exige que o passo 5 já tenha rodado.

Se preferir, abra o Claude Code **na raiz do pacote** e digite `/reset-sessao`, que roda o mesmo script.

O `CLAUDE.md` da sessão é você quem escreve, junto com o Claude, no começo do caso.

---

## 7. Jira (opcional)

O caso pede um card no Jira. Isso só funciona se você tiver acesso a um Jira e à skill `jira-preencher`, que **não vem no pacote**. Se não tiver, pule: o resto do caso funciona sem Jira.

Se tiver:

1. Gere um token em https://id.atlassian.com/manage-profile/security/api-tokens ("Create API token"). Ele só aparece uma vez.
2. Cole no `preparacao/.env.local`, na linha `JIRA_API_TOKEN=""`, **pelo seu editor**. Nunca cole o token no chat do Claude.

---

## 8. Abrir a sessão e começar

Em um terminal, a partir da raiz do pacote:

```bash
cd sessao-ds101
source ../preparacao/setup/config.env          # projeto, conta do gcloud e token
source ../preparacao/app/.venv/bin/activate    # Python com Streamlit e BigQuery
claude
```

Carregue as variáveis e o venv **antes** de abrir o Claude: a trava da sessão impede o Claude de citar `preparacao/`, então ele depende do que já está no seu terminal.

Primeiro prompt sugerido: *"Leia o PEDIDO.md e a pasta estudos/ e me diga o que entendeu da demanda antes de fazer qualquer coisa."*

Para subir a dash que você construir, use um segundo terminal com o mesmo `source` acima e rode `streamlit run <arquivo-da-dash>.py` dentro de `sessao-ds101/`.

### Recomeçar do zero

Feche o Claude aberto na sessão e rode o passo 6 de novo. Além de recriar a pasta e esvaziar `trama_silver` e `trama_gold`, ele apaga a memória e o histórico do Claude Code dessa pasta. Tudo o que você produziu na sessão se perde.

---

## 9. Problemas comuns

| Sintoma | O que fazer |
|---|---|
| `✘ Defina o seu projeto em preparacao/.env.local` | Faltou o passo 3, ou o `GCP_PROJECT` ainda está `SEU-PROJETO-GCP` |
| `A conta atual do gcloud (...) não acessa o projeto` | Rode os dois logins do passo 2.1 com a conta certa. Se tiver várias contas, use `CLOUDSDK_ACTIVE_CONFIG_NAME` |
| Python reclama de credenciais (`DefaultCredentialsError`) | Faltou `gcloud auth application-default login` |
| `Access Denied` / `bigquery.jobs.create` | Sua conta precisa do papel **BigQuery User** e **BigQuery Data Editor** no projeto (IAM no console) |
| `quota project` / `billing not enabled` | Rode o `set-quota-project` do passo 2.2 e confira o billing do projeto |
| Erro de região / `Not found: Dataset ... was not found in location` | Deixe `BQ_LOCATION="US"` no `.env.local` |
| Algum `ASSERT` do `09_checagens.sql` falhou | Rode de novo com outra data (`DATA_REF=...`). Se persistir, guarde a saída do `00_recon_thelook.sql` e fale com quem conduz o treinamento |
| Dentro da sessão, o Claude diz "Bloqueado pela trava do treinamento" | É esperado: ele tentou sair do escopo. Se bloquear tudo, gere a sessão de novo pelo passo 6 |
| Não existe a pasta `sessao-ds101/` | Rode o passo 6 |
| `streamlit: command not found` | O venv não está ativo: `source ../preparacao/app/.venv/bin/activate` |

### Atalho: deixar o Claude fazer o setup

Se preferir, abra o Claude Code **dentro de `preparacao/`** (nunca na `sessao-ds101/`) e cole o prompt de `preparacao/SETUP_PROMPT.md`. Ele faz os passos 1 a 6 e pede para você rodar o que for interativo (os logins). Para rodar um comando interativo no próprio Claude, digite `! <comando>` no prompt, por exemplo `! gcloud auth login`.
