-- O "print" da Head: vendas web e CPA por canal na dash legada
SELECT canal, vendas_web_mes_anterior, vendas_web_ultimo_mes, var_vendas, cpa_mes_anterior, cpa_ultimo_mes
FROM trama_legacy.vw_dash_growth_resumo;
