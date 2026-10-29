#!/usr/bin/env bash
# Devolve ../sessao-ds101/ ao estado inicial do treinamento. Rode antes de cada ensaio e na manhã do treino.
#   · recria a pasta a partir de sessao_template/ (só PEDIDO.md + a trava .claude/settings.local.json)
#   · apaga a auto memory e o histórico do Claude Code dessa pasta (~/.claude/projects/<pasta>/)
#   · esvazia os datasets trama_silver e trama_gold no BigQuery
# Uso: bash reset_sessao.sh        (pede confirmação)
#      bash reset_sessao.sh -y     (sem confirmação)
set -euo pipefail

PREP="$(cd "$(dirname "$0")" && pwd)"
SESSAO="$(cd "$PREP/.." && pwd)/sessao-ds101"
TEMPLATE="$PREP/sessao_template"
source "$PREP/setup/config.env"
source "$PREP/setup/acesso.sh"
checar_acesso || exit 1
SLUG="$(echo "$SESSAO" | sed 's/[^a-zA-Z0-9]/-/g')"
CC_DIR="$HOME/.claude/projects/$SLUG"

echo "Vai resetar:"
echo "  · pasta        $SESSAO"
echo "  · Claude Code  $CC_DIR (memória + histórico)"
echo "  · BigQuery     $GCP_PROJECT:trama_silver e trama_gold (todas as tabelas/views)"
if [[ "${1:-}" != "-y" ]]; then
  read -r -p "Confirma? [s/N] " ok
  [[ "$ok" == "s" || "$ok" == "S" ]] || { echo "Cancelado."; exit 1; }
fi

[[ -f "$TEMPLATE/PEDIDO.md" ]] || { echo "Template não encontrado em $TEMPLATE"; exit 1; }
[[ "$(basename "$SESSAO")" == "sessao-ds101" ]] || { echo "Caminho inesperado: $SESSAO"; exit 1; }
[[ "$SLUG" == *sessao-ds101 ]] || { echo "Slug inesperado: $SLUG"; exit 1; }

rm -rf "$SESSAO"
cp -R "$TEMPLATE" "$SESSAO"
# no pacote, o template vem com placeholders (empacotar.sh): aqui viram o projeto e o caminho desta máquina
RAIZ="$(cd "$PREP/.." && pwd)"
grep -rIl -e 'SEU-PROJETO-GCP' -e '/CAMINHO/ATE/treinamento-ia-data-science' "$SESSAO" | while read -r f; do
  sed -i.bak -e "s#SEU-PROJETO-GCP#$GCP_PROJECT#g" -e "s#/CAMINHO/ATE/treinamento-ia-data-science#$RAIZ#g" "$f"
  rm -f "$f.bak"
done
echo "✔ pasta recriada: $(cd "$SESSAO" && find . -type f | sort | tr '\n' ' ')"

rm -rf "$CC_DIR"
echo "✔ memória e histórico do Claude Code da sessão apagados"

BQ=(bq --project_id="$GCP_PROJECT" --location="${BQ_LOCATION:-US}")
if ! "${BQ[@]}" ls 2>/dev/null | grep -qw trama_raw; then
  echo "✘ O projeto $GCP_PROJECT não tem a trama_raw. Rode o setup antes: bash setup/run_setup.sh"
  exit 1
fi
for ds in trama_silver trama_gold; do
  "${BQ[@]}" rm -r -f -d "$GCP_PROJECT:$ds" >/dev/null 2>&1 || true
  "${BQ[@]}" mk --dataset --description "Treinamento DS-101 (Trama Moda)" "$GCP_PROJECT:$ds" >/dev/null
done
echo "✔ trama_silver e trama_gold vazios"

