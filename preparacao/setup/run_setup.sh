#!/usr/bin/env bash
# Setup do caso DS-101 (Trama Moda) no BigQuery.
# Uso: defina o projeto em .env.local (copie do .env) e rode:  bash setup/run_setup.sh
# Idempotente: tudo é CREATE OR REPLACE. Rodar de novo recria a base do zero.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/config.env"
source "$DIR/acesso.sh"
checar_acesso || exit 1
DATA_REF="${DATA_REF:-$(date +%Y-%m-%d)}"
LOCATION="${BQ_LOCATION:-US}"

BQ=(bq --project_id="$GCP_PROJECT" --location="$LOCATION")
Q=("${BQ[@]}" query --use_legacy_sql=false --maximum_bytes_billed=5000000000 --max_rows=200)

echo "▶ projeto=$GCP_PROJECT  data_ref=$DATA_REF  location=$LOCATION"

echo "▶ datasets"
for ds in trama_setup trama_raw trama_legacy trama_silver trama_gold trama_gabarito; do
  if ! "${BQ[@]}" show --dataset "$GCP_PROJECT:$ds" >/dev/null 2>&1; then
    "${BQ[@]}" mk --dataset --description "Treinamento DS-101 (Trama Moda)" "$GCP_PROJECT:$ds"
  fi
done

run() {
  local f="$1"
  echo "▶ $f"
  # @data_ref vira literal: evita depender de query parameter dentro de CTAS/scripts
  sed "s/@data_ref/DATE '$DATA_REF'/g" "$DIR/$f" | "${Q[@]}"
}

# 00 é o único que dá para validar com --dry_run: os demais scripts criam tabelas que
# as instruções seguintes do mesmo arquivo leem (o dry run não enxerga o que ainda não existe).
"${Q[@]}" --dry_run < "$DIR/00_recon_thelook.sql"
run 00_recon_thelook.sql
run 01_params_e_funcoes.sql
run 02_orders_truth_e_raw_orders.sql
run 03_raw_web_events.sql
run 04_raw_app_events.sql
run 05_raw_media_spend_e_campanhas.sql
run 06_raw_ingestion_log.sql
run 07_legacy_dash_growth.sql
run 08_gabarito.sql
run 09_checagens.sql

echo "✅ setup concluído. Base ancorada em $DATA_REF (janela de 90 dias até o dia anterior)."
