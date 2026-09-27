"""
Preparación y control de calidad de los datos horarios.

Principio: ningún valor alto o bajo se elimina de forma automática. Cada valor sospechoso
recibe una bandera y una clasificación ("error probable", "evento real probable",
"revisar"); solo se anulan valores físicamente imposibles.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CONTAMINANTES = ["O3", "CO", "PM10", "PM2.5"]
METEO = ["ET", "IT", "RH", "WS", "WD", "ATM"]
TODAS = ["O3", "NO", "NO2", "NOX", "SO2", "CO", "PM10", "PM2.5",
         "IT", "ET", "RH", "WS", "WD", "PP", "ATM", "RS", "UVI"]

UNIDADES = {
    "O3": "ppm", "NO": "ppm", "NO2": "ppm", "NOX": "ppm", "SO2": "ppm", "CO": "ppm",
    "PM10": "µg/m³", "PM2.5": "µg/m³", "IT": "°C", "ET": "°C", "RH": "%",
    "WS": "m/s", "WD": "grados", "PP": "mm", "ATM": "mmHg", "RS": "W/m²", "UVI": "mW/m²",
}
NOMBRES = {
    "O3": "Ozono", "NO": "Monóxido de nitrógeno", "NO2": "Dióxido de nitrógeno",
    "NOX": "Óxidos de nitrógeno", "SO2": "Dióxido de azufre", "CO": "Monóxido de carbono",
    "PM10": "Partículas PM10", "PM2.5": "Partículas PM2.5", "IT": "Temperatura interna",
    "ET": "Temperatura externa", "RH": "Humedad relativa", "WS": "Velocidad del viento",
    "WD": "Dirección del viento", "PP": "Precipitación", "ATM": "Presión atmosférica",
    "RS": "Radiación solar", "UVI": "Índice UV",
}
# Rangos físicamente posibles (fuera de ellos = error)
RANGO_FISICO = {
    "O3": (0, 1), "CO": (0, 50), "PM10": (0, 2000), "PM2.5": (0, 1500),
    "ET": (-10, 50), "IT": (-10, 50), "RH": (0, 100), "WS": (0, 60), "WD": (0, 360),
    "ATM": (550, 700),
}


def cargar(ruta_csv: str) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv)
    df.columns = [c.strip() for c in df.columns]
    df["DATE"] = pd.to_datetime(df["DATE"])
    for c in TODAS:
        df[c] = pd.to_numeric(df[c], errors="coerce")  # texto -> NaN (problema de formato)
    return df


def perfil(df: pd.DataFrame, inicio: str, fin: str) -> dict:
    """Perfil de calidad del periodo analizado."""
    per = df[(df.DATE >= inicio) & (df.DATE <= fin)].copy()
    esperado = pd.date_range(inicio, fin, freq="h")
    faltan_ts = sorted(set(esperado) - set(per.DATE))
    variables = []
    for c in TODAS:
        s = per[c]
        variables.append({
            "variable": c,
            "nombre": NOMBRES[c],
            "unidad": UNIDADES[c],
            "tipo": "numérico (float)" if s.notna().any() else "vacío",
            "validos": int(s.notna().sum()),
            "faltantes": int(s.isna().sum()),
            "disponibilidad": round(100 * s.notna().mean(), 1),
            "min": None if s.notna().sum() == 0 else float(s.min()),
            "mediana": None if s.notna().sum() == 0 else float(s.median()),
            "max": None if s.notna().sum() == 0 else float(s.max()),
            "dias_con_datos": int(s.groupby(per.DATE.dt.day).count().gt(0).sum()),
        })
    faltantes_dia = {
        c: per.groupby(per.DATE.dt.day)[c].apply(lambda s: int(s.isna().sum())).tolist()
        for c in CONTAMINANTES + ["ET", "WS", "WD"]
    }
    return {
        "registros": int(len(per)),
        "registros_esperados": int(len(esperado)),
        "timestamps_faltantes": [str(t) for t in faltan_ts],
        "duplicados": int(per.DATE.duplicated().sum()),
        "hora_convencion": f"{int(per.HOUR.min())}–{int(per.HOUR.max())}",
        "hora_consistente": bool((per.HOUR == per.DATE.dt.hour).all()),
        "variables": variables,
        "faltantes_por_dia": faltantes_dia,
    }


def _rachas(s: pd.Series, minimo: int):
    g = (s != s.shift()).cumsum()
    for _, bloque in s.groupby(g):
        if len(bloque) >= minimo and bloque.notna().all():
            yield bloque.index[0], bloque.index[-1], bloque.iloc[0], len(bloque)


def control_calidad(df: pd.DataFrame, inicio: str, fin: str) -> tuple[pd.DataFrame, list[dict]]:
    """Aplica reglas de control de calidad. Devuelve (df con banderas, bitácora)."""
    df = df.copy().set_index("DATE").sort_index()
    bitacora: list[dict] = []
    periodo = (df.index >= inicio) & (df.index <= fin)

    def registrar(ts, var, valor, regla, clasif, accion, detalle):
        bitacora.append({
            "fecha_hora": ts.strftime("%Y-%m-%d %H:%M"), "variable": var,
            "valor": None if pd.isna(valor) else float(valor), "regla": regla,
            "clasificacion": clasif, "accion": accion, "detalle": detalle,
        })

    for c in CONTAMINANTES + ["ET", "WS", "WD", "ATM"]:
        df[f"flag_{c}"] = ""

    # 1) Rango físico -> error -> se anula
    for c, (lo, hi) in RANGO_FISICO.items():
        if c not in df:
            continue
        malos = df.index[periodo & df[c].notna() & ((df[c] < lo) | (df[c] > hi))]
        for ts in malos:
            registrar(ts, c, df.at[ts, c], "Rango físico", "Error", "Anulado",
                      f"Fuera de [{lo}, {hi}] {UNIDADES[c]}")
            df.at[ts, c] = np.nan

    # 2) Consistencia PM2.5 <= PM10
    inc = df.index[periodo & (df["PM2.5"] > df["PM10"])]
    for ts in inc:
        registrar(ts, "PM2.5", df.at[ts, "PM2.5"], "PM2.5 > PM10", "Revisar", "Conservado",
                  f"PM10 = {df.at[ts, 'PM10']}")
        df.at[ts, "flag_PM2.5"] = "PM2.5>PM10"

    # 3) Ceros exactos en partículas
    for c in ["PM10", "PM2.5"]:
        for ts in df.index[periodo & (df[c] == 0)]:
            registrar(ts, c, 0, "Valor cero", "Revisar", "Conservado",
                      "Cero exacto poco probable en zona urbana; no altera la categoría (Buena).")
            df.at[ts, f"flag_{c}"] = "cero"

    # 4) Atípicos por hora del día: z robusto = (x - mediana_h) / escala_h, donde
    #    escala_h = max(1.4826·MAD_h, piso). El piso evita que horas con valores casi
    #    constantes (O3 nocturno ≈ 0) conviertan cualquier variación mínima en "atípico".
    PISO = {"O3": 0.005, "CO": 0.10, "PM10": 10.0, "PM2.5": 5.0}
    PARES = {"PM10": ["PM2.5", "CO"], "PM2.5": ["PM10", "CO"], "CO": ["PM10", "PM2.5"], "O3": []}
    mes = df[periodo]
    hora = mes.index.hour
    for c in CONTAMINANTES:
        med = mes.groupby(hora)[c].median()
        mad = mes.groupby(hora)[c].apply(lambda s: (s - s.median()).abs().median())
        escala = np.maximum(1.4826 * mad, PISO[c])
        z_todas = {p: (mes[p] - hora.map(mes.groupby(hora)[p].median()).values)
                   / np.maximum(1.4826 * hora.map(mes.groupby(hora)[p].apply(
                       lambda s: (s - s.median()).abs().median())).values, PISO[p])
                   for p in CONTAMINANTES}
        z = z_todas[c]
        for ts, zval in z[z.abs() > 3.5].dropna().items():
            antes, despues = ts - pd.Timedelta(hours=1), ts + pd.Timedelta(hours=1)
            z_vec = [z.get(t, np.nan) for t in (antes, despues)]
            if zval > 0:
                sostenido = any(pd.notna(v) and v > 2 for v in z_vec)
                pares = [p for p in PARES[c] if pd.notna(z_todas[p].get(ts, np.nan)) and z_todas[p].get(ts) > 2]
                if sostenido or pares:
                    clasif = "Evento real probable"
                    motivo = []
                    if sostenido:
                        motivo.append("el aumento se sostiene en horas vecinas")
                    if pares:
                        motivo.append(f"{', '.join(pares)} también elevado(s) a la misma hora")
                    detalle = f"Valor alto (z = {zval:.1f} vs. la misma hora del mes); " + " y ".join(motivo) + "."
                else:
                    clasif = "Revisar"
                    detalle = f"Valor alto aislado (z = {zval:.1f}) sin respaldo de horas vecinas ni de otros contaminantes."
            else:
                sostenido = any(pd.notna(v) and v < -1 for v in z_vec)
                clasif = "Valor bajo plausible" if sostenido else "Revisar"
                detalle = (f"Valor bajo (z = {zval:.1f}); "
                           + ("las horas vecinas también son bajas, consistente con dispersión o química del día."
                              if sostenido else "caída aislada respecto a las horas vecinas."))
            registrar(ts, c, df.at[ts, c], "Atípico por hora del día (|z| > 3.5)", clasif, "Conservado", detalle)
            df.at[ts, f"flag_{c}"] = {"Evento real probable": "alto-evento", "Revisar": "revisar",
                                      "Valor bajo plausible": "bajo"}[clasif]

    # 5) Rachas de valores idénticos (posible sensor pegado)
    for c, minimo in [("O3", 6), ("CO", 6), ("PM10", 6), ("PM2.5", 6), ("WS", 6), ("ET", 6)]:
        for a, b, v, n in _rachas(df.loc[periodo, c], minimo):
            clas = "Revisar"
            det = f"{n} horas consecutivas con el mismo valor ({v})."
            if c == "WS":
                det += " Coincide con el mínimo que reporta el sensor (0.4 m/s): se interpreta como calma."
            registrar(a, c, v, "Valor constante", clas, "Conservado", det + f" Hasta {b:%Y-%m-%d %H:%M}.")
            df.loc[a:b, f"flag_{c}"] = "constante"

    # 6) Resolución/umbral del anemómetro
    ws = df.loc[periodo, "WS"].dropna()
    if len(ws):
        registrar(ws.index[0], "WS", ws.min(), "Resolución del sensor", "Limitación", "Conservado",
                  f"Solo se registran {ws.nunique()} valores distintos entre {ws.min()} y {ws.max()} m/s "
                  f"(paso 0.1). El valor mínimo aparece {int((ws == ws.min()).sum())} veces: posible umbral de arranque.")

    return df.reset_index(), bitacora


def sector_viento(grados):
    if grados is None or pd.isna(grados):
        return ""
    sectores = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    return sectores[int((grados % 360) / 22.5 + 0.5) % 16]


def media_vectorial(direcciones: pd.Series, velocidades: pd.Series | None = None):
    d = direcciones.dropna()
    if d.empty:
        return np.nan
    v = velocidades.reindex(d.index).fillna(1) if velocidades is not None else pd.Series(1, index=d.index)
    rad = np.deg2rad(d)
    u, w = (v * np.sin(rad)).sum(), (v * np.cos(rad)).sum()
    return float((np.rad2deg(np.arctan2(u, w)) + 360) % 360)
