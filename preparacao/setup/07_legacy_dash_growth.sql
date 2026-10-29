-- 07 · A dash atual da Growth (o que a Head olhou)
--
-- Erros de propósito, todos plausíveis numa dash que "sempre funcionou":
--   · conversão = só compra WEB (ignora o app)                          → cai com o P3
--   · canal por match exato de UTM ('facebook' + 'cpc')                 → cai com o P2
--   · spend por INNER JOIN com o catálogo (objective = 'web')           → perde o spend NULL do TikTok (P4)
--   · nenhum controle de dia vazio                                      → cai com o P1

CREATE OR REPLACE VIEW trama_legacy.vw_dash_growth
OPTIONS (description = 'Dash de Growth (legado). Vendas web e CPA por canal, por dia.')
AS
WITH conv AS (
  SELECT
    event_date AS dt,
    CASE
      WHEN utm_source = 'facebook' AND utm_medium = 'cpc' THEN 'Meta'
      WHEN utm_source = 'google'   AND utm_medium = 'cpc' THEN 'Google'
      WHEN utm_source = 'tiktok'   AND utm_medium = 'cpc' THEN 'TikTok'
      ELSE 'Outros'
    END AS canal,
    COUNT(DISTINCT transaction_id) AS vendas_web,
    SUM(value)                     AS receita_web
  FROM trama_raw.raw_web_events
  WHERE event_name = 'purchase'
  GROUP BY 1, 2
),
spend AS (
  SELECT
    s.date AS dt,
    CASE c.platform WHEN 'meta_ads' THEN 'Meta' WHEN 'google_ads' THEN 'Google' WHEN 'tiktok_ads' THEN 'TikTok' END AS canal,
    SUM(s.spend) AS spend
  FROM trama_raw.raw_media_spend s
  JOIN trama_raw.raw_campaigns  c USING (campaign_name)
  WHERE c.objective = 'web'
  GROUP BY 1, 2
)
SELECT
  dt,
  canal,
  COALESCE(conv.vendas_web, 0)  AS vendas_web,
  COALESCE(conv.receita_web, 0) AS receita_web,
  COALESCE(spend.spend, 0)      AS spend
FROM conv
FULL OUTER JOIN spend USING (dt, canal);


-- O "print" que a Head mandou no Slack: último mês × mês anterior
CREATE OR REPLACE VIEW trama_legacy.vw_dash_growth_resumo AS
WITH p AS (SELECT * FROM trama_setup.params),
b AS (
  SELECT
    d.canal,
    IF(d.dt >= p.inicio_b, 'ultimo_mes', 'mes_anterior') AS periodo,
    SUM(d.vendas_web) AS vendas_web,
    SUM(d.spend)      AS spend
  FROM trama_legacy.vw_dash_growth d CROSS JOIN p
  WHERE d.dt BETWEEN p.inicio_a AND p.janela_fim
  GROUP BY 1, 2
)
SELECT
  canal,
  SUM(IF(periodo = 'mes_anterior', vendas_web, 0))                                   AS vendas_web_mes_anterior,
  SUM(IF(periodo = 'ultimo_mes',   vendas_web, 0))                                   AS vendas_web_ultimo_mes,
  ROUND(SAFE_DIVIDE(SUM(IF(periodo = 'ultimo_mes', vendas_web, 0)),
                    SUM(IF(periodo = 'mes_anterior', vendas_web, 0))) - 1, 3)         AS var_vendas,
  ROUND(SAFE_DIVIDE(SUM(IF(periodo = 'mes_anterior', spend, 0)),
                    SUM(IF(periodo = 'mes_anterior', vendas_web, 0))), 2)             AS cpa_mes_anterior,
  ROUND(SAFE_DIVIDE(SUM(IF(periodo = 'ultimo_mes', spend, 0)),
                    SUM(IF(periodo = 'ultimo_mes', vendas_web, 0))), 2)               AS cpa_ultimo_mes
FROM b
GROUP BY canal;
