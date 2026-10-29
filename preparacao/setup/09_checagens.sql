-- 09 · Checagens automáticas: o caso "funciona"?
-- Cada ASSERT derruba o script se a base não contar a história que o gabarito promete.
-- Se algum falhar, ajuste os knobs em 01_params_e_funcoes.sql e rode o setup de novo.

-- P1 · os dias sem ingestão têm zero linhas web, e o job ficou verde
ASSERT (
  SELECT COUNT(*) FROM trama_raw.raw_web_events w, trama_setup.params p
  WHERE w.event_date IN UNNEST(p.dias_sem_ingestao_web)
) = 0 AS 'P1: há eventos web em dia que deveria estar vazio';

ASSERT (
  SELECT COUNTIF(status = 'SUCCESS' AND rows_written = 0) FROM trama_raw.raw_ingestion_log WHERE job_name = 'ga4_web_export'
) = 4 AS 'P1: o log deveria ter exatamente 4 execuções SUCCESS com 0 linhas';

-- P2 · há UTM fora do padrão para o Meta, e só no período B
ASSERT (
  SELECT COUNT(DISTINCT CONCAT(utm_source, '/', utm_medium))
  FROM trama_raw.raw_web_events w, trama_setup.params p
  WHERE w.event_date >= p.inicio_b AND LOWER(utm_source) IN ('fb', 'ig', 'meta', 'facebook')
) >= 4 AS 'P2: variantes de UTM do Meta não apareceram no período B';

-- P3 · campanhas de web do Meta aparecem no export do app
ASSERT (
  SELECT COUNT(*) FROM trama_raw.raw_app_events WHERE STARTS_WITH(campaign, 'trm_meta_web_')
) > 0 AS 'P3: nenhuma campanha web do Meta convertendo no app';

-- P4 · TikTok com spend sem nome
ASSERT (
  SELECT COUNTIF(campaign_name IS NULL) FROM trama_raw.raw_media_spend WHERE platform = 'tiktok_ads'
) > 0 AS 'P4: não há spend de TikTok sem campaign_name';

-- A história do card: a dash legada mostra o que a Head disse
ASSERT (
  SELECT SAFE_DIVIDE(SUM(vendas_web_ultimo_mes), SUM(vendas_web_mes_anterior)) - 1 FROM trama_legacy.vw_dash_growth_resumo
) BETWEEN -0.40 AND -0.18 AS 'Card: queda de vendas web na dash legada fora de ~-30%';

ASSERT (
  SELECT cpa_ultimo_mes / cpa_mes_anterior FROM trama_legacy.vw_dash_growth_resumo WHERE canal = 'Meta'
) BETWEEN 1.5 AND 2.6 AS 'Card: CPA do Meta na dash legada não "dobrou"';

ASSERT (
  SELECT LOGICAL_AND(t.cpa_ultimo_mes < o.cpa_ultimo_mes)
  FROM trama_legacy.vw_dash_growth_resumo t, trama_legacy.vw_dash_growth_resumo o
  WHERE t.canal = 'TikTok' AND o.canal IN ('Meta', 'Google')
) AS 'Card: TikTok deveria parecer o canal mais barato na dash legada';

-- O veredito: na régua unificada o Meta quase não piorou e o TikTok é o mais caro
ASSERT (
  SELECT var_cpa FROM trama_gabarito.veredito_cpa WHERE regua = 'unificada' AND channel = 'meta'
) BETWEEN -0.10 AND 0.20 AS 'Veredito: CPA unificado do Meta deveria variar pouco';

ASSERT (
  SELECT LOGICAL_AND(t.cpa_b > o.cpa_b)
  FROM trama_gabarito.veredito_cpa t, trama_gabarito.veredito_cpa o
  WHERE t.regua = 'unificada' AND o.regua = 'unificada' AND t.channel = 'tiktok' AND o.channel IN ('meta', 'google')
) AS 'Veredito: TikTok deveria ser o mais caro na régua unificada';

-- Resumo para o facilitador copiar para gabarito/GABARITO.md
SELECT 'legado' AS fonte, * EXCEPT (canal), canal FROM trama_legacy.vw_dash_growth_resumo;
SELECT * FROM trama_gabarito.veredito_cpa ORDER BY regua, channel;
SELECT * FROM trama_gabarito.veredito_cascata_meta;
