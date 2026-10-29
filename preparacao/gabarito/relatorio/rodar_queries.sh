#!/usr/bin/env bash
# Roda cada queries/rNN_*.sql (dry run primeiro) e salva results/rNN_*.csv com o mesmo basename.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/../../setup/config.env"
source "$DIR/../../setup/acesso.sh"
checar_acesso || exit 1
BQ=(bq --project_id="$GCP_PROJECT" --location="${BQ_LOCATION:-US}" query --use_legacy_sql=false --maximum_bytes_billed=1000000000)
mkdir -p "$DIR/results"
for f in "$DIR"/queries/r*.sql; do
  b="$(basename "$f" .sql)"
  "${BQ[@]}" --dry_run < "$f" >/dev/null
  "${BQ[@]}" --format=csv --max_rows=100000 < "$f" > "$DIR/results/$b.csv"
  echo "✔ $b  ($(($(wc -l < "$DIR/results/$b.csv") - 1)) linhas)"
done
