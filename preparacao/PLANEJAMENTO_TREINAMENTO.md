# Treinamento — Claude Code para Análise de Dados & Data Science

> Planejamento v2 · 2026-09-30 · owner: Tony Lima
> Público: time de Tech, nível variado, conteúdo **avançado/técnico** · Duração: **2h** · Execução: **demo guiada no GCP do Tony**

---

## 1. Ideia central

O treinamento é **um caso simulado de ponta a ponta**, igual aos cards que chegam no Jira. O time recebe uma demanda com prazo e pressão de negócio e resolve com o Claude Code. O objetivo é mostrar as **funcionalidades do Claude Code** no dia a dia da área: preparar o ambiente, gerenciar contexto, planejar, paralelizar e registrar.

| Ato | Pergunta | Ferramenta | Entregável |
|---|---|---|---|
| **0 · Ambiente** | "O que a IA precisa saber antes de começar?" | `/context`, `/memory`, `/init`, `CLAUDE.md`, `settings.json`, auto memory, `/model` | Projeto preparado: regras do time, permissões, memória e modelo |
| **Abertura no Jira** | "Como a demanda entra?" | Skill `/jira-preencher` | Card criado a partir do `PEDIDO.md` (projeto DS, filho do DS-1) |
| **1 · Tratar** | "Os dados estão certos?" | Claude Code + `bq` CLI + plan mode | silver/gold no BigQuery + reconciliação ERP × tracking + **caderno da investigação** (HTML de trabalho) |
| **2 · Veredito** | "O que aconteceu de verdade?" | Subagentes em paralelo no Sonnet, síntese no Opus | Veredito na régua unificada, fechado no caderno e salvo na memória |
| **3 · Entregas** | "Como a gente comunica e acompanha?" | Deep research (pronto em `estudos/`) + plan mode + HTML/Chart.js + **Streamlit** | HTML executivo para o cliente + dash de acompanhamento diário construída ao vivo |
| **Fechamento** | "Como registra?" | Skill `/jira-preencher` | Comentário + anexos no card |

**Mensagem do treinamento:** o Claude é um par que investiga com você, e não um gerador de SQL. Você entra com critério e ceticismo, ele entra com velocidade e método. As lições vêm de erros reais dos nossos projetos, **sem números de cliente**.

**Decisões fechadas:**
- **Streamlit no lugar do Looker e do Databricks.** É 100% código, sem nenhuma interação manual. Faz o papel da dash "como código" que no Databricks a gente publicaria pelo CLI.
- **A dash é construída na sessão, e não entregue pronta.** O Claude constrói a dash de acompanhamento a partir da `trama_gold` do time. A dash-gabarito (plano B) é a `gabarito/dash/app.py`.
- **Toda entrega começa pelas boas práticas, e a pesquisa já vem pronta.** O deep research (subagentes com busca na web) é citado no Ato 3, mas não roda ao vivo: as pesquisas estão em `sessao-ds101/estudos/`, que vem com a sessão. Os prompts mandam usar esses arquivos, e o plano cita a prática por trás de cada decisão. Os estudos são genéricos de propósito: o `/init` lê a pasta no Ato 0, então nada neles pode entregar o diagnóstico.
- **Três entregas, três públicos.** O **caderno da investigação** (`investigacao/caderno.html`) é para nós: nasce no 1.1 e cresce a cada achado, para o time ver o que os agentes estão vendo. O **HTML executivo** é para o cliente: o comitê decide em 2 minutos. A **dash** é o acompanhamento diário, com um bloco por problema.
- **Opus orquestra, Sonnet executa.** A sessão principal roda no Opus (planejar, arbitrar, sintetizar). Todo subagente é lançado no Sonnet. Está na regra 13 do `CLAUDE.md` e no prompt 2.1.
- **Tudo roda no GCP do Tony.** Quem quiser reproduzir usa o `SETUP_PROMPT.md`.
- **Entram os crimes P1–P4.** P5 (colisão de nome) e P6 (iOS de teste) ficaram de fora para caber em 2h.
- **A sessão roda numa pasta limpa** (`sessao-ds101/`), fora da preparação, só com o `PEDIDO.md`. Isso garante que o Claude comece sem contexto. Duas travas impedem que ele veja a preparação (seção 5).
- **`/clear` e `/compact` têm momentos marcados:** `/clear` depois do Jira e antes das entregas (tarefa nova), e `/compact` no fim do Ato 1 (mesma tarefa, contexto pesado).

