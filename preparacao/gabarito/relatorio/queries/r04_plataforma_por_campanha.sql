-- Onde convertem as campanhas de objetivo web: web × app, por canal e período (P3)
WITH conv AS (
  SELECT date, campaign_name, source_canon, 'web' AS plataforma FROM trama_gabarito.silver_web_purchases
  UNION ALL
  SELECT date, campaign_name, source_canon, 'app'               FROM trama_gabarito.silver_app_purchases
)
SELECT
  IF(c.date >= p.inicio_b, 'B', 'A') AS periodo,
  c.source_canon                     AS channel,
  c.plataforma,
  COUNT(*)                           AS conversoes
FROM conv c
JOIN trama_raw.raw_campaigns cp USING (campaign_name)
CROSS JOIN trama_setup.params p
WHERE cp.objective = 'web'
  AND c.date BETWEEN p.inicio_a AND p.janela_fim
  AND c.date NOT IN UNNEST(p.dias_sem_ingestao_web)   -- mesma régua nos dois lados: sem os dias quebrados
  AND c.source_canon IN ('meta', 'google', 'tiktok')
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
