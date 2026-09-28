"""Regresión: calculos.py sobre el periodo limpio de marzo 2024 reproduce los resultados validados del Sprint 1."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
import calculos  # noqa: E402
import etl  # noqa: E402
import limpieza as L  # noqa: E402

PERIODO = "2024-03"
LIMPIO = etl.ruta_limpio_periodo(PERIODO)


@pytest.fixture(scope="module")
def resultados():
    if not LIMPIO.exists():
        pytest.skip(f"Falta {LIMPIO}; corran python pipeline/etl.py --periodo {PERIODO}")
    inicio, fin, _ = etl.rango_periodo(PERIODO)
    limpio, _ = L.control_calidad(L.cargar(LIMPIO), inicio, fin)
    h = calculos.calcular_horario(limpio, PERIODO)
    return h, calculos.calcular_diario(h)


def test_periodo_incluye_calentamiento():
    df = pd.read_csv(LIMPIO) if LIMPIO.exists() else pytest.skip("sin datos")
    assert df["CALENTAMIENTO"].sum() == 24
    assert len(df) == 744 + 24


def test_marzo_dias_por_categoria(resultados):
    _, d = resultados
    assert d["Cat_Global_Diaria"].value_counts().to_dict() == {"Mala": 18, "Aceptable": 10, "Sin datos": 2, "Buena": 1}
    assert d.loc[d["Responsable_Diario"] != "", "Responsable_Diario"].value_counts().to_dict() == {"PM10": 25, "O3": 4}


def test_marzo_horas_por_categoria(resultados):
    h, _ = resultados
    assert len(h) == 744
    assert h["Cat_Global_Horaria"].value_counts().to_dict() == {
        "Buena": 407, "Mala": 158, "Aceptable": 126, "Sin datos": 36, "Muy Mala": 17}


def test_decimales_diarios(resultados):
    _, d = resultados
    pm = d["Indicador_PM10"].dropna()
    assert (pm == pm.round(0)).all()                       # PM: promedio 24 h entero
    o3 = d["Indicador_O3"].dropna()
    assert (o3 == o3.round(3)).all()                       # O3: 3 decimales
    assert d.loc[d["Fecha"] == "2024-03-07", "Cat_Global_Diaria"].item() == "Buena"

