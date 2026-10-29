-- 05 · Investimento de mídia (conector das plataformas) + catálogo de campanhas
--
-- Spend constante nos 90 dias ("a verba é a mesma"), calibrado pelo CPA real de cada canal
-- no período A: spend_dia = cpa_alvo × conversões_dia_médias(A) × sazonalidade × ruído.
--   P4 · TikTok: parte do spend chega sem campaign_name (o ad_history do conector não cobre
--        os anúncios novos). Vira uma linha/dia com campaign_name NULL, que nunca casa em join
--        por nome. A fração sobe de 20% para 75% no período B.

CREATE OR REPLACE TABLE trama_raw.raw_campaigns
OPTIONS (description = 'Catálogo de campanhas pagas (cadastro da agência). objective = web | app.')
AS
SELECT
  campaign_name,
  CASE canal WHEN 'meta' THEN 'meta_ads' WHEN 'google' THEN 'google_ads' WHEN 'tiktok' THEN 'tiktok_ads' END AS platform,
  objetivo AS objective,
  'active' AS status
FROM trama_setup.campanhas
WHERE canal IN ('meta', 'google', 'tiktok');


CREATE OR REPLACE TABLE trama_raw.raw_media_spend
PARTITION BY date
OPTIONS (description = 'Spend diário por campanha, vindo do conector de cada plataforma. Não traz conversão.')
AS
WITH conv_a AS (
  SELECT campaign_name, canal, COUNT(*) / 30 AS conv_dia
  FROM trama_setup.orders_truth
  WHERE periodo = 'A' AND canal IN ('meta', 'google', 'tiktok')
  GROUP BY 1, 2
),
dias AS (
  SELECT d AS date, IF(d >= p.inicio_b, 'B', 'AC') AS periodo, p.*
  FROM trama_setup.params p, UNNEST(GENERATE_DATE_ARRAY(p.janela_inicio, p.janela_fim)) d
),
base AS (
  SELECT
    d.date,
    d.periodo,
    c.canal,
    c.campaign_name,
    ROUND(
      CASE c.canal WHEN 'meta' THEN d.cpa_alvo_meta WHEN 'google' THEN d.cpa_alvo_google ELSE d.cpa_alvo_tiktok END
      * c.conv_dia
      * (1 + 0.12 * IF(EXTRACT(DAYOFWEEK FROM d.date) IN (1, 7), 1, 0))                    -- fim de semana
      * (0.90 + 0.20 * trama_setup.u(CONCAT('spend|', c.campaign_name, '|', CAST(d.date AS STRING)))),
      2) AS spend,
    IF(d.periodo = 'B', d.p_tiktok_sem_nome_b, d.p_tiktok_sem_nome_a) AS p_sem_nome
  FROM dias d
  CROSS JOIN conv_a c
),
linhas AS (
  -- Meta e Google: 1 linha por campanha-dia, sempre com nome
  SELECT date, canal, campaign_name, spend FROM base WHERE canal <> 'tiktok'
  UNION ALL
  -- TikTok: a parte coberta pelo ad_history mantém o nome...
  SELECT date, canal, campaign_name, ROUND(spend * (1 - p_sem_nome), 2) FROM base WHERE canal = 'tiktok'
  UNION ALL
  -- ...e o resto vira uma linha/dia sem campanha
  SELECT date, 'tiktok', CAST(NULL AS STRING), ROUND(SUM(spend * p_sem_nome), 2)
  FROM base WHERE canal = 'tiktok' GROUP BY date
)
SELECT
  date,
  CASE canal WHEN 'meta' THEN 'meta_ads' WHEN 'google' THEN 'google_ads' ELSE 'tiktok_ads' END AS platform,
  CASE canal WHEN 'meta' THEN 'act_1029384756' WHEN 'google' THEN '418-220-9931' ELSE '7300112233445566' END AS account_id,
  campaign_name,
  spend,
  CAST(ROUND(spend / CASE canal WHEN 'meta' THEN 1.80 WHEN 'google' THEN 2.40 ELSE 0.90 END) AS INT64) AS clicks,
  CAST(ROUND(spend / CASE canal WHEN 'meta' THEN 1.80 WHEN 'google' THEN 2.40 ELSE 0.90 END
                   / CASE canal WHEN 'meta' THEN 0.012 WHEN 'google' THEN 0.045 ELSE 0.008 END) AS INT64) AS impressions,
  TIMESTAMP_ADD(TIMESTAMP(DATE_ADD(date, INTERVAL 1 DAY)), INTERVAL 6 HOUR) AS _synced_at
FROM linhas
WHERE spend > 0;
