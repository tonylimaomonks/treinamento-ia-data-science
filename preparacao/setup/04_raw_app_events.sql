-- 04 · Export do MMP do app (estilo AppsFlyer in-app events)
--
-- 1 linha por compra rastreada no app. A atribuição é o last click do MMP, que carrega o NOME
-- DA CAMPANHA que trouxe o usuário. Isso inclui campanhas de WEB do Meta: o clique no anúncio
-- abriu o app via deep link.
--   P3 · quem casar campaign_name entre web e app vê que as campanhas "trm_meta_web_*"
--        passaram a converter aqui no período B.

CREATE OR REPLACE TABLE trama_raw.raw_app_events
PARTITION BY DATE(event_time)
OPTIONS (description = 'Export do MMP (in-app events). 1 linha por evento af_purchase. Atribuição last click do MMP.')
AS
SELECT
  TIMESTAMP_ADD(t.created_at, INTERVAL CAST(1 + trama_setup.u(CONCAT('lat|', CAST(t.order_id AS STRING))) * 40 AS INT64) SECOND) AS event_time,
  'af_purchase'                                                           AS event_name,
  CONCAT(CAST(UNIX_MILLIS(TIMESTAMP_TRUNC(t.created_at, DAY)) AS STRING), '-',
         SUBSTR(TO_HEX(MD5(CAST(t.user_id AS STRING))), 1, 16))          AS appsflyer_id,
  CAST(t.user_id AS STRING)                                               AS customer_user_id,
  t.device                                                                AS platform,        -- android / ios
  CASE t.canal
    WHEN 'meta'   THEN 'Facebook Ads'
    WHEN 'google' THEN 'googleadwords_int'
    WHEN 'tiktok' THEN 'tiktokglobal_int'
    WHEN 'crm'    THEN 'Email'
    ELSE 'organic'
  END                                                                     AS media_source,
  t.campaign_name                                                         AS campaign,
  CAST(t.order_id AS STRING)                                              AS af_order_id,
  t.receita                                                               AS event_revenue,
  'BRL'                                                                   AS event_revenue_currency
FROM trama_setup.orders_truth t
WHERE t.plataforma = 'app'
  AND t.rastreado;
