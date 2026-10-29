-- 03 · Export do analytics web (estilo GA4 achatado)
--
-- Duas origens de linha:
--   (a) sessões de compra → derivadas de orders_truth (web + rastreado): view_item → add_to_cart → begin_checkout → purchase
--   (b) sessões sem compra → navegação real do thelook.events, só para dar textura/volume
--
-- Problemas que nascem aqui:
--   P1 · dias_sem_ingestao_web → ZERO linhas nesses dias (as duas origens)
--   P2 · UTMs do Meta no período B com source/medium fora do padrão
--   P3 · (indireto) a venda migrou pro app, então some daqui

CREATE OR REPLACE TABLE trama_raw.raw_web_events
PARTITION BY event_date
CLUSTER BY event_name
OPTIONS (description = 'Export diário do analytics web (GA4 achatado). 1 linha por evento. Carregado pelo job ga4_web_export.')
AS
WITH
-- (a) sessões de compra --------------------------------------------------------------
compras AS (
  SELECT
    t.*,
    CONCAT(CAST(MOD(MOD(FARM_FINGERPRINT(CAST(t.user_id AS STRING)), 1000000000) + 1000000000, 1000000000) AS STRING),
           '.', CAST(UNIX_SECONDS(TIMESTAMP_TRUNC(t.created_at, DAY)) AS STRING)) AS user_pseudo_id
  FROM trama_setup.orders_truth t
  WHERE t.plataforma = 'web' AND t.rastreado
),
eventos_compra AS (
  SELECT
    DATE(TIMESTAMP_SUB(c.created_at, INTERVAL e.min_antes MINUTE))         AS event_date,
    TIMESTAMP_SUB(c.created_at, INTERVAL e.min_antes MINUTE)               AS event_timestamp,
    e.event_name,
    c.user_pseudo_id,
    CONCAT('o', CAST(c.order_id AS STRING))                                AS ga_session_id,
    IF(e.event_name = 'purchase', CAST(c.order_id AS STRING), NULL)        AS transaction_id,
    IF(e.event_name IN ('purchase', 'begin_checkout'), c.receita, NULL)    AS value,
    c.utm_source,
    c.utm_medium,
    c.campaign_name                                                        AS utm_campaign,
    c.device                                                               AS device_category,
    e.page                                                                 AS page_location
  FROM compras c
  CROSS JOIN UNNEST([
    STRUCT('view_item'      AS event_name, 9 AS min_antes, '/produto'  AS page),
    STRUCT('add_to_cart',                  6,              '/produto'),
    STRUCT('begin_checkout',               3,              '/checkout'),
    STRUCT('purchase',                     0,              '/checkout/obrigado')
  ]) e
),

-- (b) sessões sem compra (textura) ------------------------------------------------------
sessoes_com_compra AS (
  SELECT DISTINCT session_id
  FROM `bigquery-public-data.thelook_ecommerce.events`
  WHERE event_type IN ('purchase', 'cancel')
    AND session_id IS NOT NULL
),
sessoes AS (
  SELECT
    e.session_id,
    DATE(MIN(e.created_at)) AS dt,
    trama_setup.u(CONCAT('s_canal|', e.session_id)) AS u_canal,
    trama_setup.u(CONCAT('s_camp|',  e.session_id)) AS u_camp,
    trama_setup.u(CONCAT('s_utm|',   e.session_id)) AS u_utm,
    trama_setup.u(CONCAT('s_dev|',   e.session_id)) AS u_dev
  FROM `bigquery-public-data.thelook_ecommerce.events` e
  CROSS JOIN trama_setup.params p
  WHERE DATE(e.created_at) BETWEEN p.janela_inicio AND p.janela_fim
    AND e.session_id NOT IN (SELECT session_id FROM sessoes_com_compra)
  GROUP BY e.session_id
),
sessoes_canal AS (
  SELECT
    s.*,
    IF(s.dt >= p.inicio_b, 'B', 'AC') AS periodo,
    IF(s.dt >= p.inicio_b, p.share_meta_b, p.share_meta_ab) AS share_meta,
    p.p_utm_suja_meta_b
  FROM sessoes s
  CROSS JOIN trama_setup.params p
),
sessoes_utm AS (
  SELECT
    s.session_id,
    s.u_dev,
    cp.campaign_name,
    CASE
      WHEN cp.canal = 'meta' AND s.periodo = 'B' AND s.u_utm < s.p_utm_suja_meta_b THEN
        ['fb', 'ig', 'Facebook', 'meta'][OFFSET(CAST(FLOOR(s.u_utm / s.p_utm_suja_meta_b * 4) AS INT64))]
      ELSE cp.utm_source
    END AS utm_source,
    CASE
      WHEN cp.canal = 'meta' AND s.periodo = 'B' AND s.u_utm < s.p_utm_suja_meta_b THEN
        ['cpc', 'paid_social', 'cpc', 'cpc,cpc'][OFFSET(CAST(FLOOR(s.u_utm / s.p_utm_suja_meta_b * 4) AS INT64))]
      ELSE cp.utm_medium
    END AS utm_medium
  FROM sessoes_canal s
  LEFT JOIN trama_setup.mix_canais m
    ON s.u_canal >= s.share_meta
   AND (s.u_canal - s.share_meta) / (1 - s.share_meta) >= m.lo
   AND ((s.u_canal - s.share_meta) / (1 - s.share_meta) <  m.hi OR m.hi >= 0.9999)
  JOIN trama_setup.campanhas cp
    ON cp.canal = IF(s.u_canal < s.share_meta, 'meta', m.canal)
   AND cp.objetivo = 'web'
   AND s.u_camp >= cp.lo
   AND (s.u_camp < cp.hi OR cp.hi >= 0.9999)
),
eventos_navegacao AS (
  SELECT
    DATE(e.created_at)                                                     AS event_date,
    e.created_at                                                           AS event_timestamp,
    CASE e.event_type
      WHEN 'product' THEN 'view_item'
      WHEN 'cart'    THEN 'add_to_cart'
      ELSE 'page_view'
    END                                                                    AS event_name,
    CONCAT(CAST(MOD(MOD(FARM_FINGERPRINT(e.session_id), 1000000000) + 1000000000, 1000000000) AS STRING),
           '.', CAST(UNIX_SECONDS(TIMESTAMP_TRUNC(e.created_at, DAY)) AS STRING)) AS user_pseudo_id,
    e.session_id                                                           AS ga_session_id,
    CAST(NULL AS STRING)                                                   AS transaction_id,
    CAST(NULL AS FLOAT64)                                                  AS value,
    su.utm_source,
    su.utm_medium,
    su.campaign_name                                                       AS utm_campaign,
    IF(su.u_dev < 0.62, 'mobile', IF(su.u_dev < 0.95, 'desktop', 'tablet')) AS device_category,
    e.uri                                                                  AS page_location
  FROM `bigquery-public-data.thelook_ecommerce.events` e
  JOIN sessoes_utm su USING (session_id)
)

SELECT u.*
FROM (
  SELECT * FROM eventos_compra
  UNION ALL
  SELECT * FROM eventos_navegacao
) u
CROSS JOIN trama_setup.params p
WHERE u.event_date BETWEEN p.janela_inicio AND p.janela_fim
  AND u.event_date NOT IN UNNEST(p.dias_sem_ingestao_web);   -- P1
