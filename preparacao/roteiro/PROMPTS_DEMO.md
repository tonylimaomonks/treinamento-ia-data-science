# Roteiro ao vivo · DS-101 (Trama Moda)

Roteiro do Tony e cheat sheet pós-treino. Cada bloco de código é um prompt pronto para colar. O texto em itálico é o que falar enquanto o Claude trabalha.

**A regra do jogo:** o Claude é aberto em `sessao-ds101/`, que só tem o `PEDIDO.md`. Tudo o que ele souber durante a sessão vem dessa pasta, do BigQuery ou do que a gente ensinar a ele ao vivo.

---

## Antes de começar (30 min antes, fora da tela)

| # | O quê | Comando (em `preparacao/`) |
|---|---|---|
| 1 | Base atualizada para hoje, com os ASSERTs passando | `bash setup/run_setup.sh` |
| 2 | Relatório-gabarito com os números do dia | `bash gabarito/relatorio/rodar_queries.sh && python3 gabarito/relatorio/gen_data.py` |
| 3 | Sessão limpa: pasta, memória, histórico e silver/gold | `bash reset_sessao.sh -y` |
| 4 | Token do Jira no `preparacao/.env.local` (gerar em https://id.atlassian.com/manage-profile/security/api-tokens). Ele entra no terminal pelo item 5 e nunca aparece na tela | editar o `.env.local` no editor |
| 5 | Projeto, conta do gcloud e token no terminal da sessão, **antes** de abrir o Claude, e o venv com Streamlit ativo | `source ../preparacao/setup/config.env && source ../preparacao/app/.venv/bin/activate` (a partir de `sessao-ds101/`) |
| 6 | Terminais prontos: **T1** sessão (na tela) e **T2** para subir a dash do time, os dois com o item 5 feito | ver o Ato 3 |
| 7 | Dash de referência aberta numa aba escondida (plano B do Ato 3) | `source setup/config.env && source app/.venv/bin/activate && cd gabarito/dash && streamlit run app.py` |
| 8 | Fonte grande no terminal e tema claro no navegador | |

> O venv (`app/.venv`) é criado uma vez só: `python3 -m venv app/.venv && app/.venv/bin/pip install -r app/requirements.txt`. Com ele ativo, a sessão enxerga `streamlit` e `python3` com as bibliotecas do BigQuery, sem o Claude precisar citar nada de `preparacao/` (o hook da sessão bloquearia).
>
> O `.env.local` fica em `preparacao/`, que a trava da sessão bloqueia. O Claude do treino recebe o token só como variável de ambiente (a skill confere com `${JIRA_API_TOKEN:+set}`, sem imprimir) e não consegue ler o arquivo.

---

## Mapa das funcionalidades

| Funcionalidade | Onde aparece | A lição |
|---|---|---|
| Pasta limpa + trava de leitura | Abertura | O contexto é o que você dá a ele |
| `/context` | Ato 0, antes e depois do `/compact` | O contexto é um orçamento, e dá para ver quanto já foi usado |
| `/memory` + hierarquia de `CLAUDE.md` | Ato 0 | O Claude sobe as pastas e carrega todo `CLAUDE.md` que encontra |
| `/init` | Ato 0 | Ponto de partida, não produto final |
| Regras do time no `CLAUDE.md` | Ato 0 | O que transforma o genérico no nosso jeito de trabalhar |
| `.claude/settings.json` + `/permissions` | Ato 0 | Allow, deny e o que é do time × pessoal |
| `!` (bash mode) | Ato 0 | Rodar um comando seu com a saída entrando no contexto |
| Auto memory | Ato 0, Jira, Atos 2 e 3 | O que precisa sobreviver ao `/clear` |
| Skill `/jira-preencher` | Abertura e fechamento do card | Workflow do time empacotado, com rascunho antes de gravar |
| `@arquivo` | Jira e Ato 1 | Apontar o arquivo em vez de descrever |
| `/clear` | Depois do Jira e antes do Ato 3 | Tarefa nova = contexto novo |
| Plan mode (`Shift+Tab`) | Ato 1 | Revisar o plano antes de ele escrever no BigQuery |
| `/compact <foco>` | Fim do Ato 1 | Mesma tarefa, contexto pesado: resumir mantendo o essencial |
| Subagentes em paralelo | Ato 2 | Contexto isolado por agente, e só a conclusão volta |
| `/model` + subagente no Sonnet | Ato 0 e Ato 2 | O Opus julga e orquestra, o Sonnet executa a tarefa fechada |
| Caderno da investigação (HTML de trabalho) | Atos 1 e 2 | O agente entende o problema, e a gente também precisa ver |
| Deep research (pronto em `estudos/`) + plan mode | Ato 3 | Planejar com referência e fonte, e não de memória |
| Dash como código (Streamlit) + `AppTest` | Ato 3 | A dash é arquivo: revisável, versionável e testada antes de abrir |
| `Esc` / `Esc Esc` (`/rewind`) | Quando precisar | Interromper e voltar a um checkpoint |

---

## Abertura (0:00–0:05)

No **T1**:
```bash
cd sessao-ds101 && ls -la && claude     # abrir exatamente aqui: fora de um repo git, o settings.local.json só vale na pasta de abertura
```
*Mostrar que a pasta só tem o `PEDIDO.md` e a trava `.claude/settings.local.json`. Ler a thread da Carla em voz alta. A pergunta do dia: "corta ou não corta?"*

---

## Ato 0 · Preparar o ambiente para a IA (0:05–0:20)

**0.1 · O que o Claude já sabe?**
```
/context
```
*Explicar o orçamento: system prompt, ferramentas, MCPs, arquivos de memória. Quase nada ainda.*

**0.2 · Quais memórias estão carregadas?**
```
/memory
```
*Ponto-chave: o `CLAUDE.md` da raiz aparece carregado, mesmo com o Claude aberto na subpasta. O Claude Code sobe as pastas e carrega todo `CLAUDE.md` que encontra. É por isso que a trava "não olhe a preparação" mora lá. Ainda não existe `CLAUDE.md` do projeto.*

**0.3 · Conferir o ambiente sem sair do Claude**
```
! gcloud config get-value project
```
```
! bq ls --project_id=SEU-PROJETO-GCP trama_raw
```
*O `!` roda o comando no terminal e a saída entra no contexto. Serve para checagens rápidas que você quer que ele veja.*

**0.4 · Gerar o ponto de partida**
```
/init
```
*O `/init` lê a pasta, que aqui é só o `PEDIDO.md`, e escreve um `CLAUDE.md`. Abrir o arquivo e comentar: é genérico, não sabe como o nosso time trabalha. Se já existir um `CLAUDE.md`, o `/init` sugere melhorias em vez de sobrescrever.*

> Para mostrar depois, se sobrar tempo: `CLAUDE_CODE_NEW_INIT=1 claude` e `/init` abrem um fluxo interativo que também passa por skills, hooks e memória pessoal.

**0.5 · Ensinar o jeito do time** (colar o bloco de `roteiro/CLAUDE_ALVO.md`)
```
Acrescente ao CLAUDE.md, abaixo do que o /init gerou, estas regras de trabalho do time,
sem reescrever o resto:

<colar o bloco "Regras de trabalho" + "Convenções de modelagem" do CLAUDE_ALVO.md>
```
*O Claude pede permissão para editar o arquivo: mostrar o diff e aprovar. Estas são as lições dos nossos projetos: bloco 0, dry run, não cravar mecanismo, não misturar réguas.*

**0.6 · Permissões do time**
```
Crie .claude/settings.json liberando bq ls, bq show, bq head, bq query, python3, mkdir,
streamlit run, WebSearch e WebFetch, e negando bq rm e gcloud projects delete.
```
```
/permissions
```
*Mostrar as três camadas: o `settings.json` (do time, vai para o repo), o `settings.local.json` (pessoal, onde está a trava que já veio na pasta) e o que cai em "ask". Daqui para frente, o `bq query` não pede mais aprovação.*

> Opcional, só se o ensaio confirmou que bloqueia: `Leia ../preparacao/PLANEJAMENTO_TREINAMENTO.md`. O esperado é a recusa ou o bloqueio pela regra de deny.
>
> Limite honesto para comentar: são duas travas. O deny de `Read` cobre as ferramentas de arquivo. Um hook `PreToolUse` confere cada comando, caminho e arquivo escrito, inclusive dos subagentes, e barra o que tenta chegar fora do escopo. Nenhuma das duas pega um script que monte o caminho ou o nome do dataset por pedaços. A trava definitiva seria IAM por dataset ou sandbox.

**0.7 · Memória do projeto**
```
Salve na sua memória deste projeto: o projeto GCP e os datasets que podemos ler e escrever,
o prazo (quinta, fim do dia) e que o comitê de verba é na sexta.
```
```
/memory
```
*A diferença que importa: o `CLAUDE.md` são as **regras que a gente escreve** (versionadas, do time). A auto memory é o que o **Claude anota sobre o projeto** para lembrar entre sessões (local, por pasta). As duas voltam depois de um `/clear`.*

**0.8 · Qual modelo para quê**
```
/model
```
*Deixar a sessão principal no **Opus**. A regra 13 do `CLAUDE.md` já diz o resto: todo subagente roda no **Sonnet**. O Opus é quem julga: planeja, arbitra conclusões conflitantes e escreve o veredito. O subagente executa uma tarefa fechada (as queries de uma hipótese), e o Sonnet faz isso bem, mais rápido e mais barato. Com 3 agentes em paralelo, a diferença de custo e de tempo aparece. Vale citar a alternativa `opusplan` no `/model`: Opus no plan mode e Sonnet na execução.*

---

## Jira · abrir a demanda (0:20–0:28)

**J1 · Card a partir do pedido**
```
/jira-preencher Crie o card desta demanda a partir do @PEDIDO.md no projeto DS (AI-DATA),
e não no DAT: tipo Tarefa, filho do épico DS-1, labels treinamento e ds-101. O projeto DS não
tem os campos Cliente nem Solicitante, então não preencha esses dois. A descrição é o pedido,
impessoal e prospectiva, como a skill manda. Use só o que está nesta pasta: não consulte
outros repositórios nem memórias de outros projetos. Me mostre o rascunho antes de gravar.
```
*Mostrar a skill trabalhando: rascunho → aval → gravação → read-back. A skill é o nosso processo empacotado. Ponto bom para comentar: a skill nasceu para outro projeto, e o prompt ajusta só o que muda (projeto, épico e campos). O resto do processo, como a voz da descrição e o rascunho antes de gravar, vem pronto.*

**J2 · Guardar a key**
```
Salve na memória a key do card que você criou.
```

**`/clear` nº 1**
```
/clear
```
*Por quê: abrir o card foi uma tarefa, e investigar é outra. Nada da conversa do Jira ajuda na análise, e carregar isso só gasta contexto.*

```
Qual é o card desta demanda, qual o prazo e quais datasets eu posso escrever?
```
*Ele responde sem reler nada: `CLAUDE.md` e memória sobrevivem ao `/clear`.*

---

## Ato 1 · Tratar (0:28–0:58)

**1.1 · O que a Carla viu + recon**
```
Rode a trama_legacy.vw_dash_growth_resumo e me explique em 3 linhas o que essa dash afirma.
Depois faça o recon da trama_raw: tabelas, schemas e volume diário de cada uma. Me aponte
qualquer coisa estranha na série. Por fim, crie o caderno da investigação (regra 12, práticas
em estudos/caderno_investigacao.md) com esta primeira seção: o que a dash afirma × o que o
recon mostrou.
```
*Ele deve seguir as regras do `CLAUDE.md` sozinho: dry run, `maximum_bytes_billed`, `queries/q01_...sql`. Se o P1 não aparecer, perguntar: "e o raw_ingestion_log?"*

No **T2**: `open investigacao/caderno.html`. *Deixar essa aba aberta até o fim do Ato 2. O agente entende o problema, mas nós também precisamos entender: o caderno é o jeito de ver, em gráfico, o que ele está vendo, e de discordar dele com o dado na frente. A cada achado, é só recarregar a aba.*

**1.2 · Provocação**
```
Pra mim é óbvio: o Meta piorou. Confirma isso pra mim.
```
*Depois da resposta: "registre no caderno o teste que você propôs e o resultado".*
*Esperado: ele pede o teste antes de concordar (regra 3). Se concordar, mostrar a regra no `CLAUDE.md` e pedir o teste.*

**1.3 · Bloco 0**
```
Quais valores utm_source e utm_medium assumem nas compras web, por mês? Na tabela real,
com GROUP BY, não por amostra. Acrescente o bloco 0 ao caderno.
```

**1.4 · Plan mode para construir a silver e a gold** (`Shift+Tab` até "plan mode")
```
Planeje a silver e a gold desta demanda: silver de compras web e app com source canônico e
is_paid (mesmo vocabulário nas duas pontas); gold com as views dos requisitos da dash no
@PEDIDO.md; a performance de mídia com FULL OUTER JOIN e match_status. Tudo como VIEW.
```
*Ler o plano com o time antes de aprovar: nome das views, colunas do contrato, o FULL OUTER. Aprovar e deixar executar. Lição: mudança grande e com escrita passa por plano.*

**1.5 · Reconciliação**
```
Reconcilie ERP × tracking por dia e plataforma usando a gold. Liste os dias com cobertura
web abaixo de 50% e cruze com o raw_ingestion_log. Acrescente ao caderno.
```
*A lição do P1: o job estava SUCCESS. Alerta de status não basta, tem que alertar volume.*

**1.6 · Cobertura do join por verba**
```
Qual a cobertura do join spend × conversão por VERBA, por canal e período? Por que
FULL OUTER e não INNER? Acrescente ao caderno.
```
*O P4 aparece: o spend do TikTok cai em `spend_only` com `campaign_name` NULL.*

**Checkpoint · `/compact`**
```
/context
```
*O contexto está pesado, cheio de output de query. A tarefa é a mesma, então não é caso de `/clear`.*
```
/compact Mantenha: as views criadas e seus contratos, os achados com os números e as queries
que os provam (P1 dias sem ingestão, P2 UTMs fora da regra, P4 spend sem nome), e o caderno
com o build.py que o regera. Descarte os outputs brutos.
```
```
/context
```
*Comparar antes e depois. O foco no `/compact` decide o que sobrevive ao resumo.*

---

## Ato 2 · Veredito (0:58–1:12)

**2.1 · Subagentes em paralelo**
```
Lance 3 agentes em paralelo, cada um com uma hipótese para a queda de vendas web e o CPA
do Meta:
  A) dado faltando / ingestão
  B) rótulo de UTM / classificação de canal
  C) a venda migrou de plataforma (web → app)
Use o Sonnet em cada agente. Cada um escreve as próprias queries em queries/ (prefixo agA_,
agB_, agC_), salva os resultados em results/, roda e devolve: evidência com números, o teste
que refutaria a hipótese e um veredito CONFIRMADA / REFUTADA / PARCIAL. Quando os três
voltarem, você acrescenta uma seção por agente no caderno.
```
*Enquanto rodam: cada agente tem o próprio contexto, e só a conclusão volta. Isso também é gestão de contexto. E os três rodam no Sonnet, enquanto o Opus fica com a síntese, que é onde está o julgamento. O custo: a síntese precisa arbitrar conclusões conflitantes. Só o agente principal escreve no caderno, para os três não disputarem o mesmo arquivo.*

*Recarregar o caderno quando os três voltarem: as três hipóteses lado a lado, cada uma com o veredito e o teste.*

**2.2 · Síntese e régua**
```
Junte as 3 conclusões. Recalcule o CPA por canal na régua unificada (web + app, mesma
atribuição por campanha, excluindo os dias sem ingestão dos DOIS períodos) e compare com a
dash legada. Use o Google como controle positivo: o que ele diz sobre a queda ser
específica do Meta? Feche o caderno com a seção de síntese: a régua unificada, o controle
positivo e o veredito.
```
*O caderno está completo: é a investigação inteira, na ordem em que aconteceu, com cada número vindo de um CSV. É o material de trabalho do time, e não o que vai para o cliente.*

**2.3 · Deixar o conhecimento salvo**
```
Atualize a memória do projeto com o veredito em 3 linhas, os 4 problemas encontrados,
onde estão as queries e os CSVs de cada um, o caminho do caderno e as views da gold com o que
cada uma responde.
```
*É isso que o Ato 3 vai usar depois do `/clear`. O que não estiver salvo aqui, a próxima sessão não sabe.*

---

## Ato 3 · Entregas: HTML executivo e dash (1:12–1:42)

**`/clear` nº 2** (no T1)
```
/clear
```
*Tarefa nova: a investigação acabou, agora são as entregas. O veredito, os achados, o caderno e onde está cada resultado ficaram na memória (2.3).*

```
Qual é o veredito desta demanda e onde estão os resultados que sustentam ele?
```

**Fala · deep research** (sem prompt)
*Antes de planejar uma entrega, vale uma pesquisa de boas práticas: subagentes com busca na web, cada um numa frente (conteúdo, visualização, layout), cada prática com fonte e com como ela se aplica ao caso. Planejar de memória dá o layout médio da internet. Planejar com pesquisa dá decisões com justificativa, que o time pode contestar. Essa pesquisa leva alguns minutos, então ela já está feita: é a pasta `estudos/`, que veio com a sessão. Abrir o `estudos/README.md` na tela.*

> Se quiser mostrar como ela foi feita, este é o prompt (não rodar ao vivo):
> ```
> Lance 3 agentes de pesquisa em paralelo, no Sonnet, com busca na web: R1 conteúdo (o que
> um comitê precisa ver para decidir verba e o que uma dash de qualidade de tracking monitora),
> R2 visualização e design, R3 layout e técnica (HTML e Streamlit). Cada um devolve até 8
> práticas acionáveis, cada uma com a fonte (link) e como se aplica a este caso. Descarte
> conselho sem fonte.
> ```

**3.1 · Plano das duas entregas** (`Shift+Tab` até "plan mode")
```
Planeje as duas entregas finais, usando as pesquisas de estudos/: o HTML executivo
(estudos/html_executivo.md), para enviar ao cliente e o comitê decidir; e a dash de
acompanhamento diário (estudos/dash_acompanhamento.md), para a Growth ver se os problemas
continuam. Os dois seguem estudos/visualizacao_e_design.md. Para cada decisão do plano,
cite a prática que a sustenta. A base é o que já está no caderno e em results/.
```
*Ler o plano com o time antes de aprovar: cada decisão cita uma prática? O HTML executivo abre com a decisão e o impacto em verba? A dash tem um bloco por problema? Discordar de um ponto e pedir ajuste antes de aprovar é parte da aula.*

**3.2 · HTML executivo (para o cliente)**
```
Execute a parte do HTML executivo do plano, no pipeline do CLAUDE.md: CSV em results/ →
relatorio/gen_data.py → const D embutido → Chart.js. O público é o comitê de verba, que
não é técnico: abra com a decisão e o que ela evita em verba, traduza cada problema técnico
para linguagem de negócio e feche com recomendações com dono e prazo. No fim, valide que o
JSON faz parse e que nenhum número foi digitado à mão, e confira o HTML contra o checklist
de estudos/html_executivo.md.
```
*Abrir o caderno e o HTML executivo lado a lado: é a mesma análise, com dois públicos. O caderno mostra como a gente chegou lá. O executivo mostra o que fazer.*

*Plano B: abrir o `preparacao/gabarito/relatorio/relatorio_DS-101.html` fora da tela do Claude.*

**3.3 · Dash de acompanhamento**
```
Execute a parte da dash do plano, em dash/app.py. Ela lê só a trama_gold (crie na gold as
views a mais que o plano pedir) e responde, para cada um dos 4 problemas, se ele continua
acontecendo: o status do último dia, a tendência e um insight em texto calculado a partir
do dado. Mais gráficos e detalhe que o HTML executivo, com filtro de período e de canal. As
queries seguem as regras de custo do CLAUDE.md. Antes de me entregar, rode o app com
streamlit.testing.v1.AppTest e corrija até não sobrar exceção, e confira a dash contra o
checklist de estudos/dash_acompanhamento.md.
```
*Enquanto ele constrói: é "dash como código". No Databricks, a gente faria o mesmo pelo CLI: o dashboard vira um arquivo `.lvdash.json`, versionado no Git e publicado com `databricks bundle deploy`. Aqui o Streamlit faz esse papel: a dash é um arquivo, revisável no PR, que roda igual em qualquer máquina e é testada antes de alguém abrir.*

**3.4 · Abrir a dash** (no **T2**, com o venv ativo)
```bash
streamlit run dash/app.py
```
*Navegar com o time: cada bloco responde a uma pergunta da Growth? O insight em texto bate com o gráfico? Se sobrar tempo, pedir um ajuste ao vivo no T1 (por exemplo, "marque na série os dias sem ingestão") e ver o Streamlit recarregar sozinho.*

*Plano B: mostrar a dash-gabarito que já está aberta (item 7 do "Antes de começar").*

---

## Fechamento · Jira (1:42–1:52)

**J3 · Comentário + anexos**
```
/jira-preencher Comente no card desta demanda (a key está na memória), em 1ª pessoa como eu:
o que eu fiz, o veredito e a resposta para a Growth em tom executivo. Anexe o HTML executivo
e um zip com investigacao/, queries/ e results/. Me mostre o rascunho antes de gravar.
```
*Pontos para mostrar: a voz muda por campo (descrição impessoal × comentário em 1ª pessoa), a estrutura `jira/<EPICO>/<TASK>/comentario-1/`, o upload e o read-back. E a key veio da memória, depois de dois `/clear`.*

---

## Recap (1:52–2:00) · cheat sheet

| Situação | O que usar |
|---|---|
| Mudei de tarefa e nada da conversa importa | `/clear` |
| Mesma tarefa, contexto pesado de outputs | `/compact <o que manter>` |
| Quero ver quanto contexto já usei | `/context` |
| Regra que vale sempre para o time | `CLAUDE.md` do projeto (versionado) |
| Fato do projeto para lembrar entre sessões | Auto memory ("salve na memória…") |
| Preferência ou trava só minha | `settings.local.json` |
| Liberar ou bloquear comandos | `.claude/settings.json` + `/permissions` |
| Começar um projeto novo com o Claude | `/init` e, logo depois, as regras do time |
| Mudança grande, com escrita | Plan mode (`Shift+Tab`) |
| Várias hipóteses independentes | Subagentes em paralelo |
| Entrega nova (relatório, dash, apresentação) | Boas práticas com fonte (deep research em subagentes, ou `estudos/` se já existir) + plan mode |
| Escolher o modelo | Opus na sessão principal (planejar, orquestrar, sintetizar) e Sonnet nos subagentes (`/model`, `opusplan`) |
| Acompanhar o que o agente está vendo | Caderno HTML da investigação, regerado a cada achado a partir dos CSVs |
| Validar um app Streamlit sem abrir o navegador | `streamlit.testing.v1.AppTest` |
| Processo repetitivo do time | Skill (ex.: `/jira-preencher`) |
| Ele foi pelo caminho errado | `Esc` para interromper, `Esc Esc` / `/rewind` para voltar |

---

## Plano B

| Se… | Faça |
|---|---|
| O Claude tentar ler `preparacao/` | `Esc`, e mostrar a regra no `CLAUDE.md` da raiz. A regra de deny deve bloquear antes |
| A gold do time não bater com os requisitos | Mostrar a dash de referência (lê a `trama_gabarito`) |
| A dash do time quebrar no `AppTest` e o tempo apertar | Pedir o erro em uma linha, corrigir uma vez e, se não fechar, mostrar a dash de referência |
| O caderno atrasar o Ato 1 | Pular as atualizações do 1.2 ao 1.6 e pedir uma atualização só, no fim do 1.6 |
| Os subagentes demorarem | Seguir com 2.2 usando o que já voltou e comentar o custo do paralelismo |
| O Jira falhar (token, rede) | Mostrar o rascunho e explicar o fluxo. A gravação fica para depois |
| O tempo estourar | Cortar o 1.6 e o 3.2 (abrir o relatório-gabarito como HTML executivo) e fazer só a dash |
