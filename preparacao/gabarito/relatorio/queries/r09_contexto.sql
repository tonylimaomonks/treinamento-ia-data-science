-- Datas do caso (para os rótulos do relatório)
SELECT data_ref, janela_inicio, janela_fim, inicio_a, inicio_b, ARRAY_TO_STRING(ARRAY(SELECT CAST(d AS STRING) FROM UNNEST(dias_sem_ingestao_web) d), ',') AS dias_sem_ingestao_web
FROM trama_setup.params;
