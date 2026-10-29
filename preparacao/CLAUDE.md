# CLAUDE.md · Preparação do treinamento DS-101 (facilitador)

Material do facilitador do treinamento de Claude Code em Data Science. A sessão ao vivo roda em `../sessao-ds101/`, sem acesso a esta pasta. Idioma: português.

## Mapa
- `PLANEJAMENTO_TREINAMENTO.md`: decisões, cronograma de 2h e pendências.
- `roteiro/PROMPTS_DEMO.md`: roteiro ao vivo, com os prompts, os momentos de `/clear` e `/compact` e o cheat sheet.
- `roteiro/CLAUDE_ALVO.md`: o `CLAUDE.md` que a sessão deve ter ao fim do Ato 0 (de onde colar as regras do time).
- `setup/`: gera a base no BigQuery (`bash setup/run_setup.sh`). Os `ASSERT`s do `09_checagens.sql` garantem a história.
- `setup/guarda_sessao.py`: hook `PreToolUse` da sessão (ligado em `sessao_template/.claude/settings.local.json`). Barra gabarito, `trama_setup`, `preparacao/` e a listagem de datasets e jobs do projeto. Mudou? Teste com eventos JSON no stdin (saída 2 = bloqueou).
- `gabarito/`: números esperados (`GABARITO.md`), o relatório-gabarito HTML (`relatorio/`), a dash-gabarito do Ato 3 (`dash/`, plano B) e a pesquisa de boas práticas de referência (`pesquisa/`). `comparar/comparar_sessao.sh` compara a gold, o HTML e a dash da sessão com o gabarito (só leitura; é o `/comparar-gabarito`). Rodar a dash: `source setup/config.env && source app/.venv/bin/activate && cd gabarito/dash && streamlit run app.py`.
- `app/`: só o venv e as dependências do Streamlit (`requirements.txt`). A sessão ativa esse venv antes de abrir o Claude.
- `reset_sessao.sh`: devolve `../sessao-ds101/` ao estado inicial (use antes do ensaio e antes do treino).
- `empacotar.sh`: gera o zip para enviar a outra pessoa, sem dados desta máquina.
- `.env` (padrões, vai no pacote) + `.env.local` (projeto, conta do gcloud e token do Jira desta máquina, **nunca** vai no pacote). Carregue os dois com `source setup/config.env`. Token do Jira: https://id.atlassian.com/manage-profile/security/api-tokens

## Regras
- **Nunca leia, imprima ou copie o `.env.local`**: ele guarda o token do Jira. Para saber se o token está carregado, use `echo "${JIRA_API_TOKEN:+set}"`.
- Nenhum número de cliente real: a Trama Moda é fictícia e os dados vêm do `thelook_ecommerce`.
- Mudou algum parâmetro em `setup/01`? Rode o setup inteiro de novo e depois `gabarito/relatorio/rodar_queries.sh` + `gen_data.py`.
- A pasta `../sessao-ds101/` só pode conter o que o participante deveria ver. Nada de gabarito lá.
