-- ERP × tracking por dia e plataforma, na janela do caso (P1 aparece como cobertura web = 0)
SELECT c.date, c.sales_platform, c.pedidos_erp, c.pedidos_rastreados, c.cobertura,
       c.date IN UNNEST(p.dias_sem_ingestao_web) AS dia_sem_ingestao
FROM trama_gabarito.gold_tracking_coverage_by_day c, trama_setup.params p
WHERE c.date BETWEEN p.janela_inicio AND p.janela_fim
ORDER BY c.date, c.sales_platform;