---

## 2. O caso: Trama Moda · `DS-101` "Corta 40% do Meta e joga no TikTok?"

Pedido que o time recebe: `sessao-ds101/PEDIDO.md` (thread do Slack, acessos e o contrato da dash). A versão do facilitador, com as pistas explicadas, é a `card/DS-101.md`. Em resumo, a Head de Growth vê na dash que as **vendas web caíram ~30%**, que o **CPA do Meta dobrou** e que o **TikTok é o mais barato**, e quer mover verba na sexta.

**A resposta certa é "não corta".** Todos os números abaixo são garantidos por `ASSERT` no setup:

| # | Problema plantado | Sintoma | Como se descobre | Origem real |
|---|---|---|---|---|
| **P1** | 4 dias sem nenhum evento web; o job fica `SUCCESS` com 0 linhas | Buracos na série; o mês "encolhe" | ERP × tracking por dia; `raw_ingestion_log` | DAT-176 |
| **P2** | UTMs do Meta no template da agência nova (`fb`, `ig/paid_social`, `meta/cpc,cpc`) | Meta perde conversão na dash | Bloco 0 com `GROUP BY utm_source, utm_medium` | macros de canonização |
| **P3** | Campanhas de web do Meta passam a converter no app (deep link + banner "10% off no app") | Web cai, app sobe, e ninguém olha junto | Casar `campaign_name` web × app | DAT-176 |
| **P4** | TikTok: parte do spend chega sem `campaign_name`, e o INNER JOIN descarta | CPA do TikTok "ótimo" | Cobertura do join **por verba** | DAT-188 |

**Veredito calibrado** (simulação com 20 sementes; detalhes em `gabarito/GABARITO.md`):

| Canal | Dash legada | Régua unificada |
|---|---|---|
| Meta | CPA ~1,9× maior | CPA estável (~0%) |
| TikTok | o canal mais barato | o canal mais caro |

O **Google** funciona como controle positivo: ele também "piora" ~30% na dash legada sem ter P2 nem P4. Isso prova que parte da queda é comum a todos os canais.

---

## 3. Base de dados

**`bigquery-public-data.thelook_ecommerce`** (pedidos reais, navegação real e datas até hoje) serve de **snapshot**. Por cima dele entram camadas sintéticas **determinísticas**, geradas com `FARM_FINGERPRINT` (a mesma chave sempre dá o mesmo sorteio).

Pontos confirmados na pesquisa:
- **O thelook muda a cada refresh e tem timestamps no futuro.** Por isso o setup copia a janela uma vez só (`trama_setup.orders_truth`) e corta em D-1.
- **O projeto precisa de billing habilitado.** No sandbox, partições com mais de 60 dias expiram, e a janela do caso tem 90 dias.
- **O sandbox do BigQuery não aceita DML nem streaming.** O setup é 100% CTAS/VIEW.
- **A calibração fecha a partir de ~100 pedidos/dia no thelook.** O `00_recon_thelook.sql` imprime o volume real antes de gerar a base.

```
trama_setup    params (knobs do caso) · u() · campanhas · mix_canais · orders_truth (verdade oculta)
trama_raw      raw_orders (ERP) · raw_web_events (GA4 achatado) · raw_app_events (MMP)
               raw_media_spend (conector) · raw_campaigns · raw_ingestion_log
trama_legacy   vw_dash_growth · vw_dash_growth_resumo   ← o "print" da Head
trama_silver   (vazio: o time constrói)
trama_gold     (vazio: o time constrói; o Streamlit lê daqui)
trama_gabarito silver/gold de referência (views) · veredito_cpa · veredito_cascata_meta
```

