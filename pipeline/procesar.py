"""
Pipeline reproducible NOM-172-SEMARNAT-2023 — estación Miravalle (MIR).

Orquesta los tres pasos con el mismo código para cada sprint:

    1. etl.py       BD_<AÑO>.xlsx (raíz, solo lectura) -> data/processed/miravalle_<AÑO>_clean.csv
                    y el recorte del periodo data/processed/<AAAA-MM>/miravalle_<mes><AÑO>_clean.csv
    2. calculos.py  periodo limpio -> Archivo1_Calculos_Horarios.csv y Archivo2_Calculos_Diarios.csv
    3. procesar.py  lee Archivo1 y Archivo2 y arma el JSON del sitio y los Excel descargables

    python pipeline/procesar.py --periodo 2024-03          # Sprint 1
    python pipeline/procesar.py --periodo 2024-04          # otro mes
    python pipeline/procesar.py --bd ruta/BD_2024.xlsx     # base anual en otra ruta

Si BD_<AÑO>.xlsx no está en la raíz, se usa el año limpio ya versionado en data/processed.

Salidas por periodo (AAAA-MM):
    data/processed/<periodo>/Archivo1_Calculos_Horarios.csv, Archivo2_Calculos_Diarios.csv
    data/processed/<periodo>/MIR_<periodo>_horario.xlsx, MIR_<periodo>_diario.xlsx, bitacora_limpieza.csv
    web/data/periodos/<periodo>.json      (insumo del sitio Next.js)
    web/data/periodos/index.json          (catálogo de periodos procesados)
    web/public/descargas/<periodo>/       (copias descargables)
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

import calculos
import etl
import reporte
import limpieza as L
import nom172 as N

RAIZ = etl.RAIZ
ESTACION = etl.STATION_CODE
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

# Eventos de calendario que ayudan a interpretar (no se usan en los cálculos)
EVENTOS = [
    ("2024-03-24", "2024-03-31", "Semana Santa", "SS"),
    ("2024-04-01", "2024-04-07", "Semana de Pascua", "SP"),
    ("2024-12-16", "2024-12-31", "Vacaciones de invierno", "VI"),
]

# Se fijan en configurar(periodo)
PERIODO = INICIO = FIN = CALENTAMIENTO = ""
OUT = WEB = DESC = Path()


def configurar(periodo: str) -> None:
    global PERIODO, INICIO, FIN, CALENTAMIENTO, OUT, WEB, DESC
    PERIODO = periodo
    INICIO, FIN, CALENTAMIENTO = etl.rango_periodo(periodo)  # calentamiento: NowCast 12 h y CO 8 h
    OUT = RAIZ / "data" / "processed" / periodo
    WEB = RAIZ / "web" / "data" / "periodos"
    DESC = RAIZ / "web" / "public" / "descargas" / periodo


def nombre_periodo() -> str:
    t = pd.Timestamp(INICIO)
    return f"{MESES[t.month - 1]} {t.year}"


def evento(fecha: pd.Timestamp):
    f = fecha.strftime("%Y-%m-%d")
    for a, b, nombre, sigla in EVENTOS:
        if a <= f <= b:
            return nombre, sigla
    return None, None


# Tabla 12 de la NOM-172-SEMARNAT-2023: mensajes por categoría para tres grupos poblacionales (texto oficial).
#   general            población en general
#   menores_gestantes  menores de 12 años y personas gestantes
#   sensibles          personas con enfermedades cardiovasculares o respiratorias y mayores de 60 años
_INFORMATE = "Infórmate sobre la evolución de la calidad del aire."
_MEDICO = "Si presentas algún síntoma o molestia o tienes dudas, busca el consejo de tu médico."
MENSAJES = {
    "Buena": {
        "general": "Disfruta las actividades al aire libre.",
        "menores_gestantes": "Disfruta las actividades al aire libre.",
        "sensibles": "Disfruta las actividades al aire libre.",
    },
    "Aceptable": {
        "general": f"Disfruta las actividades al aire libre. {_INFORMATE}",
        "menores_gestantes": f"Disfruta las actividades al aire libre. {_INFORMATE}",
        "sensibles": ("Es posible realizar actividades físicas al aire libre como trotar suave, caminar a paso rápido o moverse "
                      "en bicicleta, monopatín/scooter, patines y patinetas. Reduce las actividades físicas vigorosas al aire libre "
                      "como ejercicios aeróbicos, jugar fútbol, básquetbol, voleibol, atletismo, ciclismo deportivo o correr. "
                      f"{_MEDICO} {_INFORMATE}"),
    },
    "Mala": {
        "general": ("Es posible realizar actividades al aire libre. Si presenta síntomas como tos o falta de aire, toma más "
                    f"descansos y realiza actividades menos vigorosas. {_INFORMATE}"),
        "menores_gestantes": ("Es posible realizar actividades físicas al aire libre como trotar suave, caminar a paso rápido o "
                              "moverse en bicicleta, monopatín/scooter, patines y patinetas; aumenta los períodos de descanso. "
                              "Reduce las actividades físicas vigorosas al aire libre como ejercicios aeróbicos, jugar fútbol, "
                              "básquetbol, voleibol, atletismo, ciclismo deportivo, etc. Si se presentan síntomas respiratorios o "
                              f"cardiacos, suspende la actividad y acude a tu médico. {_INFORMATE}"),
        "sensibles": ("Reduce las actividades físicas vigorosas al aire libre como ejercicios aeróbicos, jugar fútbol, básquetbol, "
                      "voleibol, atletismo, ciclismo deportivo o correr, trotar suave, caminar a paso rápido o moverse en "
                      f"bicicleta, monopatín/scooter, patines y patinetas. {_MEDICO} {_INFORMATE}"),
    },
    "Muy Mala": {
        "general": ("Reduce las actividades físicas al aire libre y de preferencia realízalas en espacios interiores, siempre y "
                    "cuando se trate de un espacio libre de humo de tabaco. Evita la actividad física vigorosa o prolongada al "
                    f"aire libre. {_INFORMATE}"),
        "menores_gestantes": ("Reduce las actividades físicas al aire libre y de preferencia realízalas en espacios interiores, "
                              "siempre y cuando se trate de un espacio libre de humo de tabaco. Evita la actividad física "
                              f"vigorosa o prolongada al aire libre. {_INFORMATE}"),
        "sensibles": ("Es posible realizar actividades físicas en espacios interiores, siempre y cuando se trate de un espacio "
                      "libre de humo de tabaco. Evita las actividades físicas vigorosas y moderadas, así como el tiempo de "
                      f"estancia al aire libre. {_MEDICO} {_INFORMATE}"),
    },
    "Extremadamente Mala": {
        k: ("Permanece en espacios interiores en donde puedes realizar actividades físicas, reprograma tus actividades al "
            f"aire libre y si presentas síntomas respiratorios y/o cardiacos acude al médico. {_INFORMATE}")
        for k in ("general", "menores_gestantes", "sensibles")
    },
    "Sin datos": {
        "general": "Sin información suficiente para calcular el Índice AIRE Y SALUD en esta hora.",
        "menores_gestantes": "",
        "sensibles": "",
    },
}

# Tabla 10 de la NOM-172-SEMARNAT-2023: descripción del riesgo por categoría.
DESCRIPCION_RIESGO = {
    "Buena": {"general": "El riesgo en salud es mínimo o nulo.", "sensible": "El riesgo en salud es mínimo o nulo."},
    "Aceptable": {"general": "El riesgo en salud es mínimo.",
                  "sensible": ("Personas que son sensibles al ozono (O3) o material particulado (PM10 y PM2.5) pueden "
                               "experimentar irritación de ojos y síntomas respiratorios como tos, irritación de vías "
                               "respiratorias, expectoración o flema, dificultad para respirar o sibilancias.")},
    "Mala": {"general": "Es poco probable que se vea afectada.",
             "sensible": "Incremento en el riesgo de tener síntomas respiratorios y/o disminución en la función pulmonar."},
    "Muy Mala": {"general": "Se puede presentar daños a la salud.",
                 "sensible": ("Pueden experimentar un agravamiento de asma, enfermedad pulmonar obstructiva crónica o evento "
                              "cardiovascular e incremento en la probabilidad de muerte prematura en personas con enfermedad "
                              "pulmonar obstructiva crónica y cardiaca.")},
    "Extremadamente Mala": {"general": "Es más probable que cualquier persona se vea afectada por efectos graves a la salud.",
                            "sensible": "Es más probable que cualquier persona se vea afectada por efectos graves a la salud."},
}


# Nombres de Archivo1/Archivo2 -> nombres que usan el JSON, los Excel y el sitio
REN_HORARIO = {
    "DATE": "FECHA_HORA", "NowCast_PM10": "PM10_NowCast", "NowCast_PM25": "PM2.5_NowCast",
    "Cat_PM25": "Cat_PM2.5", "Cat_Global_Horaria": "Cat_global", "Responsable_Horario": "Responsable",
    "Datos8h_CO": "CO_datos_8h", "Datos12h_PM10": "PM10_datos_12h", "Datos3h_PM10": "PM10_datos_3h",
    "W_PM10": "PM10_W", "Datos12h_PM25": "PM2.5_datos_12h", "Datos3h_PM25": "PM2.5_datos_3h", "W_PM25": "PM2.5_W",
}
METEO_Y_BANDERAS = ["NO2", "SO2", "ET", "IT", "RH", "WS", "WD", "ATM",
                    "flag_O3", "flag_CO", "flag_PM10", "flag_PM2.5", "flag_WS"]


def leer_horario(limpio: pd.DataFrame) -> pd.DataFrame:
    """Archivo1 (cálculos) + meteorología y banderas del periodo limpio -> tabla horaria del sitio."""
    a1 = pd.read_csv(calculos.ruta_archivo1(PERIODO), parse_dates=["DATE"], keep_default_na=False, na_values=[""])
    df = a1.rename(columns=REN_HORARIO).set_index("FECHA_HORA")
    df["Responsable"] = df["Responsable"].fillna("")
    meteo = limpio.set_index("DATE")[METEO_Y_BANDERAS]
    df = df.join(meteo)
    for c in [c for c in METEO_Y_BANDERAS if c.startswith("flag_")]:
        df[c] = df[c].fillna("")
    df["Riesgo"] = df["Cat_global"].map(N.RIESGO).fillna("")
    prev = df["Cat_global"].shift()
    df["Cambio_categoria"] = (df["Cat_global"] != prev) & prev.notna()
    df["Mensaje"] = df["Cat_global"].map(lambda c: MENSAJES[c]["general"])
    df["Sector_viento"] = df["WD"].map(L.sector_viento)
    df["FECHA"] = df.index.normalize()
    df["HORA"] = df.index.hour
    return df


def leer_diario(h: pd.DataFrame) -> pd.DataFrame:
    """Archivo2 (cálculos) + la perspectiva horaria y la meteorología de cada día -> tabla diaria del sitio."""
    a2 = pd.read_csv(calculos.ruta_archivo2(PERIODO), parse_dates=["Fecha"], keep_default_na=False, na_values=[""])
    filas = []
    for _, r in a2.iterrows():
        fecha = r["Fecha"]
        fila = {"FECHA": fecha, "ESTACION": ESTACION, "dia_semana": DIAS[fecha.weekday()]}
        for c in ["PM2.5", "PM10", "O3", "CO"]:
            fila.update({f"{c}_validos": int(r[f"Validos_{c}"]), f"{c}_suficiencia": r[f"Suficiencia_{c}"],
                         f"{c}_indicador": r[f"Indicador_{c}"], f"{c}_categoria": r[f"Cat_{c}"]})
        g = r["Cat_Global_Diaria"]
        fila["Cat_global"], fila["Responsable"] = g, r["Responsable_Diario"] if isinstance(r["Responsable_Diario"], str) else ""
        # Perspectiva horaria dentro del día
        d = h[h["FECHA"] == fecha]
        horas = d["Cat_global"]
        fila["horas_con_categoria"] = int((horas != N.SIN_DATOS).sum())
        for cat in N.CATEGORIAS:
            fila[f"horas_{cat}"] = int((horas == cat).sum())
        validas = horas[horas != N.SIN_DATOS]
        fila["peor_horaria"] = max(validas, key=lambda c: N.ORDEN[c]) if len(validas) else N.SIN_DATOS
        fila["horas_peores_que_diaria"] = int(sum(N.ORDEN[c] > N.ORDEN.get(g, 99) for c in validas)) if g != N.SIN_DATOS else None
        fila["cambios_categoria"] = int(d["Cambio_categoria"].sum())
        resp_h = d.loc[d["Cat_global"] != N.SIN_DATOS, "Responsable"].value_counts()
        fila["responsable_horario_frecuente"] = resp_h.index[0] if len(resp_h) else ""
        # Meteorología resumida
        fila["ET_media"] = round(float(d["ET"].mean()), 1) if d["ET"].notna().any() else np.nan
        fila["ET_max"] = float(d["ET"].max()) if d["ET"].notna().any() else np.nan
        fila["WS_media"] = round(float(d["WS"].mean()), 2) if d["WS"].notna().any() else np.nan
        wd = L.media_vectorial(d["WD"], d["WS"])
        fila["WD_vectorial"] = round(wd) if pd.notna(wd) else np.nan
        fila["Sector_dominante"] = L.sector_viento(wd)
        ev, sigla = evento(fecha)
        fila["evento"], fila["evento_sigla"] = ev, sigla
        filas.append(fila)
    return pd.DataFrame(filas)


def seleccionar_periodo(h: pd.DataFrame, horas: int = 72) -> dict:
    """Ventana de `horas` con más cambios de categoría global; desempata la peor categoría alcanzada.

    Solo se consideran ventanas que empiezan a las 00:00 y con >= 90 % de horas con categoría.
    """
    candidatos = []
    for inicio in pd.date_range(INICIO, pd.Timestamp(FIN) - pd.Timedelta(hours=horas - 1), freq="D"):
        w = h.loc[inicio: inicio + pd.Timedelta(hours=horas - 1)]
        cobertura = (w["Cat_global"] != N.SIN_DATOS).mean()
        if cobertura < 0.9:
            continue
        peor = max((N.ORDEN[c] for c in w["Cat_global"] if c != N.SIN_DATOS), default=-1)
        horas_mala = int(w["Cat_global"].map(lambda c: N.ORDEN.get(c, -1) >= 2).sum())
        responsables = w.loc[w["Cat_global"] != "Buena", "Responsable"].nunique()
        candidatos.append({
            "inicio": inicio, "cambios": int(w["Cambio_categoria"].sum()), "peor": peor,
            "horas_mala": horas_mala, "contaminantes_responsables": int(responsables),
        })
    c = pd.DataFrame(candidatos).sort_values(
        ["peor", "contaminantes_responsables", "cambios", "horas_mala"], ascending=False)
    top = c.iloc[0]
    return {
        "inicio": top["inicio"].strftime("%Y-%m-%d %H:%M"),
        "fin": (top["inicio"] + pd.Timedelta(hours=horas - 1)).strftime("%Y-%m-%d %H:%M"),
        "cambios": int(top["cambios"]),
        "horas_mala_o_peor": int(top["horas_mala"]),
        "peor": N.CATEGORIAS[int(top["peor"])],
        "contaminantes_responsables": int(top["contaminantes_responsables"]),
        "criterio": ("Ventanas de 72 h que inician a las 00:00 con ≥ 90 % de horas con categoría. Se ordenan por: "
                     "(1) peor categoría alcanzada, (2) número de contaminantes distintos que definieron una categoría "
                     "distinta de Buena, (3) número de cambios de categoría, (4) horas en Mala o peor."),
        "ranking": [
            {"inicio": r.inicio.strftime("%Y-%m-%d"), "cambios": int(r.cambios),
             "peor": N.CATEGORIAS[int(r.peor)], "horas_mala": int(r.horas_mala),
             "contaminantes": int(r.contaminantes_responsables)}
            for r in c.head(8).itertuples()
        ],
    }


def exportar_excel(h: pd.DataFrame, d: pd.DataFrame, bitacora: pd.DataFrame, perfil: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cols_h = ["STATION", "FECHA", "HORA", "O3", "CO", "PM10", "PM2.5", "NO2", "SO2", "ET", "IT", "RH", "WS",
              "WD", "ATM", "REGISTRO_EN_FUENTE",
              "CO_datos_8h", "CO_8h",
              "PM10_datos_12h", "PM10_datos_3h", "PM10_W", "PM10_NowCast",
              "PM2.5_datos_12h", "PM2.5_datos_3h", "PM2.5_W", "PM2.5_NowCast",
              "Cat_O3", "Cat_CO", "Cat_PM10", "Cat_PM2.5", "Cat_global", "Responsable", "Riesgo",
              "Cambio_categoria", "Mensaje", "Sector_viento",
              "flag_O3", "flag_CO", "flag_PM10", "flag_PM2.5", "flag_WS"]
    hx = h.reset_index()[["FECHA_HORA"] + cols_h]
    with pd.ExcelWriter(OUT / f"MIR_{PERIODO}_horario.xlsx", engine="xlsxwriter",
                        datetime_format="yyyy-mm-dd hh:mm", date_format="yyyy-mm-dd") as xw:
        hx.to_excel(xw, sheet_name="Cálculos horarios", index=False)
        pd.DataFrame(perfil["variables"]).to_excel(xw, sheet_name="Perfil de variables", index=False)
        bitacora.to_excel(xw, sheet_name="Bitácora limpieza", index=False)
        metodologia().to_excel(xw, sheet_name="Metodología", index=False)
        for ws in xw.sheets.values():
            ws.freeze_panes(1, 1)
            ws.set_column(0, 60, 14)
    with pd.ExcelWriter(OUT / f"MIR_{PERIODO}_diario.xlsx", engine="xlsxwriter",
                        date_format="yyyy-mm-dd", datetime_format="yyyy-mm-dd") as xw:
        d.to_excel(xw, sheet_name="Cálculos diarios", index=False)
        metodologia().to_excel(xw, sheet_name="Metodología", index=False)
        for ws in xw.sheets.values():
            ws.freeze_panes(1, 1)
            ws.set_column(0, 60, 14)
    bitacora.to_csv(OUT / "bitacora_limpieza.csv", index=False)


def metodologia() -> pd.DataFrame:
    filas = [
        ("Fuente", f"SEMADET Jalisco, BD_{PERIODO[:4]}.xlsx (hoja Data), estación Miravalle (MIR). Unidades de la hoja Param."),
        ("Proceso", "etl.py (limpieza del año) → calculos.py (Archivo1 horario y Archivo2 diario) → procesar.py (JSON del sitio y Excel)."),
        ("Norma", "NOM-172-SEMARNAT-2023. Criterios validados en Actividades 5 y 6 (SFE, enero 2025)."),
        ("Periodo", f"{INICIO[:10]} a {FIN[:10]}, horas 0–23 (hora local). Las 24 h previas ({CALENTAMIENTO[:10]}) solo calientan las ventanas."),
        ("O3", "Indicador horario = concentración horaria (ppm, 3 decimales). Diario = máximo horario."),
        ("CO", "Promedio móvil 8 h (hora actual + 7 previas), ≥ 6 de 8 datos, 2 decimales (half-up). Diario = máximo del promedio 8 h."),
        ("PM10 / PM2.5", "NowCast 12 h con la función de referencia de la profesora (≥ 2 de las 3 horas recientes; W ≥ 0.5; "
                         "factor 0.714 PM10 / 0.694 PM2.5). Diario = promedio 24 h redondeado a entero."),
        ("Bandas", "Tablas 4 a 9 de la NOM. O3: 0.058/0.090/0.135/0.175 ppm · CO: 5/9/12/16 ppm · PM10: 45/60/132/213 µg/m³ · "
                   "PM2.5: 15/33/79/130 µg/m³. Para partículas se usa la columna «a partir de enero de 2024», que corresponde a la fecha de los datos."),
        ("Redondeo", "Numeral 5.2.4: O3 a 3 decimales, CO a 2 y PM a entero; si la cifra siguiente es 5 o más, se sube. "
                     "En marzo 2024 el redondeo interno de la función NowCast de referencia coincide con esta regla en todas las horas."),
        ("Mensajes", "Tabla 12 de la NOM, textos oficiales para tres grupos: población en general; menores de 12 años y personas "
                     "gestantes; personas con enfermedades cardiovasculares o respiratorias y mayores de 60 años."),
        ("Suficiencia diaria", "≥ 18 de 24 datos horarios válidos (75 %) por contaminante; si no cumple, no se calcula indicador."),
        ("Categoría global", "La más desfavorable entre los contaminantes con indicador (NO2 y SO2 no se miden en MIR)."),
        ("Contaminante responsable", "El de la categoría más desfavorable. Si empatan, el que está más cerca del límite superior "
                                     "de su banda (criterio del equipo; la NOM no define desempate)."),
        ("Limpieza", "No se eliminan valores altos o bajos automáticamente. Solo se anulan valores físicamente imposibles; "
                     "el resto recibe bandera y clasificación en la bitácora."),
        ("Imputación", "Ninguna. Las variables sin datos (p. ej. humedad relativa en marzo 2024) se reportan como limitación."),
    ]
    return pd.DataFrame(filas, columns=["Elemento", "Criterio"])


def _limpio(v):
    if isinstance(v, (np.floating, float)):
        return None if np.isnan(v) else round(float(v), 4)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d %H:%M")
    return v


def exportar_json(h, d, bitacora, perfil, periodo) -> None:
    WEB.mkdir(parents=True, exist_ok=True)
    cols = ["O3", "CO", "PM10", "PM2.5", "ET", "WS", "WD", "Sector_viento", "CO_8h", "CO_datos_8h",
            "PM10_NowCast", "PM10_W", "PM10_datos_3h", "PM10_datos_12h", "PM2.5_NowCast", "PM2.5_W", "PM2.5_datos_3h", "PM2.5_datos_12h",
            "Cat_O3", "Cat_CO", "Cat_PM10", "Cat_PM2.5", "Cat_global", "Responsable", "Cambio_categoria",
            "flag_O3", "flag_CO", "flag_PM10", "flag_PM2.5", "flag_WS"]
    horario = [{"t": ts.strftime("%Y-%m-%d %H:%M"), **{c: _limpio(r[c]) for c in cols}} for ts, r in h.iterrows()]
    diario = [{k: _limpio(v) for k, v in r.items()} for r in d.to_dict("records")]
    for r in diario:
        r["FECHA"] = r["FECHA"][:10]

    dias_cat = d.loc[d.Cat_global != N.SIN_DATOS, "Cat_global"].value_counts()
    dom = d.loc[d.Cat_global != N.SIN_DATOS, "Responsable"].value_counts()
    horas_cat = h.loc[h.Cat_global != N.SIN_DATOS, "Cat_global"].value_counts()
    horas_resp = h.loc[h.Cat_global != N.SIN_DATOS, "Responsable"].value_counts()
    numeralia = {
        "dias_mes": int(len(d)),
        "dias_con_categoria": int((d.Cat_global != N.SIN_DATOS).sum()),
        "dias_sin_datos": d.loc[d.Cat_global == N.SIN_DATOS, "FECHA"].dt.strftime("%Y-%m-%d").tolist(),
        "dias_por_categoria": {c: int(dias_cat.get(c, 0)) for c in N.CATEGORIAS},
        "dias_por_responsable": {k: int(v) for k, v in dom.items()},
        "horas_con_categoria": int((h.Cat_global != N.SIN_DATOS).sum()),
        "horas_por_categoria": {c: int(horas_cat.get(c, 0)) for c in N.CATEGORIAS},
        "horas_por_responsable": {k: int(v) for k, v in horas_resp.items()},
        "suficiencia": {c: int((d[f"{c}_suficiencia"] == "Cumple").sum()) for c in ["PM2.5", "PM10", "O3", "CO"]},
    }
    # Días más desfavorables: peor categoría, luego posición en banda del responsable
    dd = d[d.Cat_global != N.SIN_DATOS].copy()
    dd["orden"] = dd.Cat_global.map(N.ORDEN)
    dd["pos"] = [N.posicion_en_banda(r[f"{r.Responsable}_indicador"], r.Responsable) for _, r in dd.iterrows()]
    peores = dd.sort_values(["orden", "pos"], ascending=False).head(5)
    numeralia["dias_mas_desfavorables"] = [
        {"fecha": r.FECHA.strftime("%Y-%m-%d"), "categoria": r.Cat_global, "responsable": r.Responsable,
         "indicador": _limpio(r[f"{r.Responsable}_indicador"]), "unidad": N.UNIDADES[r.Responsable],
         "horas_mala_o_peor": int(r["horas_Mala"] + r["horas_Muy Mala"] + r["horas_Extremadamente Mala"])}
        for _, r in peores.iterrows()
    ]
    # Máximos del periodo: cuándo ocurrieron y qué categoría horaria tenía esa hora
    def extremo(col, fn="max", pol=None):
        serie = h[col].dropna()
        if serie.empty:
            return None
        ts = serie.idxmax() if fn == "max" else serie.idxmin()
        empates = serie.index[serie == serie[ts]]  # todas las horas que alcanzan el mismo valor
        return {"variable": col, "tipo": fn, "valor": _limpio(serie[ts]), "fecha_hora": ts.strftime("%Y-%m-%d %H:%M"),
                "otras_horas": [t.strftime("%Y-%m-%d %H:%M") for t in empates if t != ts],
                "categoria": h.at[ts, f"Cat_{pol}"] if pol else None, "cat_global": h.at[ts, "Cat_global"]}
    numeralia["maximos"] = [m for m in [
        extremo("PM10", pol=None), extremo("PM10_NowCast", pol="PM10"),
        extremo("PM2.5", pol=None), extremo("PM2.5_NowCast", pol="PM2.5"),
        extremo("O3", pol="O3"), extremo("CO_8h", pol="CO"),
        extremo("ET"), extremo("ET", "min"), extremo("WS"),
    ] if m]
    # Pérdida de información horario -> diario
    comp = d[d.Cat_global != N.SIN_DATOS]
    numeralia["horario_vs_diario"] = {
        "dias_con_horas_peores": int((comp.horas_peores_que_diaria > 0).sum()),
        "horas_peores_total": int(comp.horas_peores_que_diaria.sum()),
        "dias_peor_horaria_distinta": int((comp.peor_horaria != comp.Cat_global).sum()),
        "dias_responsable_distinto": int((comp.responsable_horario_frecuente != comp.Responsable).sum()),
        "cambios_categoria_total": int(h.Cambio_categoria.sum()),
    }
    # Perfil diurno medio (para interpretación)
    diurno = h.groupby("HORA")[["O3", "CO", "PM10", "PM2.5", "ET", "WS", "PM10_NowCast", "PM2.5_NowCast"]].mean().round(3)
    cat_hora = (h[h.Cat_global != N.SIN_DATOS].groupby("HORA")["Cat_global"]
                .value_counts().unstack(fill_value=0).reindex(columns=N.CATEGORIAS, fill_value=0))
    datos = {
        "periodo": {"clave": PERIODO, "nombre": nombre_periodo(), "inicio": INICIO, "fin": FIN,
                    "calentamiento": CALENTAMIENTO},
        "estacion": {"clave": "MIR", "nombre": "Miravalle", "lat": 20.614511, "lon": -103.343352, "altitud": 1622,
                     "direccion": "Av. Gobernador Curiel, esq. J. Salomé Piña, Col. Miravalle, Guadalajara",
                     "contaminantes": ["O3", "CO", "PM10", "PM2.5"],
                     "meteorologia": ["ET", "IT", "RH", "WS", "WD", "ATM"]},
        "bandas": N.BANDAS, "unidades": N.UNIDADES, "categorias": N.CATEGORIAS, "riesgo": N.RIESGO,
        "indicador_horario": N.INDICADOR_HORARIO, "indicador_diario": N.INDICADOR_DIARIO,
        "mensajes": MENSAJES,
        "descripcion_riesgo": DESCRIPCION_RIESGO,
        "perfil": perfil,
        "bitacora": bitacora.to_dict("records"),
        "horario": horario,
        "diario": diario,
        "numeralia": numeralia,
        "periodo_simulacion": periodo,
        "perfil_diurno": {c: [_limpio(x) for x in diurno[c]] for c in diurno.columns},
        "categorias_por_hora": {c: cat_hora[c].astype(int).tolist() for c in N.CATEGORIAS},
        "metodologia": metodologia().to_dict("records"),
    }
    (WEB / f"{PERIODO}.json").write_text(json.dumps(datos, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    indice_p = WEB / "index.json"
    indice = json.loads(indice_p.read_text(encoding="utf-8")) if indice_p.exists() else []
    indice = [x for x in indice if x["periodo"] != PERIODO] + [{
        "periodo": PERIODO, "nombre": nombre_periodo(), "inicio": INICIO, "fin": FIN,
        "dias_con_categoria": numeralia["dias_con_categoria"],
        "categoria_predominante": max(numeralia["dias_por_categoria"], key=numeralia["dias_por_categoria"].get),
    }]
    indice_p.write_text(json.dumps(sorted(indice, key=lambda x: x["periodo"]), ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--periodo", default="2024-03", help="Mes a procesar, formato AAAA-MM")
    ap.add_argument("--bd", type=Path, help="Ruta a la base anual (por defecto BD_<AÑO>.xlsx en la raíz)")
    args = ap.parse_args()
    configurar(args.periodo)

    # 1. ETL: si hay base anual se regenera el año limpio; si no, se usa el ya versionado
    anio = int(PERIODO[:4])
    bd = args.bd or etl.ruta_bd(anio)
    if bd.exists():
        etl.ejecutar(bd, anio)
    else:
        print(f"No se encontró {bd.name}; se usa {etl.ruta_limpio_anual(anio).relative_to(RAIZ)} tal como está.")
    etl.exportar_periodo(PERIODO)

    # 2. Cálculos NOM-172: Archivo1 (horario) y Archivo2 (diario)
    limpio, bitacora, perfil = calculos.ejecutar(PERIODO)
    perfil["formato"] = [
        "En BD_2024.xlsx la columna PM2.5 es de tipo objeto: mezcla enteros y decimales y contiene al menos un valor "
        "guardado como texto (CEN, 2024-01-07 14:00). Se convierte a numérico con errors='coerce'.",
        "El encabezado 'MES ' trae un espacio al final; DIA y MES son fórmulas de Excel (=DAY(B2), =MONTH(B2)). "
        "Se recalculan desde DATE.",
        ("La columna HOUR va de 0 a 23 y coincide con la hora de DATE en todos los registros del periodo."
         if perfil["hora_consistente"] else "La columna HOUR no coincide con la hora de DATE en algunos registros; se usa DATE."),
        "Resolución de medición: ET, IT y ATM en enteros; WS con paso de 0.1 m/s; PM en enteros.",
    ]

    # 3. Sitio: el JSON se arma a partir de Archivo1 y Archivo2
    h = leer_horario(limpio)
    d = leer_diario(h)
    periodo = seleccionar_periodo(h)
    bit = pd.DataFrame(bitacora)
    exportar_excel(h, d, bit, perfil)
    exportar_json(h, d, bit, perfil, periodo)
    reporte.generar(PERIODO)  # reporte de resultados en texto para el documento en Word
    DESC.mkdir(parents=True, exist_ok=True)
    for f in [reporte.ruta_reporte(PERIODO).name, f"MIR_{PERIODO}_horario.xlsx", f"MIR_{PERIODO}_diario.xlsx", "bitacora_limpieza.csv",
              etl.ruta_limpio_periodo(PERIODO).name, calculos.ruta_archivo1(PERIODO).name, calculos.ruta_archivo2(PERIODO).name]:
        shutil.copy2(OUT / f, DESC / f)

    print(f"Periodo {PERIODO} | horas: {len(h)} | con categoría: {(h.Cat_global != N.SIN_DATOS).sum()}")
    print("Días por categoría:", d.Cat_global.value_counts().to_dict())
    print("Responsable diario:", d.Responsable.value_counts().to_dict())
    print("Periodo de simulación:", periodo["inicio"], "→", periodo["fin"], f"({periodo['cambios']} cambios)")
    print("Bitácora:", bit.clasificacion.value_counts().to_dict())
    print(f"Reporte en texto para Word: {reporte.ruta_reporte(PERIODO).relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
