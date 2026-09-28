"""
ETL - Estación Miravalle (MIR), BD_<AÑO>.xlsx
-----------------------------------------------------
Principio: el archivo original (BD_<AÑO>.xlsx) NUNCA se modifica.
Este script lo abre en modo lectura, explora, verifica calidad,
limpia y escribe los resultados en archivos nuevos dentro de data/processed.

Pipeline: raw (BD_<AÑO>.xlsx, intacto) -> exploración -> verificación de
calidad -> limpieza -> processed (listo para calcular el Índice AIRE Y
SALUD por NOM-172 en calculos.py).

Uso (desde la raíz):
    python pipeline/etl.py --periodo 2024-03                  # usa BD_2024.xlsx de la raíz
    python pipeline/etl.py --periodo 2024-03 --bd otra/ruta.xlsx

Salidas:
    data/processed/miravalle_<AÑO>_clean.csv                  año completo, todas las variables
    data/processed/calidad_datos_miravalle_por_mes.csv        % de datos disponibles por mes
    data/processed/<AAAA-MM>/miravalle_<mes><AÑO>_clean.csv   periodo + 24 h de calentamiento
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESSED = RAIZ / "data" / "processed"
STATION_CODE = "MIR"  # Miravalle, según hoja Param
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

# Identificadores de tiempo + los 6 contaminantes criterio de la NOM-172 (se incluyen aunque
# estén vacíos, p. ej. SO2, para dejar constancia de que la estación no lo mide) + meteorología.
COLUMNAS = ["STATION", "DATE", "HOUR", "DIA", "MES",
            "O3", "NO", "NO2", "NOX", "SO2", "CO", "PM10", "PM2.5",
            "IT", "ET", "RH", "WS", "WD", "PP", "ATM", "RS", "UVI"]


# =================================================================
# Rutas y rango del periodo (compartido con calculos.py y procesar.py)
# =================================================================
def rango_periodo(periodo: str) -> tuple[str, str, str]:
    """(inicio, fin, calentamiento) del mes AAAA-MM. El calentamiento son las 24 h previas,
    necesarias para las ventanas de NowCast (12 h) y CO (8 h)."""
    ini = pd.Timestamp(periodo + "-01")
    fin = ini + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=23)
    cal = ini - pd.Timedelta(hours=24)
    f = "%Y-%m-%d %H:%M"
    return ini.strftime(f), fin.strftime(f), cal.strftime(f)


def ruta_bd(anio: int) -> Path:
    return RAIZ / f"BD_{anio}.xlsx"


def ruta_limpio_anual(anio: int) -> Path:
    return PROCESSED / f"miravalle_{anio}_clean.csv"


def ruta_limpio_periodo(periodo: str) -> Path:
    t = pd.Timestamp(periodo + "-01")
    return PROCESSED / periodo / f"miravalle_{MESES[t.month - 1]}{t.year}_clean.csv"


# =================================================================
# ETL anual
# =================================================================
def ejecutar(bd: Path, anio: int) -> pd.DataFrame:
    if not bd.exists():
        raise FileNotFoundError(f"No se encontró la base original: {bd}. Colóquenla en la raíz del proyecto.")
    PROCESSED.mkdir(parents=True, exist_ok=True)

    # PASO 1. Carga y exploración inicial (no se modifica nada todavía)
    df_raw = pd.read_excel(bd, sheet_name="Data")
    print("--- PASO 1: Exploración inicial ---")
    print(f"Filas totales en 'Data': {len(df_raw):,}")
    print(f"Columnas (crudas, antes de limpiar nombres): {list(df_raw.columns)}")
    print(f"Tipos de dato (dtypes):\n{df_raw.dtypes}")
    print(f"Estaciones encontradas: {sorted(df_raw['STATION'].unique())}")
    print(f"Valores nulos por columna:\n{df_raw.isnull().sum()}")

    # PASO 2. Filtrar solo Miravalle
    df_raw.columns = df_raw.columns.str.strip()  # "MES " trae un espacio de más en el original
    faltan = [c for c in COLUMNAS if c not in df_raw.columns]
    if faltan:
        raise KeyError(f"La hoja 'Data' de {bd.name} no tiene las columnas: {', '.join(faltan)}")
    mir = df_raw[df_raw["STATION"] == STATION_CODE].copy()
    mir["DATE"] = pd.to_datetime(mir["DATE"])
    print("\n--- PASO 2: Filtrado de Miravalle ---")
    print(f"Filas de Miravalle: {len(mir):,}")
    print(f"Rango de fechas: {mir['DATE'].min()} a {mir['DATE'].max()}")

    # PASO 3. Verificación de duplicados (archivo completo y Miravalle; fila completa y llave estación+hora)
    print("\n--- PASO 3: Verificación de duplicados ---")
    print(f"Filas 100% duplicadas (archivo completo): {df_raw.duplicated().sum()}")
    print(f"Duplicados por STATION+DATE (archivo completo): {df_raw.duplicated(subset=['STATION', 'DATE']).sum()}")
    print(f"Filas 100% duplicadas (solo Miravalle): {mir.duplicated().sum()}")
    print(f"Duplicados por DATE (solo Miravalle): {mir.duplicated(subset=['DATE']).sum()}")

    # PASO 4. Tipos de dato y errores de formato
    #   PM2.5 se carga como texto por una celda con un valor no numérico; DIA y MES son
    #   fórmulas de Excel, así que se recalculan desde DATE.
    print("\n--- PASO 4: Tipos de dato y errores de formato ---")
    valor_raro = mir.loc[mir["PM2.5"].apply(lambda x: isinstance(x, str)), ["DATE", "PM2.5"]]
    print(f"Valores de texto encontrados en PM2.5 (Miravalle): {len(valor_raro)}")
    if len(valor_raro):
        print(valor_raro)
    for c in COLUMNAS[5:]:
        mir[c] = pd.to_numeric(mir[c], errors="coerce")
    mir["DIA"], mir["MES"] = mir["DATE"].dt.day, mir["DATE"].dt.month
    print("Variables convertidas a numérico. Nuevo dtype de PM2.5:", mir["PM2.5"].dtype)

    # PASO 5. Integridad de la serie de tiempo (sin huecos en la rejilla horaria)
    mir = mir.sort_values("DATE").reset_index(drop=True)
    expected_hours = pd.date_range(mir["DATE"].min(), mir["DATE"].max(), freq="h")
    missing_hours = expected_hours.difference(mir["DATE"])
    print("\n--- PASO 5: Integridad de la serie de tiempo ---")
    print(f"Horas faltantes en la rejilla (huecos en el índice, no en las mediciones): {len(missing_hours)}")

    # PASO 6. Datos disponibles por mes y contaminante (insumo para elegir el mes de cada sprint
    #   y para aplicar luego los criterios de suficiencia de la NOM-172)
    contaminantes = ["O3", "NO2", "SO2", "CO", "PM10", "PM2.5"]
    completeness = (
        mir.groupby(mir["DATE"].dt.month.rename("mes"))[contaminantes]
        .apply(lambda g: g.notna().mean() * 100)
        .round(1)
    )
    completeness.to_csv(PROCESSED / "calidad_datos_miravalle_por_mes.csv")
    print("\n--- PASO 6: % de datos disponibles por mes y contaminante ---")
    print(completeness)

    # PASO 7. Detección de valores atípicos (método IQR). Solo se reportan; no se eliminan,
    #   porque en una serie ambiental un atípico suele ser un evento real de contaminación.
    #   La clasificación detallada por periodo la hace limpieza.control_calidad (bitácora).
    print("\n--- PASO 7: Valores atípicos (IQR), año completo Miravalle ---")
    for c in ["O3", "CO", "PM10", "PM2.5"]:
        serie = mir[c].dropna()
        q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = serie[(serie < lower) | (serie > upper)]
        print(f"{c}: límites=[{lower:.3f}, {upper:.3f}]  "
              f"atípicos={len(outliers)} ({len(outliers) / len(serie) * 100:.1f}%)")

    # PASO 8. Exportar el año limpio con las columnas relevantes
    limpio = mir[COLUMNAS].copy()
    out_path = ruta_limpio_anual(anio)
    limpio.to_csv(out_path, index=False)
    print(f"\n--- PASO 8: Archivo limpio exportado a: {out_path.relative_to(RAIZ)} ---")
    return limpio


# =================================================================
# PASO 9. Recorte del periodo (p. ej. marzo 2024 para el sprint 1)
#   Se reutiliza el año limpio (pasos 4-8); aquí solo se recorta el rango de fechas.
#   Incluye las 24 h previas marcadas con CALENTAMIENTO = True: no se analizan, solo
#   llenan las ventanas móviles. Si el calentamiento cae en el año anterior, se toma de
#   su archivo limpio cuando existe.
# =================================================================
def exportar_periodo(periodo: str) -> Path:
    inicio, fin, calentamiento = rango_periodo(periodo)
    anio, anio_cal = int(periodo[:4]), int(calentamiento[:4])
    fuentes = [ruta_limpio_anual(a) for a in sorted({anio_cal, anio})]
    faltan = [f for f in fuentes if not f.exists()]
    if ruta_limpio_anual(anio) in faltan:
        raise FileNotFoundError(f"Falta {ruta_limpio_anual(anio).relative_to(RAIZ)}. Corran primero el ETL con BD_{anio}.xlsx.")
    if faltan:
        print(f"Aviso: no existe {faltan[0].relative_to(RAIZ)}; el calentamiento del periodo queda incompleto.")
    df = pd.concat([pd.read_csv(f, parse_dates=["DATE"]) for f in fuentes if f.exists()], ignore_index=True)
    periodo_df = df[(df["DATE"] >= calentamiento) & (df["DATE"] <= fin)].copy()
    periodo_df["CALENTAMIENTO"] = periodo_df["DATE"] < inicio
    ruta = ruta_limpio_periodo(periodo)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    periodo_df.to_csv(ruta, index=False)
    n = int((~periodo_df["CALENTAMIENTO"]).sum())
    print(f"Periodo {inicio} a {fin}: {n:,} filas (+{len(periodo_df) - n} de calentamiento) -> {ruta.relative_to(RAIZ)}")
    return ruta


def main() -> None:
    ap = argparse.ArgumentParser(description="ETL de la estación Miravalle desde BD_<AÑO>.xlsx")
    ap.add_argument("--periodo", default="2024-03", help="Mes a recortar, formato AAAA-MM")
    ap.add_argument("--bd", type=Path, help="Ruta a la base anual (por defecto BD_<AÑO>.xlsx en la raíz)")
    args = ap.parse_args()
    anio = int(args.periodo[:4])
    ejecutar(args.bd or ruta_bd(anio), anio)
    exportar_periodo(args.periodo)


if __name__ == "__main__":
    main()
