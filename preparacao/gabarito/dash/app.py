"""Dash de acompanhamento · Trama Moda (gabarito do DS-101).

Visão analítica para a Growth e o comitê acompanharem, nos próximos dias, se os
4 problemas de medição do caso continuam acontecendo:

  P1 · ingestão web     cobertura diária pedidos rastreados ÷ pedidos do ERP (alerta de VOLUME)
  P2 · UTMs do Meta     % das compras web do Meta fora do template que a dash legada reconhece
  P3 · web → app        % das conversões das campanhas web do Meta que acontecem no app
  P4 · join TikTok      cobertura do join spend × conversão medida POR VERBA

Mais: CPA por canal (dash legada × régua unificada) e a cascata das vendas web do Meta.

Como rodar (a partir da raiz do treinamento):

    source preparacao/setup/config.env                 # exporta GCP_PROJECT
    source preparacao/app/.venv/bin/activate
    cd preparacao/gabarito/dash && streamlit run app.py

Variáveis de ambiente:
  GCP_PROJECT          projeto do BigQuery (obrigatória; vem do config.env)
  TRAMA_GOLD_DATASET   dataset das views gold (padrão: trama_gabarito). Com trama_gold, a dash
                       lê a gold do time e avisa, bloco a bloco, o que ainda não existe lá.

Custo: só lê views/tabelas pequenas e agregadas, com colunas explícitas, dry run antes de
cada consulta e maximum_bytes_billed = 1 GB. Resultados em cache por 1 hora.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st
from google.api_core import exceptions as gexc
from google.cloud import bigquery

# ── Configuração ─────────────────────────────────────────────────────────────────────────

PROJETO = os.environ.get("GCP_PROJECT", "")
GOLD = os.environ.get("TRAMA_GOLD_DATASET", "trama_gabarito")
GABARITO = "trama_gabarito"  # tabelas de veredito (cascata usa a verdade oculta do setup)
LIMITE_BYTES = 1_000_000_000

# Cores: uma de destaque, cinza de contexto e vermelho só para o que está fora do limiar
DESTAQUE = "#4F46E5"
CINZA = "#94A3B8"
CINZA_ESCURO = "#475569"
ALERTA = "#DC2626"

CANAIS_PAGOS = ["meta", "google", "tiktok"]
NOME_CANAL = {"meta": "Meta", "google": "Google", "tiktok": "TikTok"}

# Limiares (pontos de partida, calibrados com o dado do caso; ver aba "Sobre os dados")
LIM = {
    "p1_atencao": 0.85,   # cobertura do período abaixo disso = atenção (normal: web ~88%, app ~92%)
    "p1_falha_dia": 0.50, # um dia abaixo disso = falha de ingestão (volume despencou)
    "p2_atencao": 0.02,   # % de compras Meta fora do template
    "p2_falha": 0.05,
    "p3_atencao": 0.20,   # % das conversões de campanhas web do Meta que acontecem no app (base ~15%)
    "p3_falha": 0.25,
    "p4_atencao": 0.98,   # cobertura do join por verba abaixo disso = atenção
    "p4_falha": 0.90,
}

# Regra do gabarito (silver_web_purchases): dicionário de source canônico
FONTES_META = {"facebook", "fb", "ig", "instagram", "meta"}

LOCALE_PTBR = {
    "number": {"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["R$ ", ""]},
    "time": {
        "dateTime": "%A, %e de %B de %Y, %X", "date": "%d/%m/%Y", "time": "%H:%M:%S",
        "periods": ["AM", "PM"],
        "days": ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"],
        "shortDays": ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"],
        "months": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                   "agosto", "setembro", "outubro", "novembro", "dezembro"],
        "shortMonths": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set",
                        "out", "nov", "dez"],
    },
}


# ── Formatação pt-BR ─────────────────────────────────────────────────────────────────────

def _milhar(txt: str) -> str:
    return txt.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_pct(v: float | None, casas: int = 1) -> str:
    return "—" if v is None or pd.isna(v) else _milhar(f"{v * 100:,.{casas}f}") + "%"


def fmt_pp(v: float | None) -> str:
    """Diferença em pontos percentuais, com sinal (para o delta do st.metric)."""
    return "" if v is None or pd.isna(v) else ("+" if v >= 0 else "-") + _milhar(f"{abs(v) * 100:,.1f}") + " p.p."


def fmt_brl(v: float | None, casas: int = 2) -> str:
    return "—" if v is None or pd.isna(v) else "R$ " + _milhar(f"{v:,.{casas}f}")


def fmt_int(v: float | None) -> str:
    return "—" if v is None or pd.isna(v) else _milhar(f"{v:,.0f}")


def fmt_data(d) -> str:
    return pd.Timestamp(d).strftime("%d/%m/%Y")


def fmt_dia(d) -> str:
    return pd.Timestamp(d).strftime("%d/%m")


def sem_latex(txt: str) -> str:
    """Escapa o $ de R$ para o Markdown do Streamlit não abrir modo LaTeX."""
    return txt.replace("$", "\\$")


def razao(num: float, den: float) -> float | None:
    return None if not den else num / den


# ── Acesso ao BigQuery ───────────────────────────────────────────────────────────────────

class SemDado(Exception):
    """A view/tabela não existe ou não tem as colunas mínimas: o bloco degrada com aviso."""


@st.cache_resource
def cliente() -> bigquery.Client:
    return bigquery.Client(project=PROJETO, location="US")


def _parametros(params: tuple) -> list:
    return [bigquery.ScalarQueryParameter(nome, tipo, valor) for nome, tipo, valor in params]


@st.cache_data(ttl=3600, show_spinner="Consultando o BigQuery…")
def consultar(sql: str, params: tuple = ()) -> tuple[pd.DataFrame, int]:
    """Dry run (estima bytes) e depois a consulta real com teto de 1 GB. Devolve (df, bytes)."""
    bq = cliente()
    seco = bq.query(sql, job_config=bigquery.QueryJobConfig(
        dry_run=True, use_query_cache=False, query_parameters=_parametros(params)))
    bytes_estimados = seco.total_bytes_processed or 0
    job = bq.query(sql, job_config=bigquery.QueryJobConfig(
        maximum_bytes_billed=LIMITE_BYTES, query_parameters=_parametros(params)))
    return job.to_dataframe(create_bqstorage_client=False), bytes_estimados


REGISTRO: list[dict] = []  # o que cada bloco consultou, para a aba "Sobre os dados"


def ler(nome: str, sql: str, params: tuple = ()) -> pd.DataFrame:
    try:
        df, b = consultar(sql, params)
    except (gexc.NotFound, gexc.BadRequest, gexc.Forbidden) as e:
        REGISTRO.append({"consulta": nome, "bytes": None, "situação": "indisponível"})
        raise SemDado(f"{nome}: {getattr(e, 'message', str(e)).splitlines()[0]}") from e
    REGISTRO.append({"consulta": nome, "bytes": b, "situação": f"{len(df)} linhas"})
    return df


def tab(dataset: str, nome: str) -> str:
    return f"`{PROJETO}.{dataset}.{nome}`"


def colunas_gold() -> dict[str, set[str]]:
    try:
        df = ler("colunas da gold", f"SELECT table_name, column_name FROM {tab(GOLD, 'INFORMATION_SCHEMA.COLUMNS')}")
    except SemDado:
        return {}
    return df.groupby("table_name")["column_name"].agg(set).to_dict()


def exigir(cols: dict, view: str, minimas: set[str]) -> set[str]:
    tem = cols.get(view)
    if tem is None:
        raise SemDado(f"a view `{GOLD}.{view}` não existe.")
    falta = minimas - tem
    if falta:
        raise SemDado(f"a view `{GOLD}.{view}` não tem as colunas {', '.join(sorted(falta))}.")
    return tem


# ── Carga (janela inteira, uma vez; os filtros atuam em pandas) ─────────────────────────

def carregar_calendario() -> tuple[date, date]:
    """Janela fechada = dias que o job de ingestão web já processou (o dado vai até D-1)."""
    df = ler("calendário (log de ingestão)", f"""
        SELECT MIN(data_date) AS inicio, MAX(data_date) AS fim
        FROM {tab('trama_raw', 'raw_ingestion_log')}
        WHERE job_name = 'ga4_web_export'""")
    return df.loc[0, "inicio"], df.loc[0, "fim"]


def carregar_log(p: tuple) -> pd.DataFrame:
    return ler("log de ingestão", f"""
        SELECT data_date AS date, job_name, status, duration_s, rows_written
        FROM {tab('trama_raw', 'raw_ingestion_log')}
        WHERE data_date BETWEEN @inicio AND @fim""", p)


def carregar_cobertura(cols: dict, p: tuple) -> pd.DataFrame:
    exigir(cols, "gold_tracking_coverage_by_day", {"date", "sales_platform", "pedidos_erp", "pedidos_rastreados"})
    return ler("cobertura ERP × tracking", f"""
        SELECT date, sales_platform, SUM(pedidos_erp) AS pedidos_erp, SUM(pedidos_rastreados) AS pedidos_rastreados
        FROM {tab(GOLD, 'gold_tracking_coverage_by_day')}
        WHERE date BETWEEN @inicio AND @fim
        GROUP BY 1, 2""", p)


def carregar_midia(cols: dict, p: tuple) -> pd.DataFrame:
    tem = exigir(cols, "gold_media_performance_by_day", {"date", "channel", "spend", "conv_total", "match_status"})
    nome = "g.campaign_name" if "campaign_name" in tem else "CAST(NULL AS STRING)"
    if "campaign_objective" in tem:
        objetivo, join = "g.campaign_objective", ""
    elif "campaign_name" in tem:
        objetivo = "cp.objective"
        join = f"LEFT JOIN {tab('trama_raw', 'raw_campaigns')} cp ON cp.campaign_name = g.campaign_name"
    else:
        objetivo, join = "CAST(NULL AS STRING)", ""
    soma = lambda c: f"SUM(g.{c})" if c in tem else "CAST(NULL AS INT64)"  # noqa: E731
    df = ler("mídia × conversão", f"""
        SELECT g.date, g.channel, g.match_status, {nome} AS campaign_name, {objetivo} AS objetivo,
               SUM(g.spend) AS spend, SUM(g.conv_total) AS conv_total,
               {soma('conv_web')} AS conv_web, {soma('conv_app')} AS conv_app
        FROM {tab(GOLD, 'gold_media_performance_by_day')} g {join}
        WHERE g.date BETWEEN @inicio AND @fim
        GROUP BY 1, 2, 3, 4, 5""", p)
    df.attrs["tem_nome"] = "campaign_name" in tem
    df.attrs["tem_plataforma"] = {"conv_web", "conv_app"} <= tem
    return df


def carregar_utm(p: tuple) -> pd.DataFrame:
    """Bloco 0 diário das UTMs das compras web (bronze, agregado). Mesma regra da silver do gabarito."""
    df = ler("UTMs das compras web", f"""
        SELECT event_date AS date, utm_source, utm_medium, COUNT(DISTINCT transaction_id) AS compras
        FROM {tab('trama_raw', 'raw_web_events')}
        WHERE event_name = 'purchase' AND event_date BETWEEN @inicio AND @fim
        GROUP BY 1, 2, 3""", p)
    df["e_meta"] = df["utm_source"].str.lower().isin(FONTES_META)
    df["template_padrao"] = (df["utm_source"] == "facebook") & (df["utm_medium"] == "cpc")
    df["template"] = df["utm_source"].fillna("∅") + " / " + df["utm_medium"].fillna("∅")
    return df


def carregar_legado() -> pd.DataFrame:
    return ler("dash legada", f"""
        SELECT canal, vendas_web_mes_anterior, vendas_web_ultimo_mes, cpa_mes_anterior, cpa_ultimo_mes
        FROM {tab('trama_legacy', 'vw_dash_growth_resumo')}""")


def carregar_cascata() -> pd.DataFrame:
    return ler("cascata do Meta", f"""
        SELECT ordem, degrau, vendas_meta_web, descricao
        FROM {tab(GABARITO, 'veredito_cascata_meta')} ORDER BY ordem""")


def carregar_veredito_cpa() -> pd.DataFrame:
    return ler("veredito CPA (gabarito)", f"""
        SELECT channel, regua, cpa_a, cpa_b, var_cpa FROM {tab(GABARITO, 'veredito_cpa')}""")


def tentar(func, *args):
    """Roda uma carga; se faltar dado, devolve (None, motivo) em vez de quebrar a página."""
    try:
        return func(*args), None
    except SemDado as e:
        return None, str(e)


# ── Cálculos (todas as razões são razão de somas) ────────────────────────────────────────

def entre(df: pd.DataFrame, ini, fim) -> pd.DataFrame:
    d = pd.to_datetime(df["date"])
    return df[(d >= pd.Timestamp(ini)) & (d <= pd.Timestamp(fim))]


def serie_cobertura(cob: pd.DataFrame, plataformas: list[str]) -> pd.DataFrame:
    base = cob[cob["sales_platform"].isin(plataformas)]
    s = base.groupby("date", as_index=False)[["pedidos_erp", "pedidos_rastreados"]].sum()
    s["cobertura"] = s["pedidos_rastreados"] / s["pedidos_erp"]
    return s.sort_values("date")


def serie_p2(utm: pd.DataFrame) -> pd.DataFrame:
    m = utm[utm["e_meta"]].assign(fora=lambda d: d["compras"].where(~d["template_padrao"], 0))
    s = m.groupby("date", as_index=False).agg(compras=("compras", "sum"), fora=("fora", "sum"))
    s["pct_fora"] = s["fora"] / s["compras"]
    return s.sort_values("date")


def serie_p3(midia: pd.DataFrame, canal: str = "meta") -> pd.DataFrame:
    m = midia[(midia["channel"] == canal) & (midia["objetivo"] == "web")]
    s = m.groupby("date", as_index=False)[["conv_app", "conv_total"]].sum().sort_values("date")
    s["pct_app"] = s["conv_app"] / s["conv_total"]
    return s


def serie_p4(midia: pd.DataFrame, canal: str = "tiktok") -> pd.DataFrame:
    m = midia[midia["channel"] == canal].assign(casou=lambda d: d["spend"].where(d["match_status"] == "matched", 0))
    s = m.groupby("date", as_index=False).agg(spend=("spend", "sum"), casou=("casou", "sum")).sort_values("date")
    s["cobertura"] = s["casou"] / s["spend"]
    return s


def rolante(s: pd.DataFrame, num: str, den: str, janela: int = 7) -> pd.Series:
    """Razão de somas móvel (7 dias), para séries de volume diário baixo."""
    s = s.sort_values("date")
    return s[num].rolling(janela, min_periods=3).sum() / s[den].rolling(janela, min_periods=3).sum()


def status(valor, atencao, falha, maior_e_melhor: bool) -> tuple[str, str, str]:
    """(cor, ícone, texto): status sempre com ícone e texto, não só cor."""
    if valor is None or pd.isna(valor):
        return "gray", ":material/help:", "Sem dado"
    ruim = (lambda v, l: v < l) if maior_e_melhor else (lambda v, l: v > l)
    if ruim(valor, falha):
        return "red", ":material/error:", "Falha"
    if ruim(valor, atencao):
        return "orange", ":material/warning:", "Atenção"
    return "green", ":material/check_circle:", "OK"


def cpa_por_canal(midia: pd.DataFrame, ini, fim, excluir: set) -> pd.DataFrame:
    m = entre(midia, ini, fim)
    m = m[m["channel"].isin(CANAIS_PAGOS) & ~pd.to_datetime(m["date"]).isin(excluir)]
    g = m.groupby("channel", as_index=False)[["spend", "conv_total"]].sum()
    g["cpa"] = g["spend"] / g["conv_total"].where(g["conv_total"] > 0)
    return g


# ── Gráficos ─────────────────────────────────────────────────────────────────────────────

def camada_eventos(eventos: dict, ini, fim) -> list:
    """Faixas dos dias sem ingestão web + linhas verticais dos eventos do caso, dentro do período."""
    camadas = []
    dias = [d for d in eventos["dias_sem_ingestao"] if pd.Timestamp(ini) <= d <= pd.Timestamp(fim)]
    if dias:
        faixa = pd.DataFrame({"ini": [d - timedelta(hours=12) for d in dias], "fim": [d + timedelta(hours=12) for d in dias],
                              "rotulo": ["dia sem ingestão web"] * len(dias)})
        camadas.append(alt.Chart(faixa).mark_rect(color=ALERTA, opacity=0.12).encode(
            x="ini:T", x2="fim:T", tooltip=[alt.Tooltip("rotulo:N", title="Evento")]))
    marcos = [(d, r) for d, r in eventos["marcos"] if pd.Timestamp(ini) <= d <= pd.Timestamp(fim)]
    if marcos:
        mdf = pd.DataFrame(marcos, columns=["data", "rotulo"])
        base = alt.Chart(mdf)
        camadas.append(base.mark_rule(color=CINZA_ESCURO, strokeDash=[4, 3]).encode(x="data:T", tooltip=["rotulo"]))
        camadas.append(base.mark_text(align="left", dx=4, dy=2, baseline="top", fontSize=11, color=CINZA_ESCURO)
                       .encode(x="data:T", y=alt.value(0), text="rotulo"))
    return camadas


def grafico_linha(df: pd.DataFrame, y: str, titulo_y: str, eventos: dict, ini, fim, *, cor: str | None = None,
                  serie: str | None = None, destaque: str | None = None, piso: float | None = None,
                  formato: str = ".0%", tooltip_extra: list | None = None, altura: int = 280) -> alt.LayerChart:
    x = alt.X("date:T", title=None, axis=alt.Axis(format="%d/%m", labelAngle=0))
    enc = dict(x=x, y=alt.Y(f"{y}:Q", title=titulo_y, axis=alt.Axis(format=formato)),
               tooltip=[alt.Tooltip("date:T", title="Dia", format="%d/%m/%Y"),
                        alt.Tooltip(f"{y}:Q", title=titulo_y, format=formato.replace("0", "1", 1) if "%" in formato else formato)]
               + (tooltip_extra or []))
    if serie:
        # Cor de destaque só para a série que importa; o resto em cinza de contexto
        dominio = sorted(df[serie].dropna().unique().tolist())
        cores = [DESTAQUE if v == destaque else CINZA for v in dominio]
        enc["color"] = alt.Color(f"{serie}:N", title=None, scale=alt.Scale(domain=dominio, range=cores),
                                 legend=alt.Legend(orient="top"))
        enc["tooltip"] = enc["tooltip"] + [alt.Tooltip(f"{serie}:N", title="Série")]
    linha = alt.Chart(df).mark_line(point=alt.OverlayMarkDef(size=18), color=cor or DESTAQUE, strokeWidth=2).encode(**enc)
    camadas = camada_eventos(eventos, ini, fim) + [linha]
    if piso is not None:
        camadas.append(alt.Chart(pd.DataFrame({"y": [piso]})).mark_rule(color=ALERTA, strokeDash=[2, 2]).encode(y="y:Q"))
    return alt.layer(*camadas).properties(height=altura)


def mostrar(chart) -> None:
    st.altair_chart(chart.configure(locale=LOCALE_PTBR).configure_view(strokeWidth=0), width="stretch")


def grafico_cascata(casc: pd.DataFrame) -> alt.LayerChart:
    c = casc.sort_values("ordem").reset_index(drop=True)
    c["anterior"] = c["vendas_meta_web"].shift(1)
    c["delta"] = c["vendas_meta_web"] - c["anterior"]
    extremos = c.index.isin([0, len(c) - 1])
    c["y0"] = c["anterior"].where(~extremos, 0)
    c["y1"] = c["vendas_meta_web"]
    c["tipo"] = ["Total"] * 1 + ["Efeito real" if "real" in d.lower() else "Medição" for d in c["degrau"][1:-1]] + ["Total"]
    c["rotulo"] = [fmt_int(v) if e else fmt_int(d) for v, d, e in zip(c["vendas_meta_web"], c["delta"], extremos)]
    # Rótulos curtos para caber no eixo; o nome completo fica no tooltip
    curtos = {0: "Mês anterior", 1: "Volume real", 2: "P3 · app", 3: "P1 · ingestão", 4: "Ruído", 5: "P2 · UTM (último mês)"}
    c["degrau_curto"] = [curtos.get(o, d) if len(c) == 6 else d for o, d in zip(c["ordem"], c["degrau"])]
    c["topo"] = c[["y0", "y1"]].max(axis=1)
    ordem = c["degrau_curto"].tolist()
    cores = alt.Scale(domain=["Total", "Efeito real", "Medição"], range=[CINZA_ESCURO, CINZA, DESTAQUE])
    base = alt.Chart(c).encode(x=alt.X("degrau_curto:N", sort=ordem, title=None, axis=alt.Axis(labelAngle=0, labelLimit=120, labelOverlap=False, labelFontSize=10)))
    barras = base.mark_bar(size=46).encode(
        y=alt.Y("y0:Q", title="Vendas web do Meta"), y2="y1:Q",
        color=alt.Color("tipo:N", scale=cores, title=None, legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip("degrau:N", title="Degrau"), alt.Tooltip("rotulo:N", title="Valor / Δ"),
                 alt.Tooltip("descricao:N", title="Leitura")])
    texto = base.mark_text(dy=-8, fontSize=12, color="#1E2330").encode(y="topo:Q", text="rotulo:N")
    return alt.layer(barras, texto).properties(height=320)


# ── Página ───────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Saúde da medição · Trama Moda", page_icon=":material/monitoring:", layout="wide")

if not PROJETO:
    st.error("Defina GCP_PROJECT (rode `source preparacao/setup/config.env` antes do `streamlit run`).")
    st.stop()

try:
    INICIO_JANELA, FIM_JANELA = carregar_calendario()
except SemDado as e:
    st.error(f"Não consegui ler o log de ingestão ({e}). Sem ele a dash não sabe até que dia o dado está fechado.")
    st.stop()

P = (("inicio", "DATE", INICIO_JANELA), ("fim", "DATE", FIM_JANELA))
COLS = colunas_gold()
cob, erro_cob = tentar(carregar_cobertura, COLS, P)
midia, erro_midia = tentar(carregar_midia, COLS, P)
log, erro_log = tentar(carregar_log, P)
utm, erro_utm = tentar(carregar_utm, P)
legado, erro_legado = tentar(carregar_legado)
cascata, erro_cascata = tentar(carregar_cascata)

# Eventos do caso, derivados do próprio dado (nada digitado à mão)
dias_sem = set()
if cob is not None:
    w = serie_cobertura(cob, ["web"])
    dias_sem |= set(pd.to_datetime(w.loc[w["cobertura"] < LIM["p1_falha_dia"], "date"]))
if log is not None:
    lw = log[(log["job_name"] == "ga4_web_export") & (log["rows_written"] == 0)]
    dias_sem |= set(pd.to_datetime(lw["date"]))
dias_sem = sorted(dias_sem)
INICIO_B = pd.Timestamp(FIM_JANELA) - timedelta(days=29)   # "último mês" da dash legada
INICIO_A = INICIO_B - timedelta(days=30)                   # "mês anterior"
marcos: dict = {}
if utm is not None:
    fora = utm[utm["e_meta"] & ~utm["template_padrao"]]
    if not fora.empty:
        marcos.setdefault(pd.Timestamp(fora["date"].min()), []).append("template novo de UTM")
marcos.setdefault(INICIO_B, []).append("banner do app + agência nova")
EVENTOS = {"dias_sem_ingestao": dias_sem, "marcos": [(d, " · ".join(r)) for d, r in sorted(marcos.items())]}

# ── Sidebar: filtros globais ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")
    periodo = st.date_input(
        "Período", value=(pd.Timestamp(FIM_JANELA) - timedelta(days=29), FIM_JANELA),
        min_value=INICIO_JANELA, max_value=FIM_JANELA, format="DD/MM/YYYY",
        help="Padrão: os últimos 30 dias fechados (o 'último mês' da dash legada). Os deltas comparam com o "
             "período imediatamente anterior, de mesmo tamanho.")
    canais = st.multiselect("Canal", CANAIS_PAGOS, default=CANAIS_PAGOS, format_func=NOME_CANAL.get,
                            help="Vale para o CPA e para as abas P3 e P4. Os KPIs do topo são fixos no canal "
                                 "de cada problema (Meta em P2/P3, TikTok em P4).")
    plataforma = st.selectbox("Plataforma", ["Ambas", "web", "app"],
                              help="Vale para a cobertura ERP × tracking (P1).")
    st.caption(f"Gold lida de `{GOLD}` · projeto `{PROJETO}`")

if isinstance(periodo, (tuple, list)) and len(periodo) == 2:
    INI, FIM = pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1])
else:  # o usuário ainda está escolhendo a data final
    INI = FIM = pd.Timestamp(periodo[0] if isinstance(periodo, (tuple, list)) else periodo)
N_DIAS = (FIM - INI).days + 1
INI_ANT, FIM_ANT = INI - timedelta(days=N_DIAS), INI - timedelta(days=1)
canais = canais or CANAIS_PAGOS
plats = ["web", "app"] if plataforma == "Ambas" else [plataforma]
DESC_DELTA = f"vs. {N_DIAS}d antes"

# ── Cabeçalho ───────────────────────────────────────────────────────────────────────────
st.title("Saúde da medição · Trama Moda")
st.caption(
    f"Acompanhamento dos 4 problemas do DS-101 · período {fmt_data(INI)} a {fmt_data(FIM)} ({N_DIAS} dias) · "
    f"**dados atualizados até {fmt_data(FIM_JANELA)}** (último dia processado pela ingestão) · "
    f"consultado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
if GOLD != GABARITO:
    st.info(f"Lendo a gold do time (`{GOLD}`). Blocos cuja view ainda não existe mostram um aviso no lugar do gráfico.",
            icon=":material/info:")

# ── KPIs (um por problema) ──────────────────────────────────────────────────────────────

def kpi(coluna, rotulo: str, valor, anterior, spark: list, ajuda: str, st_tuple, delta_color: str,
        erro: str | None = None, nota: str = "") -> None:
    with coluna:
        if valor is None or pd.isna(valor):
            st.metric(rotulo, "—", help=ajuda, border=True)
            st.caption(f":gray-badge[:material/help: Sem dado] {erro or ''}")
            return
        delta = fmt_pp(valor - anterior) if anterior is not None and not pd.isna(anterior) else None
        st.metric(rotulo, fmt_pct(valor), delta=delta, delta_color=delta_color, help=ajuda, border=True,
                  chart_data=[round(v, 4) for v in spark if not pd.isna(v)][-14:], chart_type="line",
                  delta_description=DESC_DELTA if delta else None)
        cor, icone, texto = st_tuple
        st.markdown(f":{cor}-badge[{icone} {texto}] {nota}")


def ratio_periodo(s: pd.DataFrame, num: str, den: str, ini, fim):
    p = entre(s, ini, fim)
    return razao(p[num].sum(), p[den].sum())


c1, c2, c3, c4 = st.columns(4)

# P1
if cob is not None:
    s1 = serie_cobertura(cob, plats)
    v1, a1 = ratio_periodo(s1, "pedidos_rastreados", "pedidos_erp", INI, FIM), ratio_periodo(s1, "pedidos_rastreados", "pedidos_erp", INI_ANT, FIM_ANT)
    dias_ruins = int((entre(serie_cobertura(cob, ["web"]) if "web" in plats else s1, INI, FIM)["cobertura"] < LIM["p1_falha_dia"]).sum())
    st1 = ("red", ":material/error:", "Falha") if dias_ruins else status(v1, LIM["p1_atencao"], 0, True)
    kpi(c1, f"P1 · Cobertura ({plataforma.lower()})", v1, a1, entre(s1, INI, FIM)["cobertura"].tolist(),
        f"Pedidos rastreados ÷ pedidos do ERP no período (razão de somas). Alerta de VOLUME, independente do status "
        f"do job. Falha: algum dia web abaixo de {fmt_pct(LIM['p1_falha_dia'], 0)}. Atenção: período abaixo de "
        f"{fmt_pct(LIM['p1_atencao'], 0)} (normal: web ~88%, app ~92%).", st1, "normal",
        nota=f"{dias_ruins} dia(s) sem ingestão web" if dias_ruins else "nenhum dia sem ingestão")
else:
    kpi(c1, "P1 · Cobertura", None, None, [], "Pedidos rastreados ÷ pedidos do ERP.", None, "normal", erro_cob)

# P2
if utm is not None:
    s2 = serie_p2(utm)
    v2, a2 = ratio_periodo(s2, "fora", "compras", INI, FIM), ratio_periodo(s2, "fora", "compras", INI_ANT, FIM_ANT)
    kpi(c2, "P2 · UTM Meta fora do padrão", v2, a2, rolante(entre(s2, INI, FIM), "fora", "compras").tolist(),
        f"Compras web do Meta (dicionário do gabarito: facebook/fb/ig/instagram/meta) que NÃO vêm como "
        f"facebook / cpc, o único template que a dash legada reconhece. Teto: {fmt_pct(LIM['p2_atencao'], 0)} "
        f"atenção, {fmt_pct(LIM['p2_falha'], 0)} falha. Sparkline: média móvel de 7 dias.",
        status(v2, LIM["p2_atencao"], LIM["p2_falha"], False), "inverse")
else:
    kpi(c2, "P2 · UTM Meta fora do padrão", None, None, [], "", None, "inverse", erro_utm)

# P3
if midia is not None and midia.attrs["tem_plataforma"] and midia["objetivo"].notna().any():
    s3 = serie_p3(midia)
    v3, a3 = ratio_periodo(s3, "conv_app", "conv_total", INI, FIM), ratio_periodo(s3, "conv_app", "conv_total", INI_ANT, FIM_ANT)
    kpi(c3, "P3 · Meta web no app", v3, a3, rolante(entre(s3, INI, FIM), "conv_app", "conv_total").tolist(),
        f"Das conversões das campanhas do Meta com objetivo web, quanto acontece no app (que a dash legada não vê). "
        f"Base histórica ~15%. Atenção acima de {fmt_pct(LIM['p3_atencao'], 0)}, falha acima de "
        f"{fmt_pct(LIM['p3_falha'], 0)}. Sparkline: média móvel de 7 dias.",
        status(v3, LIM["p3_atencao"], LIM["p3_falha"], False), "inverse")
else:
    erro_p3 = erro_midia or "a gold de mídia não tem conv_web/conv_app ou campaign_name."
    kpi(c3, "P3 · Meta web no app", None, None, [], "", None, "inverse", erro_p3)

# P4
if midia is not None:
    s4 = serie_p4(midia)
    v4, a4 = ratio_periodo(s4, "casou", "spend", INI, FIM), ratio_periodo(s4, "casou", "spend", INI_ANT, FIM_ANT)
    kpi(c4, "P4 · Join TikTok (verba)", v4, a4, entre(s4, INI, FIM)["cobertura"].tolist(),
        f"Σ spend do TikTok com match_status = matched ÷ Σ spend do TikTok (por VERBA, não por número de campanhas). "
        f"Piso: {fmt_pct(LIM['p4_atencao'], 0)} (abaixo = atenção), {fmt_pct(LIM['p4_falha'], 0)} (abaixo = falha).",
        status(v4, LIM["p4_atencao"], LIM["p4_falha"], True), "normal")
else:
    kpi(c4, "P4 · Join TikTok (verba)", None, None, [], "", None, "normal", erro_midia)


def aviso(erro: str | None) -> None:
    st.warning(f"Bloco indisponível: {erro}", icon=":material/database_off:")


# ── Abas ────────────────────────────────────────────────────────────────────────────────
aba_geral, aba1, aba2, aba3, aba4, aba_sobre = st.tabs(
    ["Visão geral", "P1 · Ingestão web", "P2 · UTMs do Meta", "P3 · Web → app", "P4 · Join TikTok", "Sobre os dados"])

# Visão geral: CPA nas duas réguas + cascata
with aba_geral:
    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.subheader("Na régua unificada, o CPA do Meta ficou estável e o TikTok é o mais caro")
        st.caption(f"CPA por canal, último mês ({fmt_data(INICIO_B)} a {fmt_data(FIM_JANELA)}) × mês anterior · "
                   "legado = spend ÷ vendas web com UTM exata; unificada = Σ spend ÷ Σ conversões web + app, "
                   "por campanha, sem os dias sem ingestão")
        if midia is None or legado is None:
            aviso(erro_midia or erro_legado)
        else:
            excl = set(dias_sem)
            ua = cpa_por_canal(midia, INICIO_A, INICIO_B - timedelta(days=1), excl).set_index("channel")["cpa"]
            ub = cpa_por_canal(midia, INICIO_B, FIM_JANELA, excl).set_index("channel")["cpa"]
            lg = legado.assign(channel=legado["canal"].str.lower()).set_index("channel")
            linhas = []
            for ch in [c for c in CANAIS_PAGOS if c in canais]:
                linhas.append({"Canal": NOME_CANAL[ch], "Régua": "Dash legada", "cpa_a": lg["cpa_mes_anterior"].get(ch), "cpa_b": lg["cpa_ultimo_mes"].get(ch)})
                linhas.append({"Canal": NOME_CANAL[ch], "Régua": "Unificada", "cpa_a": ua.get(ch), "cpa_b": ub.get(ch)})
            cpa = pd.DataFrame(linhas)
            cpa["var"] = cpa["cpa_b"] / cpa["cpa_a"] - 1
            cpa["rotulo"] = cpa["cpa_b"].map(lambda v: fmt_brl(v, 0))
            barras = alt.Chart(cpa).mark_bar(height=16).encode(
                y=alt.Y("Régua:N", title=None, axis=None), x=alt.X("cpa_b:Q", title="CPA último mês (R$)", axis=alt.Axis(format=",.0f")),
                color=alt.Color("Régua:N", scale=alt.Scale(domain=["Dash legada", "Unificada"], range=[CINZA, DESTAQUE]),
                                legend=alt.Legend(orient="top", title=None)),
                tooltip=["Canal", "Régua", alt.Tooltip("rotulo:N", title="CPA último mês")])
            texto = barras.mark_text(align="left", dx=4, color="#1E2330").encode(text="rotulo:N", color=alt.value("#1E2330"))
            mostrar(alt.layer(barras, texto).facet(row=alt.Row("Canal:N", title=None, header=alt.Header(labelAngle=0, labelAlign="left")))
                    .properties(bounds="flush"))
            # Insight gerado do mesmo DataFrame
            uni = cpa[cpa["Régua"] == "Unificada"].dropna(subset=["cpa_b"])
            frases = []
            if not uni.empty:
                caro = uni.loc[uni["cpa_b"].idxmax()]
                frases.append(f"Na régua unificada, o canal mais caro no último mês é o **{caro['Canal']}** ({fmt_brl(caro['cpa_b'])}).")
            meta = cpa[cpa["Canal"] == "Meta"].set_index("Régua")
            if {"Dash legada", "Unificada"} <= set(meta.index):
                l, u = meta.loc["Dash legada"], meta.loc["Unificada"]
                vezes = _milhar(f"{l['cpa_b'] / l['cpa_a']:.2f}")
                sinal = "+" if u["var"] >= 0 else ""
                frases.append(f"O CPA do Meta na dash legada foi de {fmt_brl(l['cpa_a'])} para {fmt_brl(l['cpa_b'])} "
                              f"({vezes}×); na régua unificada, de {fmt_brl(u['cpa_a'])} para {fmt_brl(u['cpa_b'])} "
                              f"({sinal}{fmt_pct(u['var'])}).")
            st.markdown(sem_latex(" ".join(frases)))
            with st.expander("Tabela do CPA (mês anterior → último mês)"):
                st.dataframe(cpa.assign(**{"CPA mês anterior": cpa["cpa_a"].map(fmt_brl), "CPA último mês": cpa["cpa_b"].map(fmt_brl),
                                           "Variação": cpa["var"].map(fmt_pct)})[["Canal", "Régua", "CPA mês anterior", "CPA último mês", "Variação"]],
                             hide_index=True, width="stretch")
    with col_b:
        st.subheader("Só uma parte pequena da queda das vendas web do Meta é real")
        st.caption("Vendas web do Meta na dash legada, do mês anterior ao último mês, decompostas por causa · "
                   f"fonte: `{GABARITO}.veredito_cascata_meta` (usa a verdade oculta do setup)")
        if cascata is None:
            aviso(erro_cascata)
        else:
            mostrar(grafico_cascata(cascata))
            c = cascata.sort_values("ordem")["vendas_meta_web"].tolist()
            total = c[-1] - c[0]
            real = c[1] - c[0]
            st.markdown(f"Das {fmt_int(abs(total))} vendas web do Meta que 'sumiram' na dash legada "
                        f"({fmt_int(c[0])} → {fmt_int(c[-1])}), só {fmt_int(abs(real))} ({fmt_pct(real / total, 0)}) "
                        f"são efeito real de volume; o resto é medição: app, dias sem ingestão e UTM fora do padrão.")

# P1 · Ingestão web
with aba1:
    if cob is None:
        aviso(erro_cob)
    else:
        por_plat = pd.concat([serie_cobertura(cob, [p]).assign(plataforma=p) for p in plats])
        per = entre(por_plat, INI, FIM)
        web = entre(serie_cobertura(cob, ["web"]), INI, FIM)
        ruins = web[web["cobertura"] < LIM["p1_falha_dia"]]
        st.subheader(f"{len(ruins)} dia(s) do período sem pedido web rastreado, com o job verde"
                     if len(ruins) else "Todos os dias do período têm pedido web rastreado")
        st.caption(f"Pedidos rastreados ÷ pedidos do ERP, por dia e plataforma · {fmt_data(INI)} a {fmt_data(FIM)} · "
                   f"linha vermelha: piso de falha diária ({fmt_pct(LIM['p1_falha_dia'], 0)})")
        mostrar(grafico_linha(per, "cobertura", "Cobertura", EVENTOS, INI, FIM, serie="plataforma", destaque="web",
                              piso=LIM["p1_falha_dia"],
                              tooltip_extra=[alt.Tooltip("pedidos_erp:Q", title="Pedidos ERP"),
                                             alt.Tooltip("pedidos_rastreados:Q", title="Rastreados")]))
        if len(ruins):
            dias_txt = ", ".join(fmt_dia(d) for d in ruins["date"])
            st.markdown(f"Nos dias {dias_txt}, o ERP registrou {fmt_int(ruins['pedidos_erp'].sum())} pedidos no site e o "
                        f"tracking registrou {fmt_int(ruins['pedidos_rastreados'].sum())}. Fora desses dias, a cobertura web "
                        f"do período foi de {fmt_pct(razao(web['pedidos_rastreados'].sum() - ruins['pedidos_rastreados'].sum(), web['pedidos_erp'].sum() - ruins['pedidos_erp'].sum()))}.")
        ultimo = {p: s.loc[s["pedidos_rastreados"] > 0, "date"].max() for p, s in por_plat.groupby("plataforma")}
        cols = st.columns(len(ultimo) + 1)
        for col, (p, d) in zip(cols, ultimo.items()):
            atraso = (pd.Timestamp(FIM_JANELA) - pd.Timestamp(d)).days if pd.notna(d) else None
            col.metric(f"Último pedido {p} rastreado", fmt_data(d) if pd.notna(d) else "—",
                       delta=f"{atraso} dia(s) de atraso" if atraso else "em dia", delta_color="off", delta_arrow="off", border=True,
                       help="Atualização (freshness): último dia com pedido rastreado vs. último dia fechado da ingestão.")

        st.subheader("O status do job não avisa: nos dias sem dado ele ficou SUCCESS com 0 linhas")
        if log is None:
            aviso(erro_log)
        else:
            lw = entre(log[log["job_name"] == "ga4_web_export"], INI, FIM).copy()
            lw["situação"] = lw["rows_written"].map(lambda r: "0 linhas" if r == 0 else "normal")
            st.caption("Linhas gravadas por dia pelo job ga4_web_export (raw_ingestion_log) · vermelho = 0 linhas")
            barras = alt.Chart(lw).mark_bar().encode(
                x=alt.X("date:T", title=None, axis=alt.Axis(format="%d/%m", labelAngle=0)),
                y=alt.Y("rows_written:Q", title="Linhas gravadas", axis=alt.Axis(format=",.0f")),
                color=alt.Color("situação:N", scale=alt.Scale(domain=["normal", "0 linhas"], range=[CINZA, ALERTA]),
                                legend=alt.Legend(orient="top", title=None)),
                tooltip=[alt.Tooltip("date:T", title="Dia", format="%d/%m/%Y"), "status", alt.Tooltip("duration_s:Q", title="Duração (s)"),
                         alt.Tooltip("rows_written:Q", title="Linhas", format=",.0f")])
            mostrar(alt.layer(*camada_eventos(EVENTOS, INI, FIM), barras).properties(height=220))
            zeros = lw[lw["rows_written"] == 0]
            if len(zeros):
                st.markdown(f"{len(zeros)} execução(ões) com status **{', '.join(sorted(zeros['status'].unique()))}** e 0 linhas, "
                            f"com duração média de {fmt_int(zeros['duration_s'].mean())} s (normal: {fmt_int(lw.loc[lw['rows_written'] > 0, 'duration_s'].mean())} s).")
        with st.expander("Detalhe diário (com mediana de 4 semanas do mesmo dia da semana)"):
            tab_dia = serie_cobertura(cob, ["web"]).sort_values("date")
            tab_dia["dow"] = pd.to_datetime(tab_dia["date"]).dt.dayofweek
            tab_dia["mediana_4sem"] = tab_dia.groupby("dow")["cobertura"].transform(lambda s: s.shift(1).rolling(4, min_periods=2).median())
            tab_dia = entre(tab_dia, INI, FIM)
            if log is not None:
                tab_dia = tab_dia.merge(log[log["job_name"] == "ga4_web_export"][["date", "status", "rows_written"]], on="date", how="left")
            tab_dia["alerta"] = tab_dia["cobertura"].map(lambda v: "Falha" if v < LIM["p1_falha_dia"] else ("Atenção" if v < LIM["p1_atencao"] else "OK"))
            st.dataframe(tab_dia.assign(dia=tab_dia["date"].map(fmt_data), cobertura_web=tab_dia["cobertura"].map(fmt_pct),
                                        mediana=tab_dia["mediana_4sem"].map(fmt_pct))
                         [["dia", "pedidos_erp", "pedidos_rastreados", "cobertura_web", "mediana"] + (["status", "rows_written"] if log is not None else []) + ["alerta"]],
                         hide_index=True, width="stretch")

# P2 · UTMs do Meta
with aba2:
    if utm is None:
        aviso(erro_utm)
    else:
        s2p = entre(serie_p2(utm), INI_ANT, FIM).copy()
        s2p["media_7d"] = rolante(s2p, "fora", "compras")
        s2p = entre(s2p, INI, FIM)
        v2 = razao(s2p["fora"].sum(), s2p["compras"].sum())
        st.subheader(f"{fmt_pct(v2)} das compras web do Meta chegam num template de UTM que a dash legada não reconhece")
        st.caption(f"% das compras web do Meta fora de facebook / cpc, por dia (pontos) e média móvel de 7 dias (linha) · "
                   f"{fmt_data(INI)} a {fmt_data(FIM)} · linha vermelha: teto de falha ({fmt_pct(LIM['p2_falha'], 0)})")
        pontos = alt.Chart(s2p).mark_circle(color=CINZA, size=24).encode(
            x=alt.X("date:T", title=None, axis=alt.Axis(format="%d/%m", labelAngle=0)), y=alt.Y("pct_fora:Q", title="% fora do padrão", axis=alt.Axis(format=".0%")),
            tooltip=[alt.Tooltip("date:T", title="Dia", format="%d/%m/%Y"), alt.Tooltip("pct_fora:Q", title="% no dia", format=".1%"),
                     alt.Tooltip("fora:Q", title="Compras fora"), alt.Tooltip("compras:Q", title="Compras Meta")])
        linha = grafico_linha(s2p, "media_7d", "% fora do padrão", EVENTOS, INI, FIM, piso=LIM["p2_falha"])
        mostrar(alt.layer(linha, pontos))
        tpl = utm[utm["e_meta"]]
        tpl_p = entre(tpl, INI, FIM).groupby("template", as_index=False)["compras"].sum()
        tpl_a = entre(tpl, INI_ANT, FIM_ANT).groupby("template", as_index=False)["compras"].sum()
        tt = tpl_p.merge(tpl_a, on="template", how="outer", suffixes=("", "_ant")).fillna(0).sort_values("compras", ascending=False)
        tt["reconhecido"] = tt["template"].eq("facebook / cpc").map({True: "sim (dash legada)", False: "não"})
        novos = tt[(tt["compras_ant"] == 0) & (tt["compras"] > 0)]["template"].tolist()
        col_t, col_u = st.columns([3, 2])
        with col_t:
            st.subheader("Templates de UTM do Meta no período")
            st.caption("Bloco 0: todos os pares utm_source / utm_medium que o dicionário do gabarito mapeia para Meta")
            st.dataframe(tt.rename(columns={"compras": "compras no período", "compras_ant": "período anterior"})
                         [["template", "compras no período", "período anterior", "reconhecido"]], hide_index=True, width="stretch")
            if novos:
                st.markdown(f"Templates que não existiam no período anterior: {', '.join(f'`{n}`' for n in novos)}.")
        with col_u:
            st.subheader("Unassigned")
            todos = entre(utm, INI, FIM)
            desconhecidos = todos[~todos["e_meta"] & ~todos["utm_source"].str.lower().isin(["google", "tiktok", "crm", "(direct)"])]
            pct_un = razao(desconhecidos["compras"].sum(), todos["compras"].sum())
            st.metric("Compras web em unassigned", fmt_pct(pct_un), border=True,
                      help="Compras cujo utm_source não está no dicionário canônico (caem no else = unassigned).")
            if midia is not None:
                gasto_meta = entre(midia[midia["channel"] == "meta"], INI, FIM)["spend"].sum()
                st.markdown(sem_latex(f"Proporcionalmente, cerca de **{fmt_brl((v2 or 0) * gasto_meta, 0)}** da verba do Meta no período "
                            f"({fmt_brl(gasto_meta, 0)}) fica sem conversão atribuída na dash legada por causa da UTM."))

# P3 · Web → app
with aba3:
    if midia is None or not midia.attrs["tem_plataforma"] or midia["objetivo"].isna().all():
        aviso(erro_midia or "a gold de mídia não expõe conv_web/conv_app ou o objetivo da campanha.")
    else:
        series = []
        for ch in [c for c in CANAIS_PAGOS if c in canais]:
            s = entre(serie_p3(midia, ch), INI_ANT, FIM).copy()
            s["pct_app_7d"] = rolante(s, "conv_app", "conv_total")
            series.append(entre(s, INI, FIM).assign(canal=NOME_CANAL[ch]))
        s3p = pd.concat(series) if series else pd.DataFrame()
        meta3 = s3p[s3p["canal"] == "Meta"] if not s3p.empty else s3p
        v3 = razao(meta3["conv_app"].sum(), meta3["conv_total"].sum()) if not meta3.empty else None
        st.subheader(f"{fmt_pct(v3)} das conversões das campanhas web do Meta acontecem no app" if v3 is not None
                     else "Conversões das campanhas web no app")
        st.caption("Share do app nas conversões das campanhas de objetivo web, média móvel de 7 dias (razão de somas) · "
                   "Meta em destaque, demais canais em cinza")
        if not s3p.empty:
            mostrar(grafico_linha(s3p.dropna(subset=["pct_app_7d"]), "pct_app_7d", "% no app (7 dias)", EVENTOS, INI, FIM,
                                  serie="canal", destaque="Meta", piso=LIM["p3_falha"]))
        # A × B fixos (mês anterior × último mês), sem os dias sem ingestão: mesma régua nos dois lados
        m = midia[midia["channel"].isin(canais) & (midia["objetivo"] == "web") & ~pd.to_datetime(midia["date"]).isin(dias_sem)].copy()
        d = pd.to_datetime(m["date"])
        m["periodo"] = pd.NA
        m.loc[(d >= INICIO_A) & (d < INICIO_B), "periodo"] = "Mês anterior"
        m.loc[d >= INICIO_B, "periodo"] = "Último mês"
        ab = m.dropna(subset=["periodo"]).groupby(["channel", "periodo"], as_index=False)[["conv_web", "conv_app"]].sum()
        ab["pct_app"] = ab["conv_app"] / (ab["conv_web"] + ab["conv_app"])
        ab["Canal"] = ab["channel"].map(NOME_CANAL)
        st.subheader("Mês anterior × último mês")
        st.caption("% das conversões das campanhas web que acontecem no app, sem os dias sem ingestão")
        barras = alt.Chart(ab).mark_bar(height=14).encode(
            y=alt.Y("periodo:N", title=None, axis=None), x=alt.X("pct_app:Q", title="% no app", axis=alt.Axis(format=".0%")),
            color=alt.Color("periodo:N", scale=alt.Scale(domain=["Mês anterior", "Último mês"], range=[CINZA, DESTAQUE]),
                            legend=alt.Legend(orient="top", title=None)),
            tooltip=["Canal", "periodo", alt.Tooltip("pct_app:Q", format=".1%", title="% no app"),
                     alt.Tooltip("conv_app:Q", title="Conv. app"), alt.Tooltip("conv_web:Q", title="Conv. web")])
        mostrar(barras.facet(row=alt.Row("Canal:N", title=None, header=alt.Header(labelAngle=0, labelAlign="left"))))
        frases = []
        for ch, g in ab.groupby("Canal"):
            g = g.set_index("periodo")["pct_app"]
            if {"Mês anterior", "Último mês"} <= set(g.index):
                frases.append(f"{ch}: {fmt_pct(g['Mês anterior'])} → {fmt_pct(g['Último mês'])}")
        if frases:
            st.markdown("Share do app nas campanhas web · " + " · ".join(frases) + ". A dash legada só enxerga a parte web.")

# P4 · Join TikTok
with aba4:
    if midia is None:
        aviso(erro_midia)
    else:
        mp = entre(midia[midia["channel"].isin(canais)], INI_ANT, FIM)
        series = []
        for ch in [c for c in CANAIS_PAGOS if c in canais]:
            s = serie_p4(mp, ch).assign(canal=NOME_CANAL[ch])
            series.append(entre(s, INI, FIM))
        s4p = pd.concat(series) if series else pd.DataFrame()
        tk = s4p[s4p["canal"] == "TikTok"] if not s4p.empty else s4p
        v4 = razao(tk["casou"].sum(), tk["spend"].sum()) if not tk.empty else None
        st.subheader(f"Só {fmt_pct(v4)} da verba do TikTok casa com conversão" if v4 is not None else "Cobertura do join por verba")
        st.caption(f"Σ spend matched ÷ Σ spend, por dia e canal · {fmt_data(INI)} a {fmt_data(FIM)} · "
                   f"linha vermelha: piso de falha ({fmt_pct(LIM['p4_falha'], 0)})")
        if not s4p.empty:
            mostrar(grafico_linha(s4p, "cobertura", "Cobertura por verba", EVENTOS, INI, FIM, serie="canal", destaque="TikTok",
                                  piso=LIM["p4_falha"], tooltip_extra=[alt.Tooltip("spend:Q", title="Spend (R$)", format=",.2f")]))
        per4 = entre(mp, INI, FIM).copy()
        per4["situação"] = per4["match_status"]
        if midia.attrs["tem_nome"]:
            per4.loc[per4["campaign_name"].isna() & (per4["match_status"] == "spend_only"), "situação"] = "spend_only sem campaign_name"
        comp = per4.groupby(["channel", "situação"], as_index=False)["spend"].sum()
        comp = comp[comp["spend"] > 0]
        comp["Canal"] = comp["channel"].map(NOME_CANAL)
        comp["rotulo"] = comp["spend"].map(lambda v: fmt_brl(v, 0))
        col_g, col_t = st.columns([3, 2])
        with col_g:
            st.subheader("Verba por situação do join")
            st.caption("Spend do período por canal e match_status · só a parte matched entra no CPA com conversão")
            ordem_sit = ["matched", "spend_only", "spend_only sem campaign_name"]
            mostrar(alt.Chart(comp).mark_bar(size=26).encode(
                y=alt.Y("Canal:N", title=None), x=alt.X("spend:Q", stack="normalize", title="% da verba", axis=alt.Axis(format=".0%")),
                color=alt.Color("situação:N", scale=alt.Scale(domain=ordem_sit, range=[CINZA, CINZA_ESCURO, ALERTA]),
                                legend=alt.Legend(orient="top", title=None)),
                order=alt.Order("situação:N"),
                tooltip=["Canal", "situação", alt.Tooltip("rotulo:N", title="Spend")]).properties(height=alt.Step(44)))
        with col_t:
            st.subheader("Gasto sem campaign_name")
            if not midia.attrs["tem_nome"]:
                st.info("A gold de mídia não expõe campaign_name: não dá para separar o gasto sem nome.")
            else:
                sem = per4[per4["campaign_name"].isna() & (per4["spend"] > 0)]
                sem_dia = sem.groupby(["date", "channel"], as_index=False)["spend"].sum().sort_values("date", ascending=False)
                st.caption(sem_latex(f"Total no período: {fmt_brl(sem['spend'].sum())} "
                           f"({fmt_pct(razao(sem['spend'].sum(), per4['spend'].sum()))} da verba dos canais filtrados)"))
                st.dataframe(sem_dia.assign(dia=sem_dia["date"].map(fmt_data), canal=sem_dia["channel"].map(NOME_CANAL),
                                            gasto=sem_dia["spend"].map(fmt_brl))[["dia", "canal", "gasto"]],
                             hide_index=True, width="stretch", height=260)

# Sobre os dados
with aba_sobre:
    st.subheader("Fontes")
    st.markdown(f"""
