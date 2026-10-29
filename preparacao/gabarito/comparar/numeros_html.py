"""Procura os números do gabarito nos HTML da sessão (texto e dados embutidos no JS).

Uso:  python3 numeros_html.py <pasta_da_sessao>
Lê os CSVs de ../relatorio/results. Não encontrar um número não prova erro: o HTML pode
calcular no JS ou arredondar diferente. Serve para apontar onde olhar.
"""
import csv
import re
import sys
from pathlib import Path

RES = Path(__file__).resolve().parent.parent / "relatorio" / "results"


def ler(nome):
    with open(RES / f"{nome}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def variantes(v):
    x = float(v)
    if x.is_integer() and abs(x) >= 10:
        n = int(x)
        return {str(n), f"{n:,}".replace(",", ".")}
    out = set()
    for casas in (2, 1):
        s = f"{x:.{casas}f}"
        out |= {s, s.replace(".", ",")}
    return out


esperados = []
for r in ler("r07_dash_legada"):
    if r["canal"] == "Meta":
        esperados += [("Dash: vendas web Meta A", r["vendas_web_mes_anterior"]),
                      ("Dash: vendas web Meta B", r["vendas_web_ultimo_mes"]),
                      ("Dash: CPA Meta B", r["cpa_ultimo_mes"])]
    if r["canal"] == "TikTok":
        esperados.append(("Dash: CPA TikTok B", r["cpa_ultimo_mes"]))
for r in ler("r06_veredito_cpa"):
    if r["regua"] == "unificada":
        esperados += [(f"Régua unificada: CPA {r['channel']} A", r["cpa_a"]),
                      (f"Régua unificada: CPA {r['channel']} B", r["cpa_b"])]
for r in ler("r08_cascata_meta"):
    esperados.append((f"Cascata: {r['degrau']}", r["vendas_meta_web"]))

sessao = Path(sys.argv[1])
htmls = [h for h in sessao.rglob("*.html") if not ({"estudos", ".claude", ".venv"} & set(h.parts))]
if not htmls:
    print("✘ nenhum HTML na sessão (fora de estudos/)")
    sys.exit(0)
for h in htmls:
    txt = h.read_text(encoding="utf-8", errors="ignore")
    achados = 0
    linhas = []
    for rotulo, v in esperados:
        ok = any(re.search(rf"(?<![\d.,]){re.escape(s)}(?![\d])", txt) for s in variantes(v))
        achados += ok
        linhas.append(f"  {'✔' if ok else '·'} {rotulo}: {v}")
    print(f"▶ {h.relative_to(sessao)}  ({achados}/{len(esperados)} números do gabarito encontrados)")
    print("\n".join(linhas))