**Janela:** 90 dias até D-1. C = baseline, A = mês anterior, B = último mês (onde os problemas acontecem). Todos os knobs ficam em `setup/01_params_e_funcoes.sql`.

---

## 4. Roteiro (2h)

Roteiro com os prompts: `roteiro/PROMPTS_DEMO.md`.

| Tempo | Bloco | O que acontece |
|---|---|---|
| 0:00–0:05 | **Abertura** | `cd sessao-ds101 && claude` numa pasta que só tem o `PEDIDO.md` · thread da Carla lida em voz alta |
| 0:05–0:20 | **Ato 0 · Ambiente** | `/context` → `/memory` (o `CLAUDE.md` da raiz carregado) → `!` para checar `gcloud`/`bq` → `/init` → colar as regras do time → `settings.json` + `/permissions` → salvar fatos na auto memory → `/model` (Opus aqui, Sonnet nos subagentes) |
| 0:20–0:28 | **Jira · abertura** | `/jira-preencher` cria o card a partir do `@PEDIDO.md` (rascunho → aval → grava → read-back) · a key vai para a memória · **`/clear` nº 1** e prova de que a memória sobreviveu |
| 0:28–0:58 | **Ato 1 · Tratar** | Dash legada + recon (P1) + **caderno criado** → provocação "o Meta piorou" → bloco 0 (P2) → **plan mode** para silver/gold → reconciliação → cobertura do join por verba (P4), cada achado entrando no caderno → **`/context` + `/compact` com foco** |
| 0:58–1:12 | **Ato 2 · Veredito** | **3 subagentes em paralelo, no Sonnet** → uma seção por agente no caderno → síntese no Opus, na régua unificada, com o controle positivo do Google → caderno fechado → veredito, achados e caminhos salvos na memória |
| 1:12–1:42 | **Ato 3 · Entregas** | **`/clear` nº 2** → fala sobre deep research e `estudos/` → **plan mode** das duas entregas citando os estudos → HTML executivo (CSV → `gen_data.py` → `const D`) → dash Streamlit em `dash/app.py`, testada com `AppTest` → abrir a dash no navegador |
| 1:42–1:52 | **Jira · fechamento** | `/jira-preencher`: comentário em 1ª pessoa + anexos (relatório e zip das queries), com a key recuperada da memória |
| 1:52–2:00 | **Recap** | Cheat sheet: quando usar `/clear`, `/compact`, `CLAUDE.md`, memória, plan mode e subagentes |

**Momentos de ensino planejados:**
- **Ato 0:** `/init` é ponto de partida. O valor está nas regras do time que a gente acrescenta.
- **Ato 0:** `CLAUDE.md` (regras que o time escreve, versionadas) × auto memory (o que o Claude anota, local por pasta).
- **Depois do Jira:** `/clear` quando muda a tarefa. A memória prova que nada importante se perdeu.
- **Fim do Ato 1:** `/compact` quando a tarefa continua, mas o contexto pesou. O foco decide o que sobrevive.
- **Ato 3:** o `/clear` antes das entregas mostra que o que foi salvo na memória vira competência da próxima sessão.
- **Ato 0 e Ato 2:** o modelo certo para cada papel. O Opus julga e orquestra, e o Sonnet executa as tarefas fechadas dos subagentes, mais rápido e mais barato.
- **Atos 1 e 2:** o agente entende o problema, mas o analista também precisa ver. O caderno é onde o time acompanha o ponto de vista dos agentes e discorda com o dado na frente.
- **Ato 3:** planejar com pesquisa, e não de memória. Cada decisão do plano tem uma fonte que o time pode contestar.
- **Ato 1:** o Tony crava "o Meta piorou", e o Claude monta o teste que refuta (ensina a nunca cravar mecanismo sem dado intermediário).
- **Ato 2:** o controle positivo do Google.
- **Ato 2:** a regra de não misturar réguas (web nativo × app de outro modelo).
- **Ato 3:** a mesma análise vira três materiais com públicos diferentes: o time trabalha no caderno, o comitê decide com o HTML executivo, e a Growth acompanha com a dash.
- **Ato 3:** a dash monitora o **volume**, e não só o **status** do job (a lição do P1).

