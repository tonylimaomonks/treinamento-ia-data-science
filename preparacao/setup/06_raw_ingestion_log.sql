-- 06 · Log dos jobs de ingestão
--   P1 · nos dias sem ingestão, o ga4_web_export sai com status SUCCESS, rows_written = 0 e
--        duração de ~3s (dia normal: 38–52s). Nenhum alerta dispara, porque o alerta olha só o status.

CREATE OR REPLACE TABLE trama_raw.raw_ingestion_log
OPTIONS (description = 'Log de execução dos jobs diários de ingestão (orquestrador). 1 linha por job por dia.')
AS
WITH dias AS (
  SELECT d AS dt, p.dias_sem_ingestao_web
  FROM trama_setup.params p, UNNEST(GENERATE_DATE_ARRAY(p.janela_inicio, p.janela_fim)) d
),
web AS (SELECT event_date AS dt, COUNT(*) AS n FROM trama_raw.raw_web_events GROUP BY 1),
app AS (SELECT DATE(event_time) AS dt, COUNT(*) AS n FROM trama_raw.raw_app_events GROUP BY 1),
spd AS (SELECT date AS dt, COUNT(*) AS n FROM trama_raw.raw_media_spend GROUP BY 1),
jobs AS (
  SELECT d.dt, 'ga4_web_export' AS job_name, COALESCE(w.n, 0) AS rows_written,
         d.dt IN UNNEST(d.dias_sem_ingestao_web) AS vazio
  FROM dias d LEFT JOIN web w USING (dt)
  UNION ALL
  SELECT d.dt, 'mmp_app_export', COALESCE(a.n, 0), FALSE FROM dias d LEFT JOIN app a USING (dt)
  UNION ALL
  SELECT d.dt, 'media_spend_connector', COALESCE(s.n, 0), FALSE FROM dias d LEFT JOIN spd s USING (dt)
)
SELECT
  DATE_ADD(dt, INTERVAL 1 DAY) AS run_date,          -- o job de D+1 carrega o dia D
  dt                           AS data_date,
  job_name,
  TIMESTAMP_ADD(TIMESTAMP(DATE_ADD(dt, INTERVAL 1 DAY)),
                INTERVAL CASE job_name WHEN 'ga4_web_export' THEN 7 WHEN 'mmp_app_export' THEN 6 ELSE 5 END HOUR) AS started_at,
  CASE
    WHEN vazio THEN 3
    ELSE CAST(38 + 14 * trama_setup.u(CONCAT('dur|', job_name, CAST(dt AS STRING))) AS INT64)
  END                          AS duration_s,
  'SUCCESS'                    AS status,
  rows_written
FROM jobs;
