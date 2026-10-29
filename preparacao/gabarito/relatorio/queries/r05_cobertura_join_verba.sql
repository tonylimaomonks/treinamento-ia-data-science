-- Cobertura do join spend × conversão POR VERBA, por canal e período (P4)
SELECT
  IF(g.date >= p.inicio_b, 'B', 'A')                    AS periodo,
  g.channel,
  g.match_status,
  g.campaign_name IS NULL                               AS sem_campaign_name,
  ROUND(SUM(g.spend), 2)                                AS spend
FROM trama_gabarito.gold_media_performance_by_day g, trama_setup.params p
WHERE g.date BETWEEN p.inicio_a AND p.janela_fim
  AND g.channel IN ('meta', 'google', 'tiktok')
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4;