### Ato 2 · como funcionam os subagentes (6.3)
Um prompt só dispara 3 agentes com escopo isolado, todos no Sonnet:
> "Lance 3 agentes em paralelo. **A:** o problema é de ingestão/dado faltando? **B:** é rótulo/UTM? **C:** a venda migrou de plataforma? Cada um: escreva as queries em `participante/queries/`, rode, e devolva a evidência + o teste que refutaria a sua hipótese + um veredito CONFIRMADA/REFUTADA/PARCIAL. Usem só os datasets do PEDIDO.md."

O ponto a mostrar: **cada agente tem contexto próprio**, os três rodam **ao mesmo tempo**, e o agente principal só recebe as conclusões. Isso resolve a janela de contexto e o tempo de parede. Também vale mostrar o risco: agentes paralelos concluindo coisas conflitantes, e a síntese precisando arbitrar.

### Caderno da investigação (Atos 1 e 2)
- `investigacao/caderno.html`, criado no 1.1 e atualizado no 1.2, 1.3, 1.5, 1.6, 2.1 e 2.2. Uma seção por hipótese: pergunta, arquivo da query, gráfico ou tabela, teste que refutaria e veredito. `investigacao/build.py` regera tudo a partir dos CSVs de `results/` (regra 12).
- No 2.1, só o agente principal escreve no caderno. Os subagentes devolvem os CSVs e a conclusão, e o Opus monta as três seções.
- Fica aberto numa aba no T2 durante os Atos 1 e 2. Vai no zip do fechamento do Jira, mas não é a entrega para o cliente.

### Ato 3 · deep research, HTML executivo e dash
- **Deep research (fala):** o Tony explica a técnica e mostra o prompt de como a pesquisa foi feita, sem rodar. As pesquisas prontas estão em `sessao-ds101/estudos/`: `README.md`, `caderno_investigacao.md`, `html_executivo.md`, `dash_acompanhamento.md` e `visualizacao_e_design.md`. São versões genéricas, sem pistas do caso, derivadas da pesquisa de referência `gabarito/pesquisa/boas_praticas.md` (que é aplicada ao caso e fica só na preparação).
- **Plano (3.1):** plan mode das duas entregas, citando os estudos.
- **HTML executivo (3.2):** para o cliente, visão de negócio. Decisão e impacto em verba primeiro, problemas técnicos traduzidos, recomendações com dono e prazo.
- **Dash (3.3):** `dash/app.py` dentro da sessão, lendo só a `trama_gold`. Um bloco por problema (P1–P4) com o status do último dia, a tendência e um insight em texto calculado do dado, mais filtros de período e canal. Validada com `streamlit.testing.v1.AppTest` antes de abrir.
- **Requisitos da dash no `PEDIDO.md`:** só duas views diárias obrigatórias na gold (`gold_tracking_coverage_by_day` e `gold_media_performance_by_day`). O resto fica a critério do time.
- **Dash-gabarito:** `gabarito/dash/app.py`, lendo a `trama_gabarito` por padrão (`TRAMA_GOLD_DATASET` troca). É o plano B.
- **Ambiente:** o `app/.venv` é ativado no terminal antes de abrir o Claude, para a sessão ter `streamlit` e as bibliotecas do BigQuery sem citar `preparacao/`.

### Jira · abertura e fechamento (6.9)
A skill `/jira-preencher` grava no Jira real (projeto DS · AI-DATA, épico DS-1, site tech-brazil) e entra duas vezes:
- **Abertura:** cria o card a partir do `PEDIDO.md`. A descrição é impessoal e prospectiva (é o pedido).
- **Fechamento:** comentário em 1ª pessoa com o veredito e anexos. A skill monta `jira/<EPICO>/<TASK>/comentario-1/` dentro da sessão e faz o upload.

Ao vivo, ela mostra a regra "rascunho antes de gravar", a voz por campo e o read-back.

