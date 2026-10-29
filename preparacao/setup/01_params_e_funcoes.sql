-- 01 · Parâmetros do caso + função de aleatoriedade determinística
-- Uso: via run_setup.sh, que troca @data_ref por DATE 'AAAA-MM-DD' antes de rodar
--
-- Tudo no setup deriva desta tabela. Mudou um knob aqui → rode o setup inteiro de novo.
-- Janela: 90 dias terminando em data_ref - 1.
--   C = baseline  [D-90, D-61]
--   A = mês anterior [D-60, D-31]
--   B = último mês   [D-30, D-1]   ← onde os problemas acontecem

CREATE OR REPLACE TABLE trama_setup.params AS
SELECT
  @data_ref                                   AS data_ref,
  DATE_SUB(@data_ref, INTERVAL 90 DAY)        AS janela_inicio,
  DATE_SUB(@data_ref, INTERVAL 1 DAY)         AS janela_fim,
  DATE_SUB(@data_ref, INTERVAL 30 DAY)        AS inicio_b,       -- banner "10% off no app" + agência nova no Meta
  DATE_SUB(@data_ref, INTERVAL 60 DAY)        AS inicio_a,

  -- P1 · dias em que a ingestão do analytics web "rodou verde" e gravou zero linhas
  [DATE_SUB(@data_ref, INTERVAL 27 DAY),
   DATE_SUB(@data_ref, INTERVAL 19 DAY),
   DATE_SUB(@data_ref, INTERVAL 12 DAY),
   DATE_SUB(@data_ref, INTERVAL 4 DAY)]       AS dias_sem_ingestao_web,

  -- volume: o thelook concentra pedidos perto de "hoje" (a última semana chega a 10× o início da janela).
  -- Sem teto, o crescimento real do dataset afoga os problemas plantados. Cada dia fica com
  -- pedidos_por_dia_base + ruído determinístico [0, pedidos_por_dia_ruido) pedidos.
  120 AS pedidos_por_dia_base,
  10  AS pedidos_por_dia_ruido,

  -- mix de canal (último clique) — o Meta cai de verdade um pouco no período B (efeito real, pequeno)
  0.35 AS share_meta_ab,        -- C e A
  0.33 AS share_meta_b,         -- B

  -- P3 · probabilidade de a venda acontecer no APP
  0.15 AS p_app_meta_web_a,     -- campanha Meta de web, antes
  0.30 AS p_app_meta_web_b,     -- depois: deep link da agência nova abre o app
  0.30 AS p_app_outros_a,       -- demais canais/objetivo web, antes
  0.40 AS p_app_outros_b,       -- depois: banner "10% off no app"
  0.95 AS p_app_campanha_app,   -- campanha com objetivo app

  -- cobertura de tracking "normal" (nunca é 100%)
  0.88 AS cobertura_web,
  0.92 AS cobertura_app,

  -- P2 · fração das UTMs do Meta (período B) no template novo da agência
  0.25 AS p_utm_suja_meta_b,

  -- P4 · fração do spend de TikTok que o conector entrega sem campaign_name
  0.20 AS p_tiktok_sem_nome_a,
  0.75 AS p_tiktok_sem_nome_b,

  -- CPA "real" (spend ÷ todas as conversões, web + app) — o TikTok é o MAIS caro
  45.0 AS cpa_alvo_meta,
  38.0 AS cpa_alvo_google,
  60.0 AS cpa_alvo_tiktok;

-- u(chave) → uniforme determinística em [0, 1). Mesma chave = mesmo número, sempre.
-- (MOD de INT64 negativo pode ser negativo; o "+ 1e6 mod 1e6" corrige sem ABS, que estoura no INT64 mínimo.)
CREATE OR REPLACE FUNCTION trama_setup.u(chave STRING) AS (
  MOD(MOD(FARM_FINGERPRINT(chave), 1000000) + 1000000, 1000000) / 1000000
);

-- Catálogo de campanhas com peso dentro do canal (pesos ficam escondidos no setup)
CREATE OR REPLACE TABLE trama_setup.campanhas AS
WITH c AS (
  SELECT * FROM UNNEST([
    STRUCT('meta'   AS canal, 'trm_meta_web_acq_prospect'    AS campaign_name, 'web' AS objetivo, 0.25 AS peso, 'facebook' AS utm_source, 'cpc'     AS utm_medium),
    STRUCT('meta',  'trm_meta_web_acq_lookalike',  'web', 0.15, 'facebook', 'cpc'),
    STRUCT('meta',  'trm_meta_web_ret_carrinho',   'web', 0.15, 'facebook', 'cpc'),
    STRUCT('meta',  'trm_meta_web_rtv_visitantes', 'web', 0.15, 'facebook', 'cpc'),
    STRUCT('meta',  'trm_meta_app_install',        'app', 0.20, 'facebook', 'cpc'),
    STRUCT('meta',  'trm_meta_app_reengajamento',  'app', 0.10, 'facebook', 'cpc'),
    STRUCT('google','trm_google_search_marca',     'web', 0.35, 'google',   'cpc'),
    STRUCT('google','trm_google_search_generico',  'web', 0.25, 'google',   'cpc'),
    STRUCT('google','trm_google_pmax_catalogo',    'web', 0.25, 'google',   'cpc'),
    STRUCT('google','trm_google_app_uac',          'app', 0.15, 'google',   'cpc'),
    STRUCT('tiktok','trm_tiktok_web_awareness',    'web', 0.35, 'tiktok',   'cpc'),
    STRUCT('tiktok','trm_tiktok_web_conversao',    'web', 0.45, 'tiktok',   'cpc'),
    STRUCT('tiktok','trm_tiktok_app_install',      'app', 0.20, 'tiktok',   'cpc'),
    STRUCT('crm',   'trm_crm_newsletter_semanal',  'web', 0.70, 'crm',      'email'),
    STRUCT('crm',   'trm_crm_carrinho_abandonado', 'web', 0.30, 'crm',      'email'),
    STRUCT('organic', CAST(NULL AS STRING),        'web', 1.00, 'google',   'organic'),
    STRUCT('direct',  CAST(NULL AS STRING),        'web', 1.00, '(direct)', '(none)')
  ])
)
SELECT
  *,
  COALESCE(SUM(peso) OVER (PARTITION BY canal ORDER BY campaign_name
                           ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) AS lo,
  SUM(peso) OVER (PARTITION BY canal ORDER BY campaign_name
                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)            AS hi
FROM c;

-- Mix dos canais NÃO-Meta, normalizado para somar 1 (a fatia do Meta vem de params).
-- Pesos base: google 0.30 · tiktok 0.10 · crm 0.10 · organic 0.10 · direct 0.05 (= 0.65)
CREATE OR REPLACE TABLE trama_setup.mix_canais AS
WITH m AS (
  SELECT * FROM UNNEST([
    STRUCT(1 AS ordem, 'google' AS canal, 0.30 AS peso_base),
    STRUCT(2, 'tiktok',  0.10), STRUCT(3, 'crm', 0.10),
    STRUCT(4, 'organic', 0.10), STRUCT(5, 'direct', 0.05)
  ])
)
SELECT
  canal,
  peso_base,
  COALESCE(SUM(peso_base) OVER (ORDER BY ordem ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) / 0.65 AS lo,
  SUM(peso_base) OVER (ORDER BY ordem ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / 0.65            AS hi
FROM m;
