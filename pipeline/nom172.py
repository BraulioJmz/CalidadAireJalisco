"""
Cálculos del Índice AIRE Y SALUD conforme a la NOM-172-SEMARNAT-2023.

Criterios validados en las Actividades 5 y 6 (estación SFE, enero 2025):
- O3: valor horario (ppm, 3 decimales).
- CO: promedio móvil de 8 h (hora actual + 7 previas), requiere >= 6 de 8 datos (ppm, 2 decimales).
- PM10 / PM2.5: NowCast de 12 h con la función de referencia proporcionada por la profesora.
- Categoría global: la condición más desfavorable entre los contaminantes con indicador.
- Suficiencia diaria: >= 18 de 24 datos horarios válidos (75 %).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------
CATEGORIAS = ["Buena", "Aceptable", "Mala", "Muy Mala", "Extremadamente Mala"]
RIESGO = {
    "Buena": "Bajo",
    "Aceptable": "Moderado",
    "Mala": "Alto",
    "Muy Mala": "Muy alto",
    "Extremadamente Mala": "Extremadamente alto",
}
SIN_DATOS = "Sin datos"
ORDEN = {c: i for i, c in enumerate(CATEGORIAS)}

# Límites superiores de cada categoría (Buena, Aceptable, Mala, Muy Mala).
# Partículas: columna «a partir de enero de 2024» de las tablas 4 y 5 de la NOM, la que corresponde a la fecha de los datos.
BANDAS = {
    "O3": [0.058, 0.090, 0.135, 0.175],     # ppm, promedio horario
    "CO": [5, 9, 12, 16],                   # ppm, promedio móvil 8 h
    "PM10": [45, 60, 132, 213],             # µg/m³, NowCast
    "PM2.5": [15, 33, 79, 130],             # µg/m³, NowCast
}
DECIMALES = {"O3": 3, "CO": 2, "PM10": 0, "PM2.5": 0}
UNIDADES = {"O3": "ppm", "CO": "ppm", "PM10": "µg/m³", "PM2.5": "µg/m³"}
INDICADOR_HORARIO = {
    "O3": "Promedio horario",
    "CO": "Promedio móvil 8 h",
    "PM10": "NowCast 12 h",
    "PM2.5": "NowCast 12 h",
}
INDICADOR_DIARIO = {
    "O3": "Máximo horario del día",
    "CO": "Máximo del promedio móvil 8 h",
    "PM10": "Promedio 24 h",
    "PM2.5": "Promedio 24 h",
}
SUFICIENCIA_DIARIA = 18


def categoria(valor, contaminante: str) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return SIN_DATOS
    lim = BANDAS[contaminante]
    for cat, tope in zip(CATEGORIAS[:4], lim):
        if valor <= tope:
            return cat
    return CATEGORIAS[4]


def posicion_en_banda(valor, contaminante: str) -> float:
    """Posición relativa del indicador dentro de su banda (0-1).

    Solo se usa para desempatar el contaminante responsable cuando dos o más
    contaminantes comparten la categoría más desfavorable (la NOM no define
    desempate; es un criterio del equipo y queda documentado).
    """
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return -1.0
    lim = [0.0] + BANDAS[contaminante]
    for i in range(1, len(lim)):
        if valor <= lim[i]:
            return (valor - lim[i - 1]) / (lim[i] - lim[i - 1])
    return 1.0


def peor_categoria(cats: dict, valores: dict) -> tuple[str, str]:
    """Devuelve (categoría global, contaminante responsable)."""
    validas = {k: c for k, c in cats.items() if c != SIN_DATOS}
    if not validas:
        return SIN_DATOS, ""
    peor = max(validas.values(), key=lambda c: ORDEN[c])
    empatados = [k for k, c in validas.items() if c == peor]
    responsable = max(empatados, key=lambda k: posicion_en_banda(valores[k], k))
    return peor, responsable


# ---------------------------------------------------------------------------
# NowCast — función de referencia (código proporcionado por la profesora, sin cambios)
# ---------------------------------------------------------------------------
def NowCast(valores, PM):
    """
    Calcula el NowCast según NOM-172-SEMARNAT-2023.

    Args:
        valores: Lista (longitud <=12) de concentraciones de PM en orden de más viejo a más reciente -> Hora: 0,1,2,3,4,5,6,7,8,9,10,11
                 Se asigna None para horas sin dato.Ejemplo: [32,37,29,22,30,27,30,25,22,27,None,32]
        PM: 0 para PM10, 1 para PM2.5.

    Returns:
        Entero con el promedio ponderado NowCast (µg/m³) o None si no se cumplen las condiciones.
    """
    # Condición a): Al menos 2 de las 3 horas más recientes deben existir
    ultimas_3 = valores[-3:] if len(valores) >= 3 else valores
    if sum(x is not None for x in ultimas_3) < 2:
        return None

    # Construir lista (valor, hora_consecutiva) respetando los huecos
    valores = valores[::-1]
    datos = []
    i = 0
    for v in valores:
        if v is not None:
            datos.append((v, i))
        i += 1

    if len(datos) < 2:
        return None

    # Rango y factor W (≥0.5), redondeado a 2 decimales
    solo_val = [v for v, _ in datos]
    rango = max(solo_val) - min(solo_val)
    w_raw = round(1 - (rango / max(solo_val)), 2) if max(solo_val) > 0 else 0.5
    W = w_raw if w_raw >= 0.5 else 0.5

    # Promedio ponderado (respetando el i original, sin reindexar huecos)
    num = 0.0
    den = 0.0
    for v, hora_consec in datos:
        peso = (W ** hora_consec)
        num += v * peso
        den += peso

    if den == 0:  # En caso de que el denominador sea 0 el dato es no valido
        return None

    # Promedio ponderado base (sin ajuste)
    promedio = round(num / den, 0)

    # Ajuste por tipo de PM (NOM 172, Anexo A): 0.714 para PM10, 0.694 para PM2.5
    if PM == 0:  # PM10
        promedio = round(promedio * 0.714, 0)
    else:  # PM2.5
        promedio = round(promedio * 0.694, 0)

    # Redondeo para PM a 0 decimales
    return int(promedio)


def factor_w(valores) -> float | None:
    """Reproduce el cálculo de W de la función de referencia (solo para mostrarlo)."""
    datos = [v for v in valores if v is not None]
    if len(datos) < 2:
        return None
    if max(datos) <= 0:
        return 0.5
    w_raw = round(1 - (max(datos) - min(datos)) / max(datos), 2)
    return w_raw if w_raw >= 0.5 else 0.5


def _a_lista(serie: pd.Series) -> list:
    return [None if pd.isna(x) else float(x) for x in serie]


def nowcast_serie(s: pd.Series, pm_flag: int) -> pd.DataFrame:
    """NowCast hora por hora usando solo las 12 horas previas (incluida la actual).

    `s` debe estar indexada por hora consecutiva (sin huecos en el índice).
    """
    vals = _a_lista(s)
    out = []
    for t in range(len(vals)):
        ventana = vals[max(0, t - 11): t + 1]
        ult3 = ventana[-3:]
        out.append(
            {
                "n12": sum(v is not None for v in ventana),
                "n3": sum(v is not None for v in ult3),
                "W": factor_w(ventana) if sum(v is not None for v in ult3) >= 2 else None,
                "NowCast": NowCast(ventana, pm_flag),
            }
        )
    return pd.DataFrame(out, index=s.index)


def redondeo_mitad_arriba(x: float, dec: int) -> float:
    """Redondeo 'half up' (igual que INT(x*100+0.5)/100 de la Act. 5)."""
    f = 10 ** dec
    return math.floor(x * f + 0.5 + 1e-9) / f


def co_movil_8h(s: pd.Series) -> pd.DataFrame:
    n = s.rolling(8, min_periods=1).count()
    media = s.rolling(8, min_periods=1).mean()
    prom = [
        redondeo_mitad_arriba(m, 2) if (k >= 6 and not pd.isna(m)) else np.nan
        for m, k in zip(media, n)
    ]
    return pd.DataFrame({"n8": n.astype(int), "CO_8h": prom}, index=s.index)