⚠️ Os padrões da skill são do projeto DAT (épico, Cliente = outro cliente, Solicitante e o template que sobrescreve a descrição). No treino, o card vai para o projeto **DS (AI-DATA)**, como **Tarefa** filha do épico **DS-1 "Treinamento"**. O DS não tem os campos Cliente nem Solicitante. Os prompts J1 e J3 sobrescrevem isso explicitamente e proíbem consultar outros repositórios, para nada de outro cliente aparecer na tela. O token fica no `preparacao/.env.local`, entra no terminal **antes** de abrir o Claude (`source setup/config.env`) e nunca aparece na tela.

---

## 5. Estrutura do repositório

```
treinamento-ia-data-science/
├── CLAUDE.md                        ← SÓ a trava: "aberto em sessao-ds101/? não olhe fora dela"
├── sessao-ds101/                    ← onde o Claude é aberto no treino (começa só com isto:)
│   ├── PEDIDO.md                    ← a demanda: thread do Slack, acessos, requisitos da dash
│   ├── estudos/                     ← boas práticas prontas (deep research), genéricas, sem pistas do caso
│   └── .claude/settings.local.json  ← trava dura: deny de Read/Edit em preparacao/
└── preparacao/                      ← material do facilitador (nunca aberto na sessão)
    ├── CLAUDE.md                    ← contexto da preparação
    ├── PLANEJAMENTO_TREINAMENTO.md  ← este arquivo
    ├── SETUP_PROMPT.md              ← prompt para reproduzir no GCP de qualquer pessoa
    ├── reset_sessao.sh              ← devolve a sessão ao estado inicial
    ├── empacotar.sh                 ← zip para enviar a outra pessoa (sem dados desta máquina)
    ├── sessao_template/             ← cópia intocada do que a sessão tem no início
    ├── roteiro/PROMPTS_DEMO.md      ← roteiro ao vivo + cheat sheet
    ├── roteiro/CLAUDE_ALVO.md       ← regras do time para colar no Ato 0
    ├── card/DS-101.md               ← versão do facilitador do pedido, com as pistas explicadas
    ├── .env / .env.local            ← padrões (vai no pacote) / projeto, conta e token do Jira desta máquina (não vai)
    ├── setup/                       ← config.env (carrega os .env), acesso.sh, run_setup.sh, 00→09
    ├── app/                         ← venv e requirements.txt do Streamlit
    └── gabarito/                    ← GABARITO.md + relatorio/ (HTML pronto) + dash/ (dash-gabarito) + pesquisa/ (boas práticas de referência)
```

### Por que a sessão não enxerga a preparação
1. **`CLAUDE.md` da raiz (camada suave):** o Claude Code carrega todo `CLAUDE.md` das pastas acima de onde foi aberto. A regra da raiz entra sozinha no contexto da sessão e diz para não ler nada fora de `sessao-ds101/`. Ela é neutra e não revela nada do caso. No Ato 0, o `/memory` mostra esse arquivo carregado, e isso vira aula sobre a hierarquia.
2. **Deny no `settings.local.json` da sessão (camada dura):** é uma regra de permissão, e não uma instrução, então vale mesmo se o modelo "esquecer" a regra. Também vale para os subagentes.
3. **O que cada pasta carrega:** o `preparacao/CLAUDE.md` só entraria se o Claude lesse arquivos de lá, o que o deny bloqueia. A auto memory é por pasta, então a sessão começa com a memória vazia.

## 6. Complementos

| # | Ideia | Status |
|---|---|---|
| 6.1 | Criar uma skill ao vivo (`/relatorio-html`) | Bônus, se sobrar tempo |
| 6.2 | Hook de custo (bloquear `bq query` sem `--maximum_bytes_billed`) | Bônus, se sobrar tempo |
| 6.3 | Subagentes em paralelo | **Entra no Ato 2** |
| 6.4 | Competição por equipes | **Aguardando decisão** (explicação abaixo) |
| 6.7 | Streamlit no lugar do Looker | **Adotado** |
| 6.10 | Boas práticas antes do plano das entregas (deep research) | **Entra no Ato 3**, com a pesquisa pronta em `estudos/` |
| 6.12 | Caderno HTML da investigação | **Entra nos Atos 1 e 2** |
| 6.13 | Opus na sessão principal, Sonnet nos subagentes | **Entra no Ato 0 e no 2.1** |
| 6.1b | Transformar o caderno numa skill (`/caderno`) ao vivo | Bônus, se sobrar tempo |
| 6.8 | Relatório-gabarito HTML + cheat sheet de prompts | **Preparar antes** (depende da base rodada) |
| 6.9 | Fechamento no Jira com a skill `jira-preencher` | **Entra no fechamento** |