| Bloco | Fonte | Observação |
|---|---|---|
| P1 cobertura | `{GOLD}.gold_tracking_coverage_by_day` | pedidos rastreados ÷ pedidos do ERP, dia × plataforma |
| P1 log | `trama_raw.raw_ingestion_log` (job `ga4_web_export`) | status e linhas gravadas; também define o último dia fechado |
| P2 UTMs | `trama_raw.raw_web_events` (compras, agregado por dia × source × medium) | mesmo dicionário da `silver_web_purchases` do gabarito |
| P3 app, P4 join, CPA unificado | `{GOLD}.gold_media_performance_by_day` + `trama_raw.raw_campaigns` (objetivo) | FULL OUTER por data + campanha, com `match_status` |
| CPA legado | `trama_legacy.vw_dash_growth_resumo` | o que a Growth vê hoje |
| Cascata | `{GABARITO}.veredito_cascata_meta` | usa a verdade oculta do setup: só o gabarito tem |
""")
    st.subheader("Definições e limiares")
    st.markdown(f"""
- **Todas as razões são razão de somas** (Σ numerador ÷ Σ denominador no período), nunca média de razões diárias.
- **P1**: falha se algum dia tiver cobertura web abaixo de {fmt_pct(LIM['p1_falha_dia'], 0)}; atenção se a cobertura do período
  ficar abaixo de {fmt_pct(LIM['p1_atencao'], 0)}. A tabela de detalhe compara cada dia com a mediana das 4 semanas anteriores no mesmo dia da semana.
