#!/usr/bin/env bash
# Compara a sessão (trama_silver, trama_gold e os HTML de ../sessao-ds101) com o gabarito.
# Só lê: não escreve no BigQuery nem na pasta da sessão.
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
SESSAO="$(cd "$DIR/../../../sessao-ds101" && pwd)"
source "$DIR/../../setup/config.env"
source "$DIR/../../setup/acesso.sh"
checar_acesso || exit 1
BQ=(bq --quiet --project_id="$GCP_PROJECT" --location="${BQ_LOCATION:-US}" query --use_legacy_sql=false --maximum_bytes_billed=1000000000 --max_rows=100 --format=pretty)

echo "▶ inventário (tipo 1 = tabela, 2 = view)"
"${BQ[@]}" "SELECT dataset_id, table_id, type, row_count FROM trama_silver.__TABLES__
            UNION ALL SELECT dataset_id, table_id, type, row_count FROM trama_gold.__TABLES__ ORDER BY 1, 2"

existe() { "${BQ[@]}" --format=csv "SELECT COUNT(*) FROM trama_gold.INFORMATION_SCHEMA.TABLES WHERE table_name = '$1'" 2>/dev/null | tail -1; }

for par in "gold_tracking_coverage_by_day:cobertura" "gold_media_performance_by_day:midia"; do
  view="${par%%:*}"; sql="${par##*:}"
  echo "▶ $view"
  if [[ "$(existe "$view")" != "1" ]]; then echo "✘ não existe em trama_gold"; continue; fi
  "${BQ[@]}" < "$DIR/$sql.sql" || true
done

echo "▶ HTML da sessão"
python3 "$DIR/numeros_html.py" "$SESSAO"

echo "▶ dash"
dash="$(find "$SESSAO" -name '*.py' -not -path '*/.venv/*' -not -path '*/.claude/*' -exec grep -l 'streamlit' {} + 2>/dev/null)"
if [[ -n "$dash" ]]; then
  echo "$dash" | sed "s|$SESSAO/||"
  echo "  views da gold lidas: $(grep -ho 'gold_[a-z_]*' $dash | sort -u | tr '\n' ' ')"
else
  echo "✘ nenhum app Streamlit na sessão"
fi
