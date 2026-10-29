"""CSV (results/) → data.json + const D embutido no relatório.

Uso:  python3 gen_data.py
Nenhum número do relatório é digitado à mão: tudo sai daqui. O template tem o marcador
`/*__D__*/null`, que é trocado pelo JSON. No fim, o script valida que o JSON embutido faz parse.
"""
import csv
import json
import re
from pathlib import Path

DIR = Path(__file__).resolve().parent
RES = DIR / "results"
CANAIS = ["meta", "google", "tiktok"]
ROTULO = {"meta": "Meta", "google": "Google", "tiktok": "TikTok"}


def ler(nome: str) -> list[dict]:
    with open(RES / f"{nome}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x: str) -> float:
    return float(x) if x not in ("", None) else 0.0


def div(a: float, b: float) -> float | None:
    return round(a / b, 4) if b else None


def main() -> None:
    ctx = ler("r09_contexto")[0]
    dias_p1 = ctx["dias_sem_ingestao_web"].split(",")

    # ── Dash legada ────────────────────────────────────────────────────────────────
    legada = {r["canal"]: r for r in ler("r07_dash_legada")}
    web_a = sum(num(r["vendas_web_mes_anterior"]) for r in legada.values())
    web_b = sum(num(r["vendas_web_ultimo_mes"]) for r in legada.values())
    legado = {
        "canais": [
            {"canal": c, "rotulo": ROTULO[c],
             "vendas_a": num(legada[ROTULO[c]]["vendas_web_mes_anterior"]),
             "vendas_b": num(legada[ROTULO[c]]["vendas_web_ultimo_mes"]),
             "var_vendas": num(legada[ROTULO[c]]["var_vendas"]),
             "cpa_a": num(legada[ROTULO[c]]["cpa_mes_anterior"]),
             "cpa_b": num(legada[ROTULO[c]]["cpa_ultimo_mes"])}
            for c in CANAIS
        ],
        "web_a": web_a, "web_b": web_b, "var_web": div(web_b - web_a, web_a),
    }

    # ── CPA: legado × unificado ────────────────────────────────────────────────────
    cpa = {}
    for r in ler("r06_veredito_cpa"):
        cpa.setdefault(r["regua"], {})[r["channel"]] = {
            "cpa_a": num(r["cpa_a"]), "cpa_b": num(r["cpa_b"]), "var": num(r["var_cpa"])}
    meta_leg, meta_uni = cpa["legado"]["meta"], cpa["unificada"]["meta"]

    # ── P1 · cobertura diária + log ────────────────────────────────────────────────
    serie = {}
    for r in ler("r01_cobertura_diaria"):
        d = serie.setdefault(r["date"], {"date": r["date"], "p1": r["dia_sem_ingestao"] == "true"})
        d[f'{r["sales_platform"]}_erp'] = num(r["pedidos_erp"])
        d[f'{r["sales_platform"]}_trk'] = num(r["pedidos_rastreados"])
        d[f'{r["sales_platform"]}_cob'] = num(r["cobertura"])
    serie = [serie[k] for k in sorted(serie)]
    normais = [d["web_cob"] for d in serie if not d["p1"]]
    log = [{"data": r["data_date"], "status": r["status"], "duracao_s": num(r["duration_s"]),
            "linhas": num(r["rows_written"])} for r in ler("r02_log_ingestao_web")]
    log_normais = [l["duracao_s"] for l in log if l["linhas"] > 0]
    web_perdido_p1 = sum(d["web_erp"] for d in serie if d["p1"])
    p1 = {
        "dias": dias_p1,
        "cobertura_web_normal_media": round(sum(normais) / len(normais), 4),
        "cobertura_web_normal_min": min(normais),
        "pedidos_web_erp_nos_dias_p1": web_perdido_p1,
        "log_status_nos_dias_p1": sorted({l["status"] for l in log if l["data"] in dias_p1}),
        "log_duracao_p1_s": max(l["duracao_s"] for l in log if l["data"] in dias_p1),
        "log_duracao_normal_min_s": min(log_normais),
        "log_duracao_normal_max_s": max(log_normais),
    }

    # ── P2 · bloco 0 de UTM ────────────────────────────────────────────────────────
    utm = ler("r03_bloco0_utm")
    meta_utm = [r for r in utm if r["e_meta"] == "true"]
    variantes_b = sorted(
        ({"utm": f'{r["utm_source"]} / {r["utm_medium"]}', "compras": num(r["compras"]),
          "reconhecida": r["dash_reconhece_meta"] == "true"}
         for r in meta_utm if r["periodo"] == "B"),
        key=lambda v: -v["compras"])
    meta_b_total = sum(v["compras"] for v in variantes_b)
    meta_b_fora = sum(v["compras"] for v in variantes_b if not v["reconhecida"])
    p2 = {
        "variantes_b": variantes_b,
        "variantes_a": len([r for r in meta_utm if r["periodo"] == "A"]),
        "compras_meta_b": meta_b_total,
        "compras_fora_da_regra_b": meta_b_fora,
        "share_fora_da_regra_b": div(meta_b_fora, meta_b_total),
    }

    # ── P3 · onde convertem as campanhas de objetivo web ──────────────────────────
    plat = {}
    for r in ler("r04_plataforma_por_campanha"):
        plat.setdefault(r["channel"], {}).setdefault(r["periodo"], {})[r["plataforma"]] = num(r["conversoes"])
    p3 = {"canais": [
        {"canal": c, "rotulo": ROTULO[c],
         "app_share_a": div(plat[c]["A"].get("app", 0), sum(plat[c]["A"].values())),
         "app_share_b": div(plat[c]["B"].get("app", 0), sum(plat[c]["B"].values())),
         "web_a": plat[c]["A"].get("web", 0), "web_b": plat[c]["B"].get("web", 0),
         "total_a": sum(plat[c]["A"].values()), "total_b": sum(plat[c]["B"].values())}
        for c in CANAIS]}

    # ── P4 · cobertura do join por verba ───────────────────────────────────────────
    verba = {}
    for r in ler("r05_cobertura_join_verba"):
        v = verba.setdefault(r["channel"], {}).setdefault(r["periodo"], {"matched": 0.0, "sem_nome": 0.0, "outros": 0.0})
        chave = "matched" if r["match_status"] == "matched" else ("sem_nome" if r["sem_campaign_name"] == "true" else "outros")
        v[chave] += num(r["spend"])
    p4 = {"canais": []}
    for c in CANAIS:
        linha = {"canal": c, "rotulo": ROTULO[c]}
        for per in ("A", "B"):
            v = verba[c][per]
            tot = sum(v.values())
            linha[f"spend_{per.lower()}"] = round(tot, 2)
            linha[f"share_matched_{per.lower()}"] = div(v["matched"], tot)
            linha[f"share_sem_nome_{per.lower()}"] = div(v["sem_nome"], tot)
            linha[f"share_outros_{per.lower()}"] = div(v["outros"], tot)
        p4["canais"].append(linha)

    # ── Cascata ────────────────────────────────────────────────────────────────────
    cascata = [{"ordem": int(r["ordem"]), "degrau": r["degrau"], "valor": num(r["vendas_meta_web"]),
                "descricao": r["descricao"]} for r in ler("r08_cascata_meta")]
    for i, d in enumerate(cascata):
        d["delta"] = None if i == 0 else d["valor"] - cascata[i - 1]["valor"]
    queda_total = cascata[-1]["valor"] - cascata[0]["valor"]
    efeito_real = next(d["delta"] for d in cascata if d["ordem"] == 1)

    D = {
        "contexto": {k: ctx[k] for k in ("data_ref", "janela_inicio", "janela_fim", "inicio_a", "inicio_b")},
        "legado": legado,
        "cpa": cpa,
        "tese": {
            "meta_cpa_legado_ratio": div(meta_leg["cpa_b"], meta_leg["cpa_a"]),
            "meta_cpa_unificado_var": meta_uni["var"],
            "tiktok_cpa_legado_b": cpa["legado"]["tiktok"]["cpa_b"],
            "tiktok_cpa_unificado_b": cpa["unificada"]["tiktok"]["cpa_b"],
            "canal_mais_caro_unificado": max(CANAIS, key=lambda c: cpa["unificada"][c]["cpa_b"]),
            "canal_mais_barato_legado": min(CANAIS, key=lambda c: cpa["legado"][c]["cpa_b"]),
            "share_queda_meta_efeito_real": div(efeito_real, queda_total),
        },
        "serie": serie, "log": log, "p1": p1, "p2": p2, "p3": p3, "p4": p4,
        "cascata": cascata,
    }

    js = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
    (DIR / "data.json").write_text(json.dumps(D, ensure_ascii=False, indent=2), encoding="utf-8")

    html = (DIR / "template.html").read_text(encoding="utf-8")
    assert html.count("/*__D__*/null") == 1, "template precisa ter exatamente um marcador /*__D__*/null"
    saida = DIR / "relatorio_DS-101.html"
    saida.write_text(html.replace("/*__D__*/null", js), encoding="utf-8")

    # validação: o JSON embutido faz parse e é idêntico ao gerado
    embutido = re.search(r"const D = (.*?);\n", saida.read_text(encoding="utf-8")).group(1)
    assert json.loads(embutido) == D
    print(f"✔ data.json + {saida.name} ({len(js):,} bytes de dados, parse ok)")


if __name__ == "__main__":
    main()
