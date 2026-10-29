-- Sessão × gabarito: gold_tracking_coverage_by_day (P1). Soma da janela por plataforma + dias que divergem.
WITH p AS (SELECT * FROM trama_setup.params),
s AS (
  SELECT CAST(date AS DATE) AS date, LOWER(sales_platform) AS sales_platform,
         SUM(pedidos_erp) AS erp, SUM(pedidos_rastreados) AS trk
  FROM trama_gold.gold_tracking_coverage_by_day GROUP BY 1, 2
),
g AS (SELECT date, sales_platform, pedidos_erp AS erp, pedidos_rastreados AS trk FROM trama_gabarito.gold_tracking_coverage_by_day),
j AS (
  SELECT g.date, g.sales_platform, g.erp AS g_erp, g.trk AS g_trk, s.erp AS s_erp, s.trk AS s_trk
  FROM g LEFT JOIN s USING (date, sales_platform) CROSS JOIN p
  WHERE g.date BETWEEN p.janela_inicio AND p.janela_fim
)
SELECT
  sales_platform,
  SUM(g_erp) AS gab_erp, SUM(s_erp) AS ses_erp,
  SUM(g_trk) AS gab_rastreados, SUM(s_trk) AS ses_rastreados,
  COUNTIF(s_erp IS NULL) AS dias_ausentes,
  COUNTIF(s_erp != g_erp OR s_trk != g_trk) AS dias_divergentes,
  IF(COUNTIF(s_erp IS NULL OR s_erp != g_erp OR s_trk != g_trk) = 0, '✔', '✘') AS ok
FROM j GROUP BY 1 ORDER BY 1;

-- P1: os dias com web zerado na sessão devem ser exatamente os 4 dias sem ingestão.
WITH p AS (SELECT * FROM trama_setup.params),
z AS (
  SELECT STRING_AGG(CAST(CAST(c.date AS DATE) AS STRING), ', ' ORDER BY CAST(c.date AS DATE)) AS dias
  FROM trama_gold.gold_tracking_coverage_by_day c CROSS JOIN p
  WHERE LOWER(c.sales_platform) = 'web' AND COALESCE(c.pedidos_rastreados, 0) = 0
    AND CAST(c.date AS DATE) BETWEEN p.janela_inicio AND p.janela_fim
)
SELECT
  ARRAY_TO_STRING(ARRAY(SELECT CAST(d AS STRING) FROM UNNEST(p.dias_sem_ingestao_web) d ORDER BY d), ', ') AS gab_dias_sem_web,
  z.dias AS ses_dias_sem_web,
  IF(ARRAY_TO_STRING(ARRAY(SELECT CAST(d AS STRING) FROM UNNEST(p.dias_sem_ingestao_web) d ORDER BY d), ', ') = z.dias, '✔', '✘') AS ok
FROM p CROSS JOIN z;
