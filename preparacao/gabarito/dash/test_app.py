"""Testes da dash com streamlit.testing.v1.AppTest, contra o BigQuery real.

Rodar (com o config.env carregado, dentro de preparacao/gabarito/dash):
    python test_app.py          # ou: pytest test_app.py
"""

import os
from datetime import timedelta

from streamlit.testing.v1 import AppTest

AQUI = os.path.dirname(os.path.abspath(__file__))


def abrir(gold: str | None = None) -> AppTest:
    if gold:
        os.environ["TRAMA_GOLD_DATASET"] = gold
    else:
        os.environ.pop("TRAMA_GOLD_DATASET", None)
    at = AppTest.from_file(os.path.join(AQUI, "app.py"), default_timeout=120)
    return at.run()


def sem_erro(at: AppTest) -> None:
    assert not at.exception, [e.message for e in at.exception]
    assert len(at.metric) >= 4


def test_gabarito_abre_com_4_kpis():
    at = abrir()
    sem_erro(at)
    rotulos = [m.label for m in at.metric[:4]]
    assert all(r.startswith(f"P{i}") for i, r in enumerate(rotulos, start=1)), rotulos
    assert all(m.value != "—" for m in at.metric[:4])
    assert len(at.tabs) == 6
    assert not at.warning, [w.value for w in at.warning]


def test_filtros_rerodam_sem_erro():
    at = abrir()
    ini, fim = at.sidebar.date_input[0].value
    at.sidebar.date_input[0].set_value((fim - timedelta(days=13), fim)).run()
    sem_erro(at)
    at.sidebar.multiselect[0].set_value(["meta", "tiktok"]).run()
    sem_erro(at)
    at.sidebar.selectbox[0].set_value("web").run()
    sem_erro(at)
    assert at.metric[0].label.endswith("(web)")


def test_gold_do_time_degrada_sem_quebrar():
    at = abrir("trama_gold")
    try:
        sem_erro(at)
        assert at.warning, "esperava avisos de bloco indisponível"
    finally:
        os.environ.pop("TRAMA_GOLD_DATASET", None)


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok ·", nome)
