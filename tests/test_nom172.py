"""Pruebas: casos de revisión de NowCast proporcionados por la profesora + reglas de categorías."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
from nom172 import NowCast, categoria, co_movil_8h, nowcast_serie, peor_categoria  # noqa: E402

N = None
CASOS = {
    "PM_1": [N, 3, 5, 9, 13, 11, 24, 39, 79, 227, 358, 442],
    "PM_2": [3, 5, 9, 13, 11, 24, 39, 79, 227, 358, 442, 421],
    "PM_3": [5, 9, 13, 11, 24, 39, 79, 227, 358, 442, 421, 362],
    "PM_4": [9, 13, 11, 24, 39, 79, 227, 358, 442, 421, 362, 312],
    "PM_5": [13, 11, 24, 39, 79, 227, 358, 442, 421, 362, 312, 222],
    "PM_6": [11, 24, 39, 79, 227, 358, 442, 421, 362, 312, 222, 143],
    "PM_7": [24, 39, 79, 227, 358, 442, 421, 362, 312, 222, 143, 132],
    "PM_8": [39, 79, 227, 358, 442, 421, 362, 312, 222, 143, 132, 121],
    "PM_9": [79, 227, 358, 442, 421, 362, 312, 222, 143, 132, 121, N],
    "PM_10": [227, 358, 442, 421, 362, 312, 222, 143, 132, 121, N, 4],
    "PM_11": [358, 442, 421, 362, 312, 222, 143, 132, 121, N, 4, N],
    "PM_12": [442, 421, 362, 312, 222, 143, 132, 121, N, 4, N, N],
    "PM_13": [421, 362, 312, 222, 143, 132, 121, N, 4, N, N, N],
    "PM_14": [362, 312, 222, 143, 132, 121, N, 4, N, N, N, 35],
    "PM_15": [312, 222, 143, 132, 121, N, 4, N, N, N, 2, N],
    "PM_16": [222, 143, 132, 121, N, 4, N, N, N, 2, N, N],
    "PM_17": [143, 132, 121, N, 4, N, N, N, 2, N, N, N],
    "PM_18": [132, 121, N, 4, N, N, N, 2, N, N, N, N],
    "PM_19": [121, N, 4, N, N, N, N, N, 2, N, N, 8],
    "PM_20": [N, 4, N, N, N, N, N, 2, N, N, 8, 32],
    "PM_21": [4, N, N, N, N, N, 2, N, N, 8, 32, 49],
    "PM_22": [N, N, N, N, N, 2, N, N, 8, 32, 49, 38],
    "PM_23": [N, N, N, N, 2, N, N, 8, 32, 49, 38, 39],
    "PM_24": [N, N, N, 2, N, N, 8, 32, 49, 38, 39, 48],
}
ESPERADOS = [240, 266, 259, 237, 196, 148, 119, 102, 102, 36, N, N, N, N, N, N, N, N, N, 16, 26, 26, 26, 30]


def test_nowcast_casos_profesora():
    for (nombre, vals), esperado in zip(CASOS.items(), ESPERADOS):
        v = [None if x is None else float(x) for x in vals]
        assert NowCast(v, 1) == esperado, nombre


def test_nowcast_serie_equivale_a_ventanas():
    # Nota: las columnas PM_1..PM_24 del archivo de la profesora no forman una serie
    # deslizante continua (p. ej. PM_19), así que se prueba la ventana sobre una serie propia.
    crudo = [None, 3, 5, 9, 13, 11, 24, 39, 79, 227, 358, 442, 421, 362, None, 312, 222, None, None, 143]
    serie = pd.Series(crudo, dtype="float")
    r = nowcast_serie(serie, 0)["NowCast"].tolist()
    for t in range(len(crudo)):
        ventana = [None if x is None else float(x) for x in crudo[max(0, t - 11): t + 1]]
        esperado = NowCast(ventana, 0)
        obtenido = None if pd.isna(r[t]) else int(r[t])
        assert obtenido == esperado, t


def test_categorias_limites():
    assert categoria(0.058, "O3") == "Buena"
    assert categoria(0.091, "O3") == "Mala"
    assert categoria(45, "PM10") == "Buena"
    assert categoria(46, "PM10") == "Aceptable"
    assert categoria(34, "PM2.5") == "Mala"
    assert categoria(float("nan"), "CO") == "Sin datos"


def test_co_8h_requiere_6():
    s6 = pd.Series([1, 2, 1, 2, 1, 2, None, None], dtype="float")
    assert co_movil_8h(s6)["CO_8h"].iloc[7] == 1.5      # 6 de 8 -> válido
    s5 = pd.Series([1, 2, 1, 2, 1, None, None, None], dtype="float")
    assert pd.isna(co_movil_8h(s5)["CO_8h"].iloc[7])     # 5 de 8 -> no válido


def test_peor_categoria_desempate():
    cats = {"PM10": "Mala", "PM2.5": "Mala", "O3": "Buena", "CO": "Buena"}
    vals = {"PM10": 70, "PM2.5": 75, "O3": 0.02, "CO": 1}
    assert peor_categoria(cats, vals) == ("Mala", "PM2.5")
