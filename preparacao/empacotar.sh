#!/usr/bin/env bash
# Gera o pacote do treinamento para enviar a outra pessoa: ../dist/treinamento-ds101-AAAAMMDD.zip
#   · fica de fora o que é desta máquina: .env.local (segredos), app/.venv e caches
#   · a sessão NÃO vai: quem recebe gera a sessao-ds101/ com reset_sessao.sh (ou /reset-sessao)
#   · o projeto GCP vira SEU-PROJETO-GCP, e o caminho absoluto da trava vira um placeholder
#   · quem recebe precisa autenticar: os scripts checam o acesso (setup/acesso.sh) e pedem login
# Uso: bash empacotar.sh
set -euo pipefail

PREP="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$PREP/.." && pwd)"
source "$PREP/setup/config.env"          # só para saber qual projeto trocar
PROJ="$GCP_PROJECT"
[[ "$PROJ" != "SEU-PROJETO-GCP" ]] || { echo "GCP_PROJECT não definido: nada para trocar"; exit 1; }

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
PKG="$STAGE/treinamento-ia-data-science"
mkdir -p "$PKG"

cp "$RAIZ/README.md" "$RAIZ/CLAUDE.md" "$RAIZ/.gitignore" "$PKG/"
rsync -a \
  --exclude '.env.local' --exclude 'app/.venv' --exclude '__pycache__' \
  --exclude '.DS_Store' \
  "$PREP/" "$PKG/preparacao/"
# skills do facilitador (/reset-sessao gera a sessao-ds101/, que não vai no pacote)
mkdir -p "$PKG/.claude" && cp -R "$RAIZ/.claude/skills" "$PKG/.claude/"

# troca o projeto e o caminho desta máquina por placeholders
grep -rIl -e "$PROJ" -e "$RAIZ" "$PKG" | while read -r f; do
  sed -i '' -e "s#$PROJ#SEU-PROJETO-GCP#g" -e "s#$RAIZ#/CAMINHO/ATE/treinamento-ia-data-science#g" "$f"
done

# trava de segurança: nada desta máquina pode sobrar no pacote
EMAIL='[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}'
if grep -rIlE -e "$PROJ" -e "$HOME" -e "$EMAIL" "$PKG"; then
  echo "✘ ainda há dado desta máquina nos arquivos acima; pacote NÃO gerado"; exit 1
fi
[[ ! -e "$PKG/preparacao/.env.local" ]] || { echo "✘ .env.local no pacote"; exit 1; }
# nenhum segredo: token do Jira vazio no .env e nenhum token Atlassian (prefixo ATATT) em lugar nenhum
grep -q '^JIRA_API_TOKEN=""' "$PKG/preparacao/.env" || { echo "✘ JIRA_API_TOKEN preenchido no .env"; exit 1; }
if grep -rIl 'ATATT[A-Za-z0-9_=-]\{20,\}' "$PKG"; then echo "✘ token Atlassian no pacote"; exit 1; fi

mkdir -p "$RAIZ/dist"
ZIP="$RAIZ/dist/treinamento-ds101-$(date +%Y%m%d).zip"
rm -f "$ZIP"
(cd "$STAGE" && zip -qr "$ZIP" treinamento-ia-data-science)
echo "✔ $ZIP ($(unzip -l "$ZIP" | tail -1 | awk '{print $2}') arquivos)"
