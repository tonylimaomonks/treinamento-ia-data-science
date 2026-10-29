-- 00 · Recon do thelook ANTES de gerar qualquer coisa (bloco 0 do próprio setup)
-- Confirma tipos e volume diário recente. O setup assume que:
--   · os *_at são TIMESTAMP
--   · events.session_id é STRING
--   · há pedidos todos os dias da janela (o thelook tem datas futuras, por isso cortamos em D-1)

SELECT table_name, column_name, data_type
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('orders', 'order_items', 'events')
  AND column_name IN ('order_id', 'user_id', 'created_at', 'sale_price', 'session_id', 'event_type', 'traffic_source')
ORDER BY table_name, column_name;

SELECT
  DATE_TRUNC(DATE(created_at), MONTH)                         AS mes,
  COUNT(*)                                                    AS pedidos,
  ROUND(COUNT(*) / COUNT(DISTINCT DATE(created_at)), 1)       AS pedidos_por_dia,
  COUNTIF(created_at > CURRENT_TIMESTAMP())                   AS no_futuro
FROM `bigquery-public-data.thelook_ecommerce.orders`
WHERE DATE(created_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 4 MONTH)
GROUP BY 1
ORDER BY 1;
