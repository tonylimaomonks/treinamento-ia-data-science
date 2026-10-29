-- 08 · Gabarito: solução de referência (silver/gold) + números do veredito
--
-- Tudo aqui é VIEW sobre a bronze, como a gold que o time constrói.
-- O que o time constrói no Ato 1 (trama_silver / trama_gold) deve ter o mesmo contrato.
-- Se o live der errado, o Streamlit aponta para cá (fallback).

-- ── SILVER ────────────────────────────────────────────────────────────────────────────

-- Compras web com canal canônico. Resolve o P2.
CREATE OR REPLACE VIEW trama_gabarito.silver_web_purchases AS
SELECT
  event_date                                  AS date,
  event_timestamp,
  transaction_id                              AS order_id,
  value                                       AS revenue,
  utm_source,
  utm_medium,
  utm_campaign                                AS campaign_name,
  CASE
    WHEN LOWER(utm_source) IN ('facebook', 'fb', 'ig', 'instagram', 'meta') THEN 'meta'
    WHEN LOWER(utm_source) = 'google'                                         THEN 'google'
    WHEN LOWER(utm_source) = 'tiktok'                                         THEN 'tiktok'
    WHEN LOWER(utm_source) = 'crm'                                            THEN 'crm'
    WHEN LOWER(utm_source) = '(direct)'                                       THEN 'direct'
    ELSE 'unassigned'
  END                                         AS source_canon,
  REGEXP_CONTAINS(LOWER(utm_medium), r'(^|[,_])(cpc|cpm|ppc|paid)([,_]|$)') AS is_paid
FROM trama_raw.raw_web_events
WHERE event_name = 'purchase';

-- Compras app com o mesmo vocabulário
CREATE OR REPLACE VIEW trama_gabarito.silver_app_purchases AS
SELECT
  DATE(event_time)                            AS date,
  event_time                                  AS event_timestamp,
  af_order_id                                 AS order_id,
  event_revenue                               AS revenue,
  campaign                                    AS campaign_name,
  CASE media_source
    WHEN 'Facebook Ads'      THEN 'meta'
    WHEN 'googleadwords_int' THEN 'google'
    WHEN 'tiktokglobal_int'  THEN 'tiktok'
    WHEN 'Email'             THEN 'crm'
    WHEN 'organic'           THEN 'organic'
    ELSE 'unassigned'
  END                                         AS source_canon,
  media_source IN ('Facebook Ads', 'googleadwords_int', 'tiktokglobal_int') AS is_paid,
  platform                                    AS app_os
FROM trama_raw.raw_app_events
WHERE event_name = 'af_purchase';

-- ── GOLD ──────────────────────────────────────────────────────────────────────────────

-- Spend × conversão (web + app) por dia e campanha. FULL OUTER + match_status. Resolve P3 e P4.
CREATE OR REPLACE VIEW trama_gabarito.gold_media_performance_by_day AS
WITH conv AS (
  SELECT
    date, campaign_name,
    ANY_VALUE(source_canon)            AS source_canon,   -- 1 campanha = 1 canal; não entra na chave para não duplicar spend
    COUNTIF(plat = 'web')              AS conv_web,
    COUNTIF(plat = 'app')              AS conv_app,
    SUM(IF(plat = 'web', revenue, 0))  AS revenue_web,
    SUM(IF(plat = 'app', revenue, 0))  AS revenue_app
  FROM (
    SELECT date, campaign_name, source_canon, revenue, 'web' AS plat FROM trama_gabarito.silver_web_purchases
    UNION ALL
    SELECT date, campaign_name, source_canon, revenue, 'app'         FROM trama_gabarito.silver_app_purchases
  )
  WHERE campaign_name IS NOT NULL
  GROUP BY 1, 2
),
spend AS (
  SELECT
    s.date,
    s.campaign_name,
    s.platform,
    REGEXP_EXTRACT(s.platform, r'^([a-z]+)_ads$') AS channel,
    SUM(s.spend)       AS spend,
    SUM(s.clicks)      AS clicks,
    SUM(s.impressions) AS impressions
  FROM trama_raw.raw_media_spend s
  GROUP BY 1, 2, 3, 4
)
SELECT
  COALESCE(s.date, c.date)                          AS date,
  COALESCE(s.channel, c.source_canon)               AS channel,
  s.platform,
  COALESCE(s.campaign_name, c.campaign_name)        AS campaign_name,
  cp.objective                                      AS campaign_objective,
  COALESCE(s.spend, 0)                              AS spend,
  COALESCE(s.clicks, 0)                             AS clicks,
  COALESCE(s.impressions, 0)                        AS impressions,
  COALESCE(c.conv_web, 0)                           AS conv_web,
  COALESCE(c.conv_app, 0)                           AS conv_app,
  COALESCE(c.conv_web, 0) + COALESCE(c.conv_app, 0) AS conv_total,
  COALESCE(c.revenue_web, 0)                        AS revenue_web,
  COALESCE(c.revenue_app, 0)                        AS revenue_app,
  CASE
    WHEN s.campaign_name IS NOT NULL AND c.campaign_name IS NOT NULL THEN 'matched'
    WHEN c.campaign_name IS NULL                                     THEN 'spend_only'
    ELSE 'conv_only'
  END                                               AS match_status
FROM spend s
FULL OUTER JOIN conv c
  ON s.date = c.date AND s.campaign_name = c.campaign_name    -- NULL = NULL não casa: é o P4 aparecendo
LEFT JOIN trama_raw.raw_campaigns cp
  ON cp.campaign_name = COALESCE(s.campaign_name, c.campaign_name);