- **P2**: compras web do Meta fora de `facebook / cpc`. Atenção acima de {fmt_pct(LIM['p2_atencao'], 0)}, falha acima de {fmt_pct(LIM['p2_falha'], 0)}.
- **P3**: conv_app ÷ conv_total das campanhas do Meta com objetivo web. Atenção acima de {fmt_pct(LIM['p3_atencao'], 0)}, falha acima de {fmt_pct(LIM['p3_falha'], 0)}.
- **P4**: Σ spend matched ÷ Σ spend do TikTok. Atenção abaixo de {fmt_pct(LIM['p4_atencao'], 0)}, falha abaixo de {fmt_pct(LIM['p4_falha'], 0)}.
- **CPA unificado**: Σ spend ÷ Σ (conversões web + app), por campanha, excluindo os dias sem ingestão web dos dois períodos.
- **Eventos anotados** (derivados do dado): dias sem ingestão = cobertura web < {fmt_pct(LIM['p1_falha_dia'], 0)} ou job com 0 linhas;
  template novo = primeiro dia com compra Meta fora do padrão; banner do app + agência nova = início do "último mês" da dash legada.
- Limiares são pontos de partida calibrados com o dado do caso (cobertura normal web ~88%, app ~92%), não vêm das fontes.
""")
    st.markdown("**Eventos detectados:** " + (", ".join(fmt_data(d) for d in EVENTOS["dias_sem_ingestao"]) or "nenhum dia sem ingestão")
                + " · " + " · ".join(f"{fmt_data(d)}: {r}" for d, r in EVENTOS["marcos"]))
    st.subheader("Consultas desta execução")
    st.caption(f"Dry run antes de cada consulta, teto de {fmt_int(LIMITE_BYTES / 1e6)} MB faturados, cache de 1 hora")
    reg = pd.DataFrame(REGISTRO).drop_duplicates("consulta")
    if not reg.empty:
        reg["MB estimados"] = reg["bytes"].map(lambda b: "—" if b is None or pd.isna(b) else _milhar(f"{b / 1e6:,.2f}"))
        st.dataframe(reg[["consulta", "MB estimados", "situação"]], hide_index=True, width="stretch")
    if GOLD == GABARITO:
        vc, erro_vc = tentar(carregar_veredito_cpa)
        if vc is not None:
            with st.expander("Conferência: CPA da tabela veredito_cpa do gabarito"):
                st.dataframe(vc.assign(cpa_a=vc["cpa_a"].map(fmt_brl), cpa_b=vc["cpa_b"].map(fmt_brl), var_cpa=vc["var_cpa"].map(fmt_pct)),
                             hide_index=True, width="stretch")
