-- O job do analytics web no último mês: status SUCCESS mesmo nos dias com 0 linhas
SELECT l.data_date, l.status, l.duration_s, l.rows_written
FROM trama_raw.raw_ingestion_log l, trama_setup.params p
WHERE l.job_name = 'ga4_web_export' AND l.data_date BETWEEN p.inicio_b AND p.janela_fim
ORDER BY l.data_date;
