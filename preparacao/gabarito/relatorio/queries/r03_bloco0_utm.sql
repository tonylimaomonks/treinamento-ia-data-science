-- Bloco 0 · valores reais de utm_source/utm_medium nas compras web, por período (P2)
SELECT
  IF(w.event_date >= p.inicio_b, 'B', 'A')                            AS periodo,
  w.utm_source, w.utm_medium,
  COUNT(DISTINCT w.transaction_id)                                    AS compras,
  LOWER(w.utm_source) IN ('facebook', 'fb', 'ig', 'instagram', 'meta') AS e_meta,
  (w.utm_source = 'facebook' AND w.utm_medium = 'cpc')                AS dash_reconhece_meta
FROM trama_raw.raw_web_events w, trama_setup.params p
WHERE w.event_name = 'purchase' AND w.event_date BETWEEN p.inicio_a AND p.janela_fim
GROUP BY 1, 2, 3, 5, 6
ORDER BY periodo, compras DESC;
