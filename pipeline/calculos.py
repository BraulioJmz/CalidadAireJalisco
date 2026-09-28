"""
Cálculos NOM-172-SEMARNAT-2023 horarios y diarios — estación Miravalle (MIR).

Entrada:  data/processed/<AAAA-MM>/miravalle_<mes><AÑO>_clean.csv   (lo genera etl.py)
Salidas:  data/processed/<AAAA-MM>/Archivo1_Calculos_Horarios.csv
          data/processed/<AAAA-MM>/Archivo2_Calculos_Diarios.csv

Estos dos archivos son la fuente de los cálculos del dashboard: procesar.py los lee para armar
el JSON del sitio. Las reglas (NowCast de la profesora, CO 8 h, bandas, redondeos, suficiencia,
categoría global y contaminante responsable) viven en nom172.py y no se duplican aquí.

Uso (desde la raíz):
    python pipeline/calculos.py --periodo 2024-03
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import etl
import limpieza as L
import nom172 as N

ESTACION = etl.STATION_CODE

# Orden en que se evalúan los contaminantes para la categoría global. Importa solo si dos quedan
# empatados en categoría y en posición dentro de la banda (se conserva el del pipeline validado).
ORDEN_HORARIO = ["O3", "CO", "PM10", "PM2.5"]
ORDEN_DIARIO = ["PM2.5", "PM10", "O3", "CO"]

# Indicador horario de cada contaminante -> (columna del indicador, columna de categoría)
INDICADOR = {
    "O3": ("O3", "Cat_O3"),
    "CO": ("CO_8h", "Cat_CO"),
    "PM10": ("NowCast_PM10", "Cat_PM10"),
    "PM2.5": ("NowCast_PM25", "Cat_PM25"),
}

COLUMNAS_ARCHIVO1 = (
    ["STATION", "DATE", "HOUR", "REGISTRO_EN_FUENTE", "O3", "CO", "PM10", "PM2.5",
     "NowCast_PM10", "NowCast_PM25", "CO_8h"]
    + [cat for _, cat in INDICADOR.values()]
    + ["Cat_Global_Horaria", "Responsable_Horario",
       # Detalle de las ventanas (para auditar el NowCast y el CO 8 h)
       "Datos8h_CO", "Datos12h_PM10", "Datos3h_PM10", "W_PM10", "Datos12h_PM25", "Datos3h_PM25", "W_PM25"]
)


def ruta_archivo1(periodo: str) -> Path:
    return etl.PROCESSED / periodo / "Archivo1_Calculos_Horarios.csv"


def ruta_archivo2(periodo: str) -> Path:
    return etl.PROCESSED / periodo / "Archivo2_Calculos_Diarios.csv"


def cargar_periodo(periodo: str) -> pd.DataFrame:
    ruta = etl.ruta_limpio_periodo(periodo)
    if not ruta.exists():
        raise FileNotFoundError(f"Falta {ruta.relative_to(etl.RAIZ)}. Corran primero: python pipeline/etl.py --periodo {periodo}")
    return L.cargar(ruta)


# ----- ARCHIVO 1: CÁLCULOS HORARIOS -----
def calcular_horario(df: pd.DataFrame, periodo: str) -> pd.DataFrame:
    """`df` ya pasó por el control de calidad; incluye las 24 h de calentamiento."""
    inicio, fin, calentamiento = etl.rango_periodo(periodo)
    df = df.set_index("DATE").sort_index()
    df = df.reindex(pd.date_range(calentamiento, fin, freq="h"))  # rejilla completa: las ventanas cuentan horas reales
    df.index.name = "DATE"
    df["REGISTRO_EN_FUENTE"] = np.where(df["STATION"].notna(), "Sí", "No")
    df["STATION"] = ESTACION

    # CO: promedio móvil 8 h, ≥ 6 de 8 datos, redondeo half-up a 2 decimales
    co = N.co_movil_8h(df["CO"])
    df["CO_8h"], df["Datos8h_CO"] = co["CO_8h"], co["n8"]

    # PM10 y PM2.5: NowCast 12 h con la función de la profesora (nom172.NowCast, sin cambios)
    for pm, flag, suf in [("PM10", 0, "PM10"), ("PM2.5", 1, "PM25")]:
        nc = N.nowcast_serie(df[pm], flag)
        df[f"NowCast_{suf}"] = pd.to_numeric(nc["NowCast"])
        df[f"W_{suf}"], df[f"Datos12h_{suf}"], df[f"Datos3h_{suf}"] = nc["W"], nc["n12"], nc["n3"]

    # Categorías por contaminante (bandas validadas en nom172.BANDAS)
    for c, (col, cat) in INDICADOR.items():
        df[cat] = [N.categoria(v, c) for v in df[col]]

    # Categoría global horaria y contaminante responsable
    glob, resp = [], []
    for _, r in df.iterrows():
        cats = {c: r[INDICADOR[c][1]] for c in ORDEN_HORARIO}
        vals = {c: r[INDICADOR[c][0]] for c in ORDEN_HORARIO}
        g, p = N.peor_categoria(cats, vals)
        glob.append(g)
        resp.append(p)
    df["Cat_Global_Horaria"], df["Responsable_Horario"] = glob, resp

    df = df.loc[inicio:fin].copy()  # el calentamiento solo llena ventanas
    df["HOUR"] = df.index.hour
    return df.reset_index()


# ----- ARCHIVO 2: CÁLCULOS DIARIOS -----
def calcular_diario(h: pd.DataFrame) -> pd.DataFrame:
    datos_diarios = []
    for dia, grupo in h.groupby(h["DATE"].dt.normalize()):
        fila_dia = {"Fecha": dia}
        cats, vals = {}, {}
        for cont, col_origen, col_indicador, tipo_calculo in [
            ("PM10", "PM10", "PM10", "promedio_24h"),
            ("PM2.5", "PM2.5", "PM2.5", "promedio_24h"),
            ("CO", "CO", "CO_8h", "maximo"),
            ("O3", "O3", "O3", "maximo"),
        ]:
            # 1. Datos válidos de la lectura original del instrumento (≥ 18 de 24)
            validos = int(grupo[col_origen].count())
            cumple = "Cumple" if validos >= N.SUFICIENCIA_DIARIA else "No cumple"

            # 2. Indicador diario si cumple, con los decimales de la NOM (O3 3, CO 2, PM 0) y redondeo half-up
            indicador = np.nan
            serie = grupo[col_indicador]
            if cumple == "Cumple" and serie.notna().any():
                valor = serie.mean() if tipo_calculo == "promedio_24h" else serie.max()
                indicador = N.redondeo_mitad_arriba(float(valor), N.DECIMALES[cont])  # NOM 5.2.4: 5 sube

            # 3. Categoría diaria
            categoria = N.categoria(indicador, cont)
            fila_dia[f"Validos_{cont}"] = validos
            fila_dia[f"Suficiencia_{cont}"] = cumple
            fila_dia[f"Indicador_{cont}"] = indicador
            fila_dia[f"Cat_{cont}"] = categoria
            cats[cont], vals[cont] = categoria, indicador

        g, p = N.peor_categoria({c: cats[c] for c in ORDEN_DIARIO}, {c: vals[c] for c in ORDEN_DIARIO})
        fila_dia["Cat_Global_Diaria"], fila_dia["Responsable_Diario"] = g, p
        datos_diarios.append(fila_dia)
    return pd.DataFrame(datos_diarios)


def guardar(h: pd.DataFrame, d: pd.DataFrame, periodo: str) -> tuple[Path, Path]:
    a1, a2 = ruta_archivo1(periodo), ruta_archivo2(periodo)
    a1.parent.mkdir(parents=True, exist_ok=True)
    h[COLUMNAS_ARCHIVO1].to_csv(a1, index=False, date_format="%Y-%m-%d %H:%M:%S")
    d.to_csv(a2, index=False, date_format="%Y-%m-%d")
    return a1, a2


def ejecutar(periodo: str) -> tuple[pd.DataFrame, list[dict], dict]:
    """Carga el periodo limpio, aplica el control de calidad y genera Archivo1 y Archivo2.

    Devuelve (datos con banderas y meteorología, bitácora, perfil) para que procesar.py arme el JSON.
    """
    inicio, fin, _ = etl.rango_periodo(periodo)
    crudo = cargar_periodo(periodo)
    perfil = L.perfil(crudo, inicio, fin)
    limpio, bitacora = L.control_calidad(crudo, inicio, fin)
    h = calcular_horario(limpio, periodo)
    d = calcular_diario(h)
    a1, a2 = guardar(h, d, periodo)
    print(f"Archivo 1 generado con éxito: {a1.relative_to(etl.RAIZ)}")
    print(f"Archivo 2 generado con éxito: {a2.relative_to(etl.RAIZ)}")
    return limpio, bitacora, perfil


def main() -> None:
    ap = argparse.ArgumentParser(description="Cálculos NOM-172 horarios y diarios de un periodo")
    ap.add_argument("--periodo", default="2024-03", help="Mes a procesar, formato AAAA-MM")
    ejecutar(ap.parse_args().periodo)


if __name__ == "__main__":
    main()
