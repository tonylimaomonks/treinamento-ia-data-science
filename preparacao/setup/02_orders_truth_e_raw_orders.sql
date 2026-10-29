-- 02 · Verdade oculta de cada pedido + tabela transacional (ERP) exposta
--
-- trama_setup.orders_truth  → o "DNA" de cada pedido: canal, campanha, plataforma e se foi rastreado.
--                              É daqui que TODAS as outras tabelas derivam. Só o setup/gabarito lê.
-- trama_raw.raw_orders      → o que o ERP enxerga: pedido, cliente, valor e plataforma de venda.
--                              NÃO tem canal de marketing (igual à vida real).
--
-- Snapshot: a janela é copiada do thelook uma vez só, então a base não muda depois do setup.

CREATE OR REPLACE TABLE trama_setup.orders_truth
PARTITION BY dt
AS
WITH pedidos AS (
  SELECT
    o.order_id,
    o.user_id,
    o.status,
    o.created_at,
    o.num_of_item,
    ROUND(SUM(oi.sale_price), 2) AS receita
  FROM `bigquery-public-data.thelook_ecommerce.orders` o
  JOIN `bigquery-public-data.thelook_ecommerce.order_items` oi USING (order_id)
  CROSS JOIN trama_setup.params p
  WHERE DATE(o.created_at) BETWEEN p.janela_inicio AND p.janela_fim
  GROUP BY 1, 2, 3, 4, 5
  -- teto diário (ver params): sorteio determinístico de quais pedidos ficam em cada dia
  QUALIFY ROW_NUMBER() OVER (PARTITION BY DATE(o.created_at)
                             ORDER BY trama_setup.u(CONCAT('keep|', CAST(o.order_id AS STRING))))
          <= ANY_VALUE(p.pedidos_por_dia_base)
             + CAST(FLOOR(trama_setup.u(CONCAT('vol|', CAST(DATE(o.created_at) AS STRING)))
                          * ANY_VALUE(p.pedidos_por_dia_ruido)) AS INT64)
),

sorteios AS (
  SELECT
    x.*,
    DATE(x.created_at) AS dt,
    CASE
      WHEN DATE(x.created_at) >= p.inicio_b THEN 'B'
      WHEN DATE(x.created_at) >= p.inicio_a THEN 'A'
      ELSE 'C'
    END AS periodo,
    trama_setup.u(CONCAT('canal|', CAST(x.order_id AS STRING))) AS u_canal,
    trama_setup.u(CONCAT('camp|',  CAST(x.order_id AS STRING))) AS u_camp,
    trama_setup.u(CONCAT('plat|',  CAST(x.order_id AS STRING))) AS u_plat,
    trama_setup.u(CONCAT('os|',    CAST(x.order_id AS STRING))) AS u_os,
    trama_setup.u(CONCAT('track|', CAST(x.order_id AS STRING))) AS u_track,
    trama_setup.u(CONCAT('utm|',   CAST(x.order_id AS STRING))) AS u_utm,
    p.*  EXCEPT (data_ref, janela_inicio, janela_fim, inicio_a, inicio_b)
  FROM pedidos x
  CROSS JOIN trama_setup.params p
),

com_canal AS (
  SELECT
    s.*,
    IF(s.periodo = 'B', s.share_meta_b, s.share_meta_ab) AS share_meta
  FROM sorteios s
),

canal AS (
  SELECT
    c.*,
    IF(c.u_canal < c.share_meta, 'meta', m.canal) AS canal
  FROM com_canal c
  LEFT JOIN trama_setup.mix_canais m
    ON c.u_canal >= c.share_meta
   AND (c.u_canal - c.share_meta) / (1 - c.share_meta) >= m.lo
   AND ((c.u_canal - c.share_meta) / (1 - c.share_meta) <  m.hi OR m.hi >= 0.9999)
),

campanha AS (
  SELECT
    k.*,
    cp.campaign_name,
    cp.objetivo,
    cp.utm_source AS utm_source_padrao,
    cp.utm_medium AS utm_medium_padrao
  FROM canal k
  JOIN trama_setup.campanhas cp
    ON cp.canal = k.canal
   AND k.u_camp >= cp.lo
   AND (k.u_camp < cp.hi OR cp.hi >= 0.9999)
),

plataforma AS (
  SELECT
    c.*,
    CASE
      WHEN c.objetivo = 'app'  THEN c.p_app_campanha_app
      WHEN c.canal    = 'meta' THEN IF(c.periodo = 'B', c.p_app_meta_web_b, c.p_app_meta_web_a)
      ELSE                          IF(c.periodo = 'B', c.p_app_outros_b,   c.p_app_outros_a)
    END AS p_app
  FROM campanha c
)

SELECT
  order_id,
  user_id,
  status,
  created_at,
  dt,
  periodo,
  num_of_item,
  receita,
  canal,
  campaign_name,
  objetivo,
  IF(u_plat < p_app, 'app', 'web') AS plataforma,
  CASE
    WHEN u_plat < p_app THEN IF(u_os < 0.78, 'android', 'ios')
    ELSE IF(u_os < 0.62, 'mobile', IF(u_os < 0.95, 'desktop', 'tablet'))
  END AS device,

  -- rastreado pelo analytics? (P1 = dia sem ingestão web zera tudo)
  CASE
    WHEN u_plat < p_app THEN u_track < cobertura_app
    ELSE u_track < cobertura_web AND dt NOT IN UNNEST(dias_sem_ingestao_web)
  END AS rastreado,
  (u_plat >= p_app AND dt IN UNNEST(dias_sem_ingestao_web)) AS perdido_por_ingestao,

  -- P2 · UTM do Meta no template novo da agência (só web, só período B)
  (canal = 'meta' AND periodo = 'B' AND u_utm < p_utm_suja_meta_b) AS utm_suja,
  CASE
    WHEN canal = 'meta' AND periodo = 'B' AND u_utm < p_utm_suja_meta_b THEN
      ['fb', 'ig', 'Facebook', 'meta'][OFFSET(CAST(FLOOR(u_utm / p_utm_suja_meta_b * 4) AS INT64))]
    ELSE utm_source_padrao
  END AS utm_source,
  CASE
    WHEN canal = 'meta' AND periodo = 'B' AND u_utm < p_utm_suja_meta_b THEN
      ['cpc', 'paid_social', 'cpc', 'cpc,cpc'][OFFSET(CAST(FLOOR(u_utm / p_utm_suja_meta_b * 4) AS INT64))]
    ELSE utm_medium_padrao
  END AS utm_medium
FROM plataforma;


-- ERP: o que o time de dados enxerga como "verdade transacional"
CREATE OR REPLACE TABLE trama_raw.raw_orders
PARTITION BY DATE(created_at)
OPTIONS (description = 'Pedidos do ERP da Trama Moda. Fonte transacional (verdade de volume e receita). Não contém canal de marketing.')
AS
SELECT
  order_id,
  user_id           AS customer_id,
  status,
  created_at,
  num_of_item       AS num_items,
  receita           AS order_value,
  plataforma        AS sales_platform,
  IF(plataforma = 'app', device, NULL) AS app_os
FROM trama_setup.orders_truth;