-- Reconciliação ERP × tracking por dia e plataforma. Resolve o P1.
CREATE OR REPLACE VIEW trama_gabarito.gold_tracking_coverage_by_day AS
WITH erp AS (
  SELECT DATE(created_at) AS date, sales_platform, COUNT(*) AS pedidos_erp, SUM(order_value) AS receita_erp
  FROM trama_raw.raw_orders GROUP BY 1, 2
),
trk AS (
  SELECT date, 'web' AS sales_platform, COUNT(DISTINCT order_id) AS pedidos_rastreados FROM trama_gabarito.silver_web_purchases GROUP BY 1
  UNION ALL
  SELECT date, 'app',                   COUNT(DISTINCT order_id)                     FROM trama_gabarito.silver_app_purchases GROUP BY 1
)
SELECT
  e.date,
  e.sales_platform,
  e.pedidos_erp,
  e.receita_erp,
  COALESCE(t.pedidos_rastreados, 0)                                 AS pedidos_rastreados,
  ROUND(SAFE_DIVIDE(COALESCE(t.pedidos_rastreados, 0), e.pedidos_erp), 4) AS cobertura
FROM erp e
LEFT JOIN trk t USING (date, sales_platform);

CREATE OR REPLACE TABLE trama_gabarito.veredito_cpa AS
WITH p AS (SELECT * FROM trama_setup.params),
legado AS (
  SELECT LOWER(canal) AS channel, 'legado' AS regua,
         ROUND(cpa_mes_anterior, 2) AS cpa_a, ROUND(cpa_ultimo_mes, 2) AS cpa_b
  FROM trama_legacy.vw_dash_growth_resumo WHERE canal <> 'Outros'
),
unif AS (
  SELECT
    g.channel,
    'unificada' AS regua,
    ROUND(SAFE_DIVIDE(SUM(IF(g.date <  p.inicio_b, g.spend, 0)), SUM(IF(g.date <  p.inicio_b, g.conv_total, 0))), 2) AS cpa_a,
    ROUND(SAFE_DIVIDE(SUM(IF(g.date >= p.inicio_b, g.spend, 0)), SUM(IF(g.date >= p.inicio_b, g.conv_total, 0))), 2) AS cpa_b
  FROM trama_gabarito.gold_media_performance_by_day g CROSS JOIN p
  WHERE g.date BETWEEN p.inicio_a AND p.janela_fim
    AND g.date NOT IN UNNEST(p.dias_sem_ingestao_web)          -- régua consistente: tira os dias quebrados dos dois lados
    AND g.channel IN ('meta', 'google', 'tiktok')
  GROUP BY 1
)
SELECT *, ROUND(SAFE_DIVIDE(cpa_b, cpa_a) - 1, 3) AS var_cpa FROM legado
UNION ALL
SELECT *, ROUND(SAFE_DIVIDE(cpa_b, cpa_a) - 1, 3) FROM unif;

-- Cascata: por que as "vendas web do Meta" da dash caíram de A para B?
-- Cada degrau desliga um efeito, em ordem. É a verdade oculta (orders_truth), então só o facilitador vê.
CREATE OR REPLACE TABLE trama_gabarito.veredito_cascata_meta AS
WITH p AS (SELECT * FROM trama_setup.params),
t AS (SELECT * FROM trama_setup.orders_truth WHERE canal = 'meta' AND periodo IN ('A', 'B')),
a AS (
  SELECT
    COUNTIF(periodo = 'A')                                                                  AS a_total,
    COUNTIF(periodo = 'A' AND plataforma = 'web' AND rastreado AND NOT utm_suja)            AS a_dash,
    COUNTIF(periodo = 'B')                                                                  AS b_total,
    COUNTIF(periodo = 'B' AND plataforma = 'web')                                           AS b_web,
    COUNTIF(periodo = 'B' AND plataforma = 'web' AND NOT perdido_por_ingestao)              AS b_web_ingerido,
    COUNTIF(periodo = 'B' AND plataforma = 'web' AND rastreado)                             AS b_web_rastreado,
    COUNTIF(periodo = 'B' AND plataforma = 'web' AND rastreado AND NOT utm_suja)            AS b_dash,
    COUNTIF(periodo = 'A' AND plataforma = 'web') / NULLIF(COUNTIF(periodo = 'A'), 0)       AS a_share_web,
    COUNTIF(periodo = 'A' AND plataforma = 'web' AND rastreado)
      / NULLIF(COUNTIF(periodo = 'A' AND plataforma = 'web'), 0)                            AS a_cobertura
  FROM t
)
SELECT ordem, degrau, ROUND(valor) AS vendas_meta_web, descricao FROM (
  SELECT 0 AS ordem, 'Dash · mês anterior' AS degrau, CAST(a_dash AS FLOAT64) AS valor,
         'O que a Growth viu no mês anterior' AS descricao FROM a
  UNION ALL
  SELECT 1, 'Efeito real (volume Meta)', a_dash * b_total / a_total,
         'Se só o volume real do Meta tivesse mudado' FROM a
  UNION ALL
  SELECT 2, 'P3 · migração pro app', a_dash * b_total / a_total * (b_web / b_total) / a_share_web,
         'Somando a venda que passou a acontecer no app' FROM a
  UNION ALL
  SELECT 3, 'P1 · dias sem ingestão', b_web_ingerido * a_cobertura,
         'Somando os 4 dias sem dado web' FROM a
  UNION ALL
  SELECT 4, 'Cobertura normal', b_web_rastreado,
         'Ruído de cobertura do período (≈ neutro)' FROM a
  UNION ALL
  SELECT 5, 'P2 · UTM fora do padrão = Dash · último mês', b_dash,
         'Somando as UTMs que a regra exata não reconhece' FROM a
)
ORDER BY ordem;
