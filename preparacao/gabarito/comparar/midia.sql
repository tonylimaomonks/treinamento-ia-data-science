-- Sessão × gabarito: gold_media_performance_by_day por canal e período.
-- CPA na régua do gabarito (web + app, sem os 4 dias quebrados) e fração da verba spend_only (P4).
WITH p AS (SELECT * FROM trama_setup.params),
base AS (
  SELECT 'gab' AS fonte, date, channel, spend, CAST(conv_total AS FLOAT64) AS conv, match_status
  FROM trama_gabarito.gold_media_performance_by_day
  UNION ALL
  SELECT 'ses', CAST(date AS DATE), LOWER(channel), CAST(spend AS FLOAT64), CAST(conv_total AS FLOAT64), LOWER(match_status)
  FROM trama_gold.gold_media_performance_by_day
),
agg AS (
  SELECT
    fonte, channel, IF(date >= p.inicio_b, 'B', 'A') AS periodo,
    SUM(spend)                                                       AS spend,
    SAFE_DIVIDE(SUM(IF(match_status = 'spend_only', spend, 0)), SUM(spend)) AS pct_spend_only,
    SAFE_DIVIDE(SUM(IF(date NOT IN UNNEST(p.dias_sem_ingestao_web), spend, 0)),
                SUM(IF(date NOT IN UNNEST(p.dias_sem_ingestao_web), conv, 0)))  AS cpa
  FROM base CROSS JOIN p
  WHERE date BETWEEN p.inicio_a AND p.janela_fim AND channel IN ('meta', 'google', 'tiktok')
  GROUP BY 1, 2, 3
),
w AS (
  SELECT channel, periodo,
    MAX(IF(fonte = 'gab', spend, NULL))          AS gab_spend,  MAX(IF(fonte = 'ses', spend, NULL))          AS ses_spend,
    MAX(IF(fonte = 'gab', pct_spend_only, NULL)) AS gab_spend_only, MAX(IF(fonte = 'ses', pct_spend_only, NULL)) AS ses_spend_only,
    MAX(IF(fonte = 'gab', cpa, NULL))            AS gab_cpa,    MAX(IF(fonte = 'ses', cpa, NULL))            AS ses_cpa
  FROM agg GROUP BY 1, 2
)
SELECT
  channel, periodo,
  ROUND(gab_spend, 0) AS gab_spend, ROUND(ses_spend, 0) AS ses_spend,
  ROUND(gab_spend_only, 3) AS gab_spend_only, ROUND(ses_spend_only, 3) AS ses_spend_only,
  ROUND(gab_cpa, 2) AS gab_cpa, ROUND(ses_cpa, 2) AS ses_cpa,
  CASE
    WHEN ses_spend IS NULL OR ses_cpa IS NULL THEN '✘'
    WHEN ABS(ses_spend / gab_spend - 1) <= 0.01 AND ABS(ses_cpa / gab_cpa - 1) <= 0.02 THEN '✔'
    WHEN ABS(ses_spend / gab_spend - 1) <= 0.05 AND ABS(ses_cpa / gab_cpa - 1) <= 0.10 THEN '⚠'
    ELSE '✘'
  END AS ok
FROM w ORDER BY channel, periodo;
