"""
Pipeline reproducible NOM-172-SEMARNAT-2023 — estación Miravalle (MIR).

Cada sprint procesa un periodo mensual con el mismo código:

    python pipeline/procesar.py --periodo 2024-03          # Sprint 1
    python pipeline/procesar.py --periodo 2024-04          # otro mes
    python pipeline/procesar.py --bd BD_2024.xlsx          # re-extrae MIR desde la base anual

Salidas por periodo (AAAA-MM):
    data/processed/<periodo>/MIR_<periodo>_horario.xlsx
    data/processed/<periodo>/MIR_<periodo>_diario.xlsx
    data/processed/<periodo>/bitacora_limpieza.csv
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

import limpieza as L
import nom172 as N

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw" / "MIR_2024.csv"
ESTACION = "MIR"
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
    ini = pd.Timestamp(periodo + "-01")
    fin = ini + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=23)
    PERIODO = periodo
    INICIO, FIN = ini.strftime("%Y-%m-%d %H:%M"), fin.strftime("%Y-%m-%d %H:%M")
    CALENTAMIENTO = (ini - pd.Timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")  # NowCast 12 h y CO 8 h
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


MENSAJES = {
    "Buena": {
        "general": "La calidad del aire es buena. Se pueden realizar actividades al aire libre con normalidad.",
        "sensibles": "Sin restricciones.",
    },
    "Aceptable": {
        "general": "Calidad del aire aceptable. Las actividades al aire libre pueden continuar.",
        "sensibles": "Consideren reducir la actividad física intensa al aire libre.",
    },
    "Mala": {
        "general": "Calidad del aire mala. Reduzcan la actividad física intensa al aire libre.",
        "sensibles": "Eviten la actividad física al aire libre y trasladen las actividades a interiores.",
    },
    "Muy Mala": {
        "general": "Calidad del aire muy mala. Eviten la actividad física al aire libre.",
        "sensibles": "Permanezcan en interiores.",
    },
    "Extremadamente Mala": {
        "general": "Calidad del aire extremadamente mala. Permanezcan en interiores.",
        "sensibles": "Permanezcan en interiores y sigan indicaciones de las autoridades.",
    },
    "Sin datos": {
        "general": "Sin información suficiente para estimar la calidad del aire en esta hora.",
        "sensibles": "",
    },
}


def extraer_de_bd(bd: Path) -> None:
    """Extrae todo el año de la estación (así cada sprint solo cambia --periodo)."""
    df = pd.read_excel(bd, sheet_name="Data")
    df.columns = [c.strip() for c in df.columns]
    m = df[df.STATION == ESTACION].copy()
    m["DIA"], m["MES"] = m.DATE.dt.day, m.DATE.dt.month
    m["PM2.5"] = pd.to_numeric(m["PM2.5"], errors="coerce")
    RAW.parent.mkdir(parents=True, exist_ok=True)
    m.to_csv(RAW, index=False)


def calcular_horario(df: pd.DataFrame) -> pd.DataFrame:
    df = df.set_index("DATE").sort_index()
    rejilla = pd.date_range(CALENTAMIENTO, FIN, freq="h")
    df = df.reindex(rejilla)
    df.index.name = "FECHA_HORA"
    df["REGISTRO_EN_FUENTE"] = np.where(df["STATION"].notna(), "Sí", "No")
    df["STATION"] = ESTACION

    co = N.co_movil_8h(df["CO"])
    df["CO_datos_8h"], df["CO_8h"] = co["n8"], co["CO_8h"]
    for pm, flag in [("PM10", 0), ("PM2.5", 1)]:
        nc = N.nowcast_serie(df[pm], flag)
        df[f"{pm}_datos_12h"] = nc["n12"]
        df[f"{pm}_datos_3h"] = nc["n3"]
        df[f"{pm}_W"] = nc["W"]
        df[f"{pm}_NowCast"] = pd.to_numeric(nc["NowCast"])

    ind = {"O3": "O3", "CO": "CO_8h", "PM10": "PM10_NowCast", "PM2.5": "PM2.5_NowCast"}
    for c, col in ind.items():
        df[f"Cat_{c}"] = [N.categoria(v, c) for v in df[col]]

    glob, resp = [], []
    for _, r in df.iterrows():
        cats = {c: r[f"Cat_{c}"] for c in ind}
        vals = {c: r[col] for c, col in ind.items()}
        g, p = N.peor_categoria(cats, vals)
        glob.append(g)
        resp.append(p)
    df["Cat_global"], df["Responsable"] = glob, resp
    df["Riesgo"] = df["Cat_global"].map(N.RIESGO).fillna("")

    df = df.loc[INICIO:FIN].copy()
    prev = df["Cat_global"].shift()
    df["Cambio_categoria"] = (df["Cat_global"] != prev) & prev.notna()
    df.loc[df.index[0], "Cambio_categoria"] = False
    df["Mensaje"] = df["Cat_global"].map(lambda c: MENSAJES[c]["general"])
    df["Sector_viento"] = df["WD"].map(L.sector_viento)
    df["FECHA"] = df.index.normalize()
    df["HORA"] = df.index.hour
    return df


def calcular_diario(h: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for fecha, d in h.groupby("FECHA"):
        fila = {"FECHA": fecha, "ESTACION": ESTACION, "dia_semana": DIAS[fecha.weekday()]}
        cats, vals = {}, {}
        for c in ["PM2.5", "PM10", "O3", "CO"]:
            n = int(d[c].notna().sum())
            cumple = n >= N.SUFICIENCIA_DIARIA
            valor = np.nan
            if cumple:
                if c in ("PM10", "PM2.5"):
                    valor = round(float(d[c].mean()), 0)
                elif c == "O3":
                    valor = round(float(d[c].max()), 3)
                elif c == "CO":
                    valor = round(float(d["CO_8h"].max()), 2) if d["CO_8h"].notna().any() else np.nan
            cat = N.categoria(valor, c)
            fila.update({f"{c}_validos": n, f"{c}_suficiencia": "Cumple" if cumple else "No cumple",
                         f"{c}_indicador": valor, f"{c}_categoria": cat})
            cats[c], vals[c] = cat, valor
        g, p = N.peor_categoria(cats, vals)
        fila["Cat_global"], fila["Responsable"] = g, p
        # Perspectiva horaria dentro del día
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
        ("Fuente", "SEMADET Jalisco, BD_2024.xlsx (hoja Data), estación Miravalle (MIR). Unidades de la hoja Param."),
        ("Norma", "NOM-172-SEMARNAT-2023. Criterios validados en Actividades 5 y 6 (SFE, enero 2025)."),
        ("Periodo", f"{INICIO[:10]} a {FIN[:10]}, horas 0–23 (hora local). Las 24 h previas ({CALENTAMIENTO[:10]}) solo calientan las ventanas."),
        ("O3", "Indicador horario = concentración horaria (ppm, 3 decimales). Diario = máximo horario."),
        ("CO", "Promedio móvil 8 h (hora actual + 7 previas), ≥ 6 de 8 datos, 2 decimales (half-up). Diario = máximo del promedio 8 h."),
        ("PM10 / PM2.5", "NowCast 12 h con la función de referencia de la profesora (≥ 2 de las 3 horas recientes; W ≥ 0.5; "
                         "factor 0.714 PM10 / 0.694 PM2.5). Diario = promedio 24 h redondeado a entero."),
        ("Bandas", "O3: 0.058/0.090/0.135/0.175 ppm · CO: 5/9/12/16 ppm · PM10: 45/60/132/213 µg/m³ · PM2.5: 15/33/79/130 µg/m³."),
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
    ap.add_argument("--bd", type=Path, help="Ruta a BD_2024.xlsx para re-extraer la estación")
    args = ap.parse_args()
    configurar(args.periodo)
    if args.bd:
        extraer_de_bd(args.bd)

    crudo = L.cargar(RAW)
    crudo = crudo[(crudo.DATE >= CALENTAMIENTO) & (crudo.DATE <= FIN)].copy()
    perfil = L.perfil(crudo, INICIO, FIN)
    perfil["formato"] = [
        "En BD_2024.xlsx la columna PM2.5 es de tipo objeto: mezcla enteros y decimales y contiene al menos un valor "
        "guardado como texto (CEN, 2024-01-07 14:00). Se convierte a numérico con errors='coerce'.",
        "El encabezado 'MES ' trae un espacio al final; DIA y MES son fórmulas de Excel (=DAY(B2), =MONTH(B2)). "
        "Se recalculan desde DATE.",
        ("La columna HOUR va de 0 a 23 y coincide con la hora de DATE en todos los registros del periodo."
         if perfil["hora_consistente"] else "La columna HOUR no coincide con la hora de DATE en algunos registros; se usa DATE."),
        "Resolución de medición: ET, IT y ATM en enteros; WS con paso de 0.1 m/s; PM en enteros.",
    ]
    limpio, bitacora = L.control_calidad(crudo, INICIO, FIN)
    h = calcular_horario(limpio)
    d = calcular_diario(h)
    periodo = seleccionar_periodo(h)
    bit = pd.DataFrame(bitacora)
    exportar_excel(h, d, bit, perfil)
    exportar_json(h, d, bit, perfil, periodo)
    DESC.mkdir(parents=True, exist_ok=True)
    for f in [f"MIR_{PERIODO}_horario.xlsx", f"MIR_{PERIODO}_diario.xlsx", "bitacora_limpieza.csv"]:
        shutil.copy2(OUT / f, DESC / f)

    print(f"Periodo {PERIODO} | horas: {len(h)} | con categoría: {(h.Cat_global != N.SIN_DATOS).sum()}")
    print("Días por categoría:", d.Cat_global.value_counts().to_dict())
    print("Responsable diario:", d.Responsable.value_counts().to_dict())
    print("Periodo de simulación:", periodo["inicio"], "→", periodo["fin"], f"({periodo['cambios']} cambios)")
    print("Bitácora:", bit.clasificacion.value_counts().to_dict())


if __name__ == "__main__":
    main()