### 6.4 · Como seria a competição (já adaptada à demo no seu GCP)
Como só você digita, a competição é um **"bolão de hipóteses"**, e o time participa com as ideias:
1. **Abertura (2 min):** a sala se divide em 3–4 equipes. Cada equipe escreve numa thread do Slack **qual acha que é a causa** e **qual seria a primeira pergunta ao Claude**.
2. **Durante os atos:** em cada checkpoint, você pergunta "qual equipe quer mandar o próximo prompt?". Você roda **o prompt da equipe, do jeito que ela escreveu**. Se o prompt for ruim, o resultado mostra isso, e essa é justamente a aula de prompt.
3. **Pontuação:**
   - +1 por problema (P1–P4) que a equipe apontou **com evidência**;
   - +1 pelo prompt que destravou algo;
   - −1 por cravar mecanismo sem dado.
   Placar numa mensagem fixada.
4. **Fim:** a equipe vencedora escreve a primeira frase do comentário do Jira.

Custo extra: quase zero de preparo, mas o roteiro fica menos previsível. Em 2h, recomendo usar **só nos Atos 1 e 2**.

---

## 7. Pendências

- [x] Setup rodado em 29/09 e de novo em 01/10 no `SEU-PROJETO-GCP` (o de 01/10 limpou as linhas do simulador antigo): os 10 ASSERTs passaram. `GABARITO.md` e relatório-gabarito regerados em 01/10. Ajuste: teto de 120–129 pedidos/dia, porque o thelook concentra pedidos perto de hoje e o crescimento real afogava os crimes
- [x] Números reais no `gabarito/GABARITO.md`
- [x] Relatório-gabarito HTML (`gabarito/relatorio/`)
- [x] Ato 3 redesenhado: pesquisa + relatório de negócio + dash construída na sessão
- [ ] Ensaiar o Ato 1 com o caderno e ver quanto tempo as atualizações somam (o Ato 1 tem 30 min)
- [ ] Ensaiar o Ato 3 cronometrado (a meta é 30 min)
- [x] Pasta da sessão (`sessao-ds101/`) separada da preparação, com `PEDIDO.md` e as duas travas
- [x] Roteiro v2 com Ato 0, Jira na abertura e no fechamento, `/clear` e `/compact`
- [x] `reset_sessao.sh` criado e testado. O projeto, a config do gcloud e o token do Jira desta máquina ficam no `.env.local`, que não vai no pacote. Quem recebe o pacote é obrigado a autenticar (`setup/acesso.sh`)
- [x] Jira: card no projeto DS, Tarefa filha do DS-1 (conferido em 01/10: o DS não tem Cliente nem Solicitante)
- [ ] No ensaio, conferir se a skill aceita o projeto DS sem tentar os campos do DAT, e apagar o card de teste depois (ou reaproveitá-lo no treino)
- [ ] Colar o token do Jira no `preparacao/.env.local` (gerar em https://id.atlassian.com/manage-profile/security/api-tokens)
- [ ] Decidir sobre o 6.4 (bolão)
- [ ] **Ensaio completo cronometrado**, validando: a trava bloqueia a leitura de `preparacao/`; o `/memory` mostra a auto memory; o `/init` numa pasta só com o `PEDIDO.md`; o caderno abrindo e crescendo; os subagentes saindo no Sonnet; o `AppTest` da dash
- [ ] Na manhã do treino: setup com `DATA_REF` vazio → relatório-gabarito → reset da sessão (checklist no topo do roteiro)
