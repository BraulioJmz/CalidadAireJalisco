"""Análisis retrospectivo MIR 2023/2024. Ver docs/sprints/sprint-2/REPRODUCIR.md.

Adaptado del prototipo suministrado; Sprint 1 y las salidas web quedan intactos.
Usa extractos locales verificables o regenera desde Excel de solo lectura.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import normativa as N

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/source/sprint-2"
OUT = ROOT / "data/processed/sprint-2"
METEO = ["ET", "RH", "WS", "WD", "IT", "ATM", "PP", "RS", "UVI"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
METRICS = N.CORE + ["GLOBAL", "NO2", "SO2"]
LOG_COLUMNS = ["fecha_hora", "variable", "valor_original", "regla", "accion", "justificacion", "fuente", "fila_excel"]

def source_info(raw, ts):
    return {"fuente": str(raw.at[ts, "SOURCE_FILE"]) if "SOURCE_FILE" in raw else "extracto local MIR",
            "fila_excel": raw.at[ts, "SOURCE_EXCEL_ROW"] if "SOURCE_EXCEL_ROW" in raw else None}

def native(v):
    if isinstance(v, dict): return {str(k): native(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)): return [native(x) for x in v]
    if isinstance(v, (pd.Timestamp, np.datetime64)): return str(pd.Timestamp(v))[:19]
    if isinstance(v, (np.integer,)): return int(v)
    if isinstance(v, (float, np.floating)): return float(v) if np.isfinite(v) else None
    if isinstance(v, np.bool_): return bool(v)
    return v

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(native(data), ensure_ascii=False, allow_nan=False, separators=(",", ":")), encoding="utf-8")

def normalize(df, year):
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    if df.columns.duplicated().any(): raise ValueError("Encabezados duplicados tras normalización")
    for c in ["STATION", "DATE"]:
        if c not in df: raise ValueError(f"Falta columna obligatoria {c}")
    df = df[df.STATION.astype(str).str.strip().str.upper().eq("MIR")].copy()
    if df.empty: raise ValueError(f"MIR sin datos de {year}")
    df["DATE"] = pd.to_datetime(df.DATE, errors="raise")
    if df.DATE.isna().any(): raise ValueError("DATE faltante")
    if df.DATE.dt.tz is not None: raise ValueError("DATE debe ser hora local sin zona según fuente")
    if not df.DATE.dt.year.eq(year).all(): raise ValueError(f"MIR contiene fechas fuera de {year}")
    if df.DATE.duplicated().any(): raise ValueError("Fechas duplicadas: resolver con evidencia antes de calcular")
    if not df.DATE.eq(df.DATE.dt.floor("h")).all(): raise ValueError("Fechas no alineadas a una hora")
    for col, expected in [("HOUR", df.DATE.dt.hour), ("DIA", df.DATE.dt.day), ("MES", df.DATE.dt.month)]:
        if col in df:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if not numeric.eq(expected).all(): raise ValueError(f"{col} no coincide con DATE")
    logs = []
    for p in N.POLS + METEO:
        if p not in df:
            df[p] = np.nan
            continue
        original = df[p].where(~df[p].astype(str).str.strip().eq(""))
        df[p] = pd.to_numeric(original, errors="coerce")
        for i in df.index[original.notna() & df[p].isna()]:
            logs.append({"fecha_hora": str(df.at[i, "DATE"]), "variable": p,
                         "valor_original": original.at[i], "regla": "Conversión no numérica",
                         "accion": "Excluir de indicadores", "justificacion": "Texto no convertible; original preservado en extracto y Excel",
                         "fuente": df.at[i, "SOURCE_FILE"] if "SOURCE_FILE" in df else "extracto local MIR",
                         "fila_excel": df.at[i, "SOURCE_EXCEL_ROW"] if "SOURCE_EXCEL_ROW" in df else None})
    df = df.set_index("DATE").sort_index()
    if "SOURCE_ROW" in df:
        tokens = df.SOURCE_ROW.astype(str).str.strip().str.lower()
        if not tokens.isin(["true", "false", "1", "0", "1.0", "0.0"]).all():
            raise ValueError("SOURCE_ROW contiene una bandera desconocida")
        df["SOURCE_ROW"] = tokens.isin(["true", "1", "1.0"])
    else:
        df["SOURCE_ROW"] = True
    df = df.reindex(pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h"))
    df.index.name = "DATE"
    df["SOURCE_ROW"] = df.SOURCE_ROW.eq(True)
    df["STATION"] = "MIR"
    df["HOUR"], df["DIA"], df["MES"] = df.index.hour, df.index.day, df.index.month
    provenance = [c for c in ["SOURCE_FILE", "SOURCE_EXCEL_ROW"] if c in df]
    out = df[["STATION", "HOUR", "DIA", "MES", "SOURCE_ROW"] + provenance + N.POLS + METEO]
    out.attrs["ingestion_log"] = logs
    out.attrs["source_columns"] = list(df.columns)
    return out

def source_extract(path, year):
    df = pd.read_excel(path, sheet_name="Data", keep_default_na=False)
    df.columns = [str(c).strip().upper() for c in df.columns]
    if df.columns.duplicated().any(): raise ValueError("Encabezados duplicados")
    df["SOURCE_EXCEL_ROW"] = np.arange(len(df)) + 2
    df["SOURCE_FILE"] = f"BD_{year}.xlsx:Data"
    df = df.loc[df.STATION.astype(str).str.strip().str.upper().eq("MIR")].copy()
    # Validar antes de escribir. El extracto conserva textos y mediciones originales.
    raw = normalize(df, year)
    SOURCE.mkdir(parents=True, exist_ok=True)
    df.to_csv(SOURCE / f"MIR_{year}.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    return raw

def load_sources(paths):
    frames = []
    logs = []
    manifest_path = ROOT / "config/fuentes_sprint2.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for year in [2023, 2024]:
        p = paths.get(year)
        if p:
            expected = next((r["sha256"] for r in manifest.get("fuentes", []) if r["archivo"] == f"02_fuentes/BD_{year}.xlsx"), None)
            if expected and hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise ValueError(f"SHA-256 inesperado en BD_{year}.xlsx")
            raw = source_extract(p, year)
        else:
            f = SOURCE / f"MIR_{year}.csv"
            if not f.exists(): raise FileNotFoundError(f"Falta {f}. Use --bd-{year} con la fuente original")
            expected = manifest.get("extractos", {}).get(str(year), {}).get("sha256")
            if expected and hashlib.sha256(f.read_bytes()).hexdigest() != expected:
                raise ValueError(f"SHA-256 inesperado en extracto {year}")
            raw = normalize(pd.read_csv(f, keep_default_na=False), year)
        logs.extend(raw.attrs.pop("ingestion_log", []))
        raw.attrs.clear()
        frames.append(raw)
    out = pd.concat(frames).sort_index()
    out.attrs["ingestion_log"] = logs
    return out

def prepare(raw):
    clean = raw.copy()
    logs = list(raw.attrs.get("ingestion_log", []))
    def flag(ts, p, rule, action, detail):
        logs.append({"fecha_hora": str(ts), "variable": p, "valor_original": raw.at[ts,p], "regla": rule, "accion": action, "justificacion": detail, **source_info(raw, ts)})
    # Exclusión documentada por la autoridad, no por un umbral estadístico.
    inv = (clean.index.year == 2023) & clean.SO2.notna()
    for t in clean.index[inv]: flag(t, "SO2", "Invalidación oficial", "Excluir de indicadores", "INECC, Informe Nacional 2023, p. 222: datos SO2 invalidados por falta de calibración")
    clean.loc[clean.index.year == 2023, "SO2"] = np.nan
    for p in N.POLS:
        for t in clean.index[clean[p].notna() & ((clean[p] < 0) | ~np.isfinite(clean[p]))]:
            flag(t, p, "Valor no utilizable", "Excluir de indicadores", "Concentración negativa o no finita; fuente original preservada")
            clean.at[t,p] = np.nan
    for p in METEO:
        for t in clean.index[clean[p].notna() & ~np.isfinite(clean[p])]:
            flag(t, p, "Meteorología no finita", "Excluir de análisis meteorológico", "No admite promedios finitos")
            clean.at[t, p] = np.nan
    for p, bad in {"RH": ~clean.RH.between(0,100), "WS": clean.WS.lt(0), "WD": ~clean.WD.between(0,360)}.items():
        for t in clean.index[clean[p].notna() & bad]:
            flag(t,p,"Rango de variable", "Excluir de análisis meteorológico", "RH 0–100 %, WS no negativa, WD 0–360 grados")
            clean.at[t,p] = np.nan
    for t in clean.index[clean['PM2.5'].gt(clean.PM10)]:
        flag(t,"PM2.5","PM2.5 > PM10","Conservar y revisar","La inconsistencia requiere revisión instrumental; no se recorta ni elimina automáticamente")
    # Diagnóstico robusto por mismo año, mes y hora: no confundir estacionalidad con anomalía.
    floors = {"PM10":10,"PM2.5":5,"O3":.005,"CO":.1,"NO2":.005}
    keys = [clean.index.year, clean.index.month, clean.index.hour]
    for p,floor in floors.items():
        med = clean[p].groupby(keys).transform("median")
        dev = (clean[p]-med).abs()
        mad = dev.groupby(keys).transform("median")
        z = (clean[p]-med) / np.maximum(1.4826*mad, floor)
        for t in clean.index[z.abs().gt(3.5)]:
            flag(t,p,"Atípico robusto |z| > 3.5", "Conservar y revisar", f"Referencia misma hora, mes y año; z={z.at[t]:.2f}; no demuestra incendio ni falla")
    log = pd.DataFrame(logs, columns=LOG_COLUMNS)
    clean.attrs.clear()
    return clean, log

def calculate(clean):
    ind = N.indicators(clean)
    # No conocemos el día previo a 2023. Exclusión conservadora del arranque,
    # adicional a la suficiencia de la NOM; 2024 utiliza diciembre de 2023.
    for p in ["PM10","PM2.5"]: ind.loc[:"2023-01-01 10:00",p] = np.nan
    ind.loc[:"2023-01-01 06:00","CO"] = np.nan
    cats = pd.DataFrame({p:ind[p].map(lambda x:N.category(x,p)) for p in N.POLS})
    hourly = clean.copy()
    hourly["BASE_CO_8H"] = N.co_base(clean.CO)
    hourly.loc[:"2023-01-01 06:00", "BASE_CO_8H"] = np.nan
    hourly["N8_CO"] = clean.CO.rolling(8, min_periods=1).count().astype(int)
    for p in ["PM10", "PM2.5"]:
        hourly[f"N12_{p}"] = clean[p].rolling(12, min_periods=1).count().astype(int)
        hourly[f"N3_{p}"] = clean[p].rolling(3, min_periods=1).count().astype(int)
    for p in N.POLS + METEO:
        hourly[f"ESTADO_{p}"] = np.select(
            [~clean.SOURCE_ROW, clean[p].isna()], ["fila_ausente", "sin_medicion_utilizable"], default="utilizable")
    for p in N.POLS:
        hourly[f"I_{p}"] = ind[p]
        hourly[f"C_{p}"] = cats[p]
    hourly["I_GLOBAL"] = cats[N.CORE].max(axis=1).where(cats[N.CORE].notna().all(axis=1))
    hourly["C_GLOBAL"] = hourly.I_GLOBAL
    hourly["C_DISPONIBLE"] = cats.max(axis=1)
    hourly["N_CONTAMINANTES"] = cats.notna().sum(axis=1)
    hourly["N_CORE"] = cats[N.CORE].notna().sum(axis=1)
    hourly["GLOBAL_PARCIAL"] = hourly.N_CONTAMINANTES.lt(len(N.POLS))
    hourly["CORE_PARCIAL"] = hourly.N_CORE.lt(len(N.CORE))
    hourly["DETERMINANTES"] = cats.apply(lambda r: ";".join(p for p in N.POLS if pd.notna(r[p]) and r[p] == r.max()), axis=1)
    hourly["DETERMINANTES_GLOBAL"] = cats[N.CORE].apply(lambda r: ";".join(p for p in N.CORE if r[p] == r.max()) if r.notna().all() else "", axis=1)
    rows=[]
    for day,g in hourly.groupby(hourly.index.normalize()):
        r={"DATE":day, "YEAR":day.year,"MONTH":day.month,"DAY":day.day,
           "N_FILAS_FUENTE": int(g.SOURCE_ROW.sum()), "HORAS_ESPERADAS": 24}
        for p in N.POLS:
            n=int(g[p].notna().sum())
            v=np.nan
            if n>=18:
                v=N.mean_decimal(g[p]) if p.startswith("PM") else g["BASE_CO_8H"].max() if p == "CO" else g[p].max()
            r[f"N_{p}"]=n
            r[f"N_IND_{p}"] = int(g[f"I_{p}"].notna().sum())
            r[f"EXACT_{p}"]=v
            r[f"I_{p}"]=N.half_up(v,N.DEC[p])
            r[f"C_{p}"]=N.category(r[f"I_{p}"],p)
        for p in METEO:
            n=int(g[p].notna().sum())
            if p=="WD":
                # Estadístico circular; no se promedia 359° y 1° como 180°.
                pair=g[["WD","WS"]].dropna();pair=pair[pair.WS.gt(0)]
                angle=np.deg2rad(pair.WD)
                u,v=(np.sin(angle)*pair.WS).sum(),(np.cos(angle)*pair.WS).sum()
                resultant = np.hypot(u,v) / pair.WS.sum() if len(pair) else 0
                value=float(np.degrees(np.arctan2(u,v))%360) if len(pair)>=18 and resultant>1e-9 else np.nan
                r["N_PARES_WD_WS"] = len(pair)
                r["RESULTANTE_WD"] = resultant if len(pair) else np.nan
            else:value=g[p].mean() if n>=18 else np.nan
            r[f"M_{p}"]=value;r[f"N_{p}"]=n
        valid=[p for p in N.POLS if pd.notna(r[f"C_{p}"])]
        coreok=all(pd.notna(r[f"C_{p}"]) for p in N.CORE)
        r["C_GLOBAL"]=max(r[f"C_{p}"] for p in N.CORE) if coreok else np.nan
        r["I_GLOBAL"]=r["C_GLOBAL"];r["EXACT_GLOBAL"]=np.nan
        r["C_DISPONIBLE"]=max((r[f"C_{p}"] for p in valid),default=np.nan)
        r["N_CONTAMINANTES"]=len(valid)
        r["N_CORE"]=sum(pd.notna(r[f"C_{p}"]) for p in N.CORE)
        r["GLOBAL_PARCIAL"]=len(valid) < len(N.POLS)
        r["CORE_PARCIAL"]=not coreok
        r["DETERMINANTES"]=";".join(p for p in valid if r[f"C_{p}"]==r["C_DISPONIBLE"])
        r["DETERMINANTES_GLOBAL"]=";".join(p for p in N.CORE if r[f"C_{p}"]==r["C_GLOBAL"]) if coreok else ""
        rows.append(r)
    return hourly,pd.DataFrame(rows).set_index("DATE")

def distribution(s, expected):
    counts=[int(s.eq(i).sum()) for i in range(5)]
    n=int(s.notna().sum())
    return {"counts":counts,"valid":n,"missing":expected-n,"expected":expected,
            "bad":sum(counts[2:]),"bad_pct":100*sum(counts[2:])/n if n else None}

def describe(s):
    """Solo magnitudes continuas; nunca recibe códigos de categorías."""
    if not s.notna().any():
        return {"n":0, **{k:None for k in ["mean","median","std","q05","q25","q75","q95","min","max"]}, "dates_max":[]}
    return {"n":int(s.count()), "mean":s.mean(), "median":s.median(), "std":s.std(ddof=1),
            "q05":s.quantile(.05), "q25":s.quantile(.25), "q75":s.quantile(.75), "q95":s.quantile(.95),
            "min":s.min(), "max":s.max(),
            "dates_max":[str(t) for t in s.index[s.eq(s.max())]] if s.notna().any() else []}

def pairs(d,p,month=0):
    a=d[d.YEAR.eq(2023)];b=d[d.YEAR.eq(2024)]
    if month: a=a[a.MONTH.eq(month)];b=b[b.MONTH.eq(month)]
    # Mismo mes/día, nunca se alinean por ordinal (2024 tiene 29 de febrero).
    a=a.set_index(["MONTH","DAY"]);b=b.set_index(["MONTH","DAY"])
    col=f"I_{p}" if p=="GLOBAL" else f"EXACT_{p}"
    z=pd.concat([a[col].rename("a"),b[col].rename("b")],axis=1,join="inner").dropna()
    expected=365 if not month else len(a)
    # La comparación anual requiere también representación en cada trimestre.
    quarterly=[]
    quarterly_n=[]
    if not month:
        for q in range(4):
            eligible=sum(1 for m,day in a.index if 3*q+1<=m<=3*q+3)
            observed=sum(1 for m,day in z.index if 3*q+1<=m<=3*q+3)
            quarterly.append(100*observed/eligible if eligible else 0)
            quarterly_n.append({"quarter":q+1,"n":observed,"expected":eligible})
    comparable=len(z)>=math.ceil(.75*expected) and (month>0 or min(quarterly,default=0)>=75)
    avg_a=float(z.a.mean()) if len(z) else None;avg_b=float(z.b.mean()) if len(z) else None
    if p=="GLOBAL":
        avg_a=100*float(z.a.ge(2).mean()) if len(z) else None
        avg_b=100*float(z.b.ge(2).mean()) if len(z) else None
    delta=avg_b-avg_a if len(z) else None
    return {"month":month,"n":len(z),"expected":expected,"coverage":100*len(z)/expected,
            "comparable":comparable,"a":avg_a,"b":avg_b,"delta":delta,
            "change_pct":100*delta/avg_a if avg_a not in (0,None) and p!="GLOBAL" else None,
            "quarterly_coverage":quarterly,"quarterly_n":quarterly_n,
            "metric":"porcentaje de días Mala o peor; delta en puntos porcentuales" if p=="GLOBAL" else "media de indicadores diarios antes del redondeo final",
            "interpretation":"Comparable en días coincidentes; persisten sesgos" if comparable else "Solo descriptivo; cobertura insuficiente para destacar cambio",
            "dates":[f"{m:02d}-{day:02d}" for m,day in z.index]}

def summarize(raw,clean,h,d,log):
    months=[];annual=[];profiles=[];coverage=[];dominance=[];meteo=[];events=[];statistics=[]
    for year in [2023,2024]:
        yr=d[d.YEAR.eq(year)];hr=h[h.index.year==year]
        for p in N.POLS+METEO:
            for month in range(13):
                rr=raw[(raw.index.year==year)&(raw.index.month==month)]
                cc=clean[(clean.index.year==year)&(clean.index.month==month)]
                if month == 0:
                    rr=raw[raw.index.year==year]; cc=clean[clean.index.year==year]
                exclusions = log[(pd.to_datetime(log.fecha_hora).dt.year == year) & log.variable.eq(p) & log.accion.str.startswith("Excluir")]
                if month: exclusions=exclusions[pd.to_datetime(exclusions.fecha_hora).dt.month.eq(month)]
                coverage.append({"year":year,"month":month,"variable":p,"expected":len(rr),
                                 "raw":int(rr[p].notna().sum()),"usable":int(cc[p].notna().sum()),
                                 "source_rows":int(rr.SOURCE_ROW.sum()), "absent_rows":int((~rr.SOURCE_ROW).sum()),
                                 "excluded":len(exclusions),
                                 "missing_measurements":int((rr.SOURCE_ROW & rr[p].isna()).sum()) - int(exclusions.regla.eq("Conversión no numérica").sum()),
                                 "first_raw":str(rr[p].first_valid_index()) if rr[p].notna().any() else None,
                                 "last_raw":str(rr[p].last_valid_index()) if rr[p].notna().any() else None,
                                 "pct":100*cc[p].notna().sum()/len(rr)})
        for p in METRICS:
            s=yr[f"C_{p}"]
            val=yr[f"EXACT_{p}"]
            stats=describe(val) if p != "GLOBAL" else {}
            row={"year":year,"pollutant":p,**distribution(s,len(yr)),**stats}
            annual.append(row)
            for month in range(1,13):
                dd=yr[yr.MONTH.eq(month)];hh=hr[hr.index.month==month]
                exact=dd[f"EXACT_{p}"]
                count=int(exact.notna().sum())
                months.append({"year":year,"month":month,"pollutant":p,**distribution(dd[f"C_{p}"],len(dd)),
                               **(describe(exact) if p != "GLOBAL" else {}),
                               "sufficient":int(dd[f"C_{p}"].notna().sum())>=math.ceil(.75*len(dd))})
                for hour in range(24):
                    ss=hh.loc[hh.index.hour==hour,f"C_{p}"]
                    profiles.append({"year":year,"month":month,"hour":hour,"pollutant":p,**distribution(ss,len(dd))})
        for month in range(13):
            hh=hr if month==0 else hr[hr.index.month==month]
            dd=yr if month==0 else yr[yr.MONTH.eq(month)]
            for p in N.POLS:
                for kind, values, expected in [("concentracion_horaria",hh[p],len(hh)),
                        ("nowcast_12h" if p.startswith("PM") else "promedio_movil_8h" if p=="CO" else "base_horaria",hh[f"I_{p}"],len(hh)),
                        ("promedio_diario_24h" if p.startswith("PM") else "maximo_diario_8h" if p=="CO" else "maximo_diario_1h",dd[f"EXACT_{p}"],len(dd))]:
                    statistics.append({"year":year,"month":month,"pollutant":p,"statistic":kind,
                                       "unit":N.UNITS[p],"expected":expected, **describe(values)})
        for day,r in yr.iterrows():
            if pd.isna(r.C_GLOBAL):continue
            dom=[p for p in N.CORE if r[f"C_{p}"]==r.C_GLOBAL]
            dominance.append({"date":str(day.date()),"year":year,"month":day.month,"category":r.C_GLOBAL,"pollutants":dom})
        for p in N.CORE+["NO2"]:
            for month in range(1,13):
                dd=yr[yr.MONTH.eq(month)]
                for var in ["ET","RH","WS"]:
                    # Elimina ruido de punto flotante muy por debajo de la resolución
                    # instrumental; exporta exactamente los pares usados en los rangos.
                    z=dd[[f"EXACT_{p}",f"M_{var}"]].dropna().round(12)
                    rho=float(spearmanr(z.iloc[:,0],z.iloc[:,1]).statistic) if len(z)>=15 and z.iloc[:,0].nunique()>1 and z.iloc[:,1].nunique()>1 else None
                    meteo.append({"year":year,"month":month,"pollutant":p,"variable":var,"n":len(z),"rho":rho,
                                  "expected":len(dd),"coverage_pct":100*len(z)/len(dd),
                                  "status":"calculado_descriptivo" if rho is not None else "menos_de_15_pares" if len(z)<15 else "serie_constante",
                                  "points":[[str(ts.date()),r.iloc[1],r.iloc[0]] for ts,r in z.iterrows()]})
        # Tres máximos diarios por año y contaminante, al menos siete días separados.
        for p in N.CORE+["NO2"]:
            ranked=yr[f"I_{p}"].dropna().sort_values(ascending=False,kind="stable")
            selected=[]
            for ts,value in ranked.items():
                if any(abs((ts-t).days)<7 for t in selected):continue
                selected.append(ts)
                window=hr.loc[ts-pd.Timedelta(days=1):ts+pd.Timedelta(days=2)-pd.Timedelta(hours=1)]
                events.append({"year":year,"date":str(ts.date()),"month":ts.month,"pollutant":p,"value":value,
                               "category":yr.at[ts,f"C_{p}"],"n":int(yr.at[ts,f"N_{p}"]),
                               "hours":[[str(t)[:16],r[p],r[f"I_{p}"],r.ET,r.WS] for t,r in window.iterrows()]})
                if len(selected)==3:break
    compare={p:[pairs(d,p,m) for m in range(13)] for p in METRICS}
    daily=[]
    for ts,r in d.iterrows():
        daily.append({"date":str(ts.date()),"year":ts.year,"month":ts.month,
                      "indicators":{p:r[f"I_{p}"] for p in METRICS},
                      "categories":{p:r[f"C_{p}"] for p in METRICS},
                      "available_category":r.C_DISPONIBLE,"n_pollutants":r.N_CONTAMINANTES,
                      "determinants":r.DETERMINANTES.split(";") if r.DETERMINANTES else []})
    available=[]
    for year in [2023,2024]:
        for month in range(13):
            ss=d[d.YEAR.eq(year)]
            if month:ss=ss[ss.MONTH.eq(month)]
            available.append({"year":year,"month":month,**distribution(ss.C_DISPONIBLE,len(ss))})
    return {"version":N.VERSION,"station":"Miravalle (MIR)","agency":"Academia Miravalle","years":[2023,2024],
            "categories":N.CATS,"bands":N.BANDS,"units":N.UNITS,"labels":N.LABELS,"months":MESES,
            "annual":annual,"monthly":months,"comparisons":compare,"coverage":coverage,"profiles":profiles,
            "statistics":statistics,
            "dominance":dominance,"meteorology":meteo,"events":events,"daily":daily,"available":available,
            "quality":{"raw_hours":{str(y):int((raw.index.year==y).sum()) for y in [2023,2024]},
                       "missing_source_rows":int((~raw.SOURCE_ROW).sum()),"flags":len(log),
                       "flag_counts":log.groupby(["regla","accion"]).size().reset_index(name="n").to_dict("records")},
            "rules":{"bands_reference":"2024, aplicadas retrospectivamente a ambos años",
                     "paired":"Mismo mes y día; 29 de febrero solo en descriptivos de 2024",
                     "comparison_threshold":"75 % de días coincidentes; anual exige además 75 % en cada trimestre (criterio del proyecto)",
                     "global":"Peor categoría de PM10, PM2.5, O3 y CO, solo cuando los cuatro tienen indicador válido",
                     "daily_gases":"Se exigen 18 horas crudas para máximos diarios como criterio conservador del curso; la NOM especifica 18/24 para PM",
                     "no2":"Serie complementaria 2024; no se integra al global comparable de cuatro contaminantes",
                     "so2":"SO2 2023 excluido por invalidación oficial; 2024 sin datos",
                     "warmup":"2024 usa diciembre de 2023; se excluyen primeras 11 h PM y 7 h CO de 2023 por ausencia de 2022",
                     "meteorology":"Promedios meteorológicos diarios con 18/24 horas; Spearman con al menos 15 pares diarios, descriptivo sin p-valores",
                     "outliers":"Conservados con bandera robusta por mismo año, mes y hora; no prueban fuente de emisión"}}

def episodes(d):
    rows=[]
    for p in N.CORE+["NO2"]:
        active=d[f"C_{p}"].ge(2)
        groups=active.ne(active.shift(fill_value=False)).cumsum()
        for _,g in d[active].groupby(groups[active]):
            if len(g)<2: continue
            rows.append({"pollutant":p,"start":str(g.index[0].date()),"end":str(g.index[-1].date()),
                         "days":len(g),"max_category":int(g[f"C_{p}"].max()),
                         "max_indicator":g[f"I_{p}"].max(),"n_raw_hours":int(g[f"N_{p}"].sum()),
                         "expected_hours":24*len(g),"selection":"Al menos 2 días consecutivos Mala o peor; faltantes cortan episodio"})
    return rows

def hourly_peaks(h):
    rows=[]
    for year in [2023,2024]:
        for p in N.CORE+["NO2"]:
            ranked=h.loc[h.index.year==year,f"I_{p}"].dropna().sort_values(ascending=False,kind="stable")
            chosen=[]
            for ts,value in ranked.items():
                if any(abs(ts-t)<pd.Timedelta(hours=24) for t in chosen): continue
                chosen.append(ts)
                rows.append({"date":str(ts),"year":year,"pollutant":p,"indicator":value,
                             "category":h.at[ts,f"C_{p}"],"raw_concentration":h.at[ts,p],
                             **{v:h.at[ts,v] for v in ["ET","RH","WS","WD"]},
                             "selection":"3 máximos horarios por año/contaminante separados al menos 24 horas; empates cronológicos"})
                if len(chosen)==3: break
    return rows

def csv_table(path, rows):
    frame=pd.DataFrame(rows)
    for col in frame:
        if frame[col].map(lambda x:isinstance(x,(list,dict))).any():
            frame[col]=frame[col].map(lambda x:json.dumps(native(x),ensure_ascii=False,allow_nan=False) if isinstance(x,(list,dict)) else x)
    frame.to_csv(path,index=False)

def execute(paths=None, out=OUT):
    raw=load_sources(paths or {})
    clean,log=prepare(raw);h,d=calculate(clean)
    for p in N.POLS+METEO:
        h.loc[h[f"ESTADO_{p}"].eq("sin_medicion_utilizable"),f"ESTADO_{p}"]="medicion_faltante"
        excluded=log[log.variable.eq(p)&log.accion.str.startswith("Excluir")]
        if len(excluded): h.loc[pd.to_datetime(excluded.fecha_hora).unique(),f"ESTADO_{p}"]="exclusion_documentada"
    out.mkdir(parents=True,exist_ok=True)
    for y in [2023,2024]:
        clean[clean.index.year==y].to_csv(out/f"MIR_{y}_depurado.csv")
        h[h.index.year==y].to_csv(out/f"MIR_{y}_horario.csv")
        d[d.YEAR.eq(y)].to_csv(out/f"MIR_{y}_diario.csv")
    log.to_csv(out/"bitacora_calidad.csv",index=False)
    data=summarize(raw,clean,h,d,log)
    data["source_hashes"]={str(y):hashlib.sha256((SOURCE/f"MIR_{y}.csv").read_bytes()).hexdigest() for y in [2023,2024]}
    manifest=ROOT/"config/fuentes_sprint2.json"
    data["sources"]=json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    data["rules"]["daily_unrounded"]="EXACT: PM media de concentraciones; CO máximo de medias móviles antes de redondear; gases máximo crudo. I: redondeo final; C: categoría de I."
    data["rules"]["global_available"]="Máximo entre seis contaminantes disponibles; GLOBAL_PARCIAL si falta alguno de seis; CORE_PARCIAL si falta alguno de cuatro comunes. NO2 complementario puede afectar disponible."
    data["rules"]["wind"]="WD media circular ponderada por WS, excluye calmas; 18 pares WD/WS con WS>0; resultante normalizada >1e-9. No se correlaciona WD linealmente."
    data["rules"]["time"]="DATE se interpreta como hora civil local ya codificada en fuente, sin inferir UTC ni convertir horario de verano. Archivos contienen rejillas completas de 24 horas/día."
    data["rules"]["instrumental"]="No hay registros subhorarios, calibraciones ni bitácoras instrumentales; suficiencia y plausibilidad no prueban validación instrumental."
    data["episodes"]=episodes(d)
    data["hourly_peaks"]=hourly_peaks(h)
    write_json(out/"resumen.json",data)
    for name in ["monthly","coverage","annual","statistics","profiles","available","dominance"]:
        csv_table(out/f"{name}.csv",data[name])
    comparisons=[{"pollutant":p,**r} for p,rr in data["comparisons"].items() for r in rr]
    csv_table(out/"comparacion_pareada.csv",comparisons)
    paired_rows=[]
    for p in METRICS:
        a=d[d.YEAR.eq(2023)].set_index(["MONTH","DAY"])
        b=d[d.YEAR.eq(2024)].set_index(["MONTH","DAY"])
        col=f"I_{p}" if p=="GLOBAL" else f"EXACT_{p}"
        z=pd.concat([a[col].rename("a"),b[col].rename("b")],axis=1,join="inner").dropna()
        for (m,day),r in z.iterrows():
            paired_rows.append({"pollutant":p,"month":m,"day":day,"date_2023":f"2023-{m:02d}-{day:02d}",
                                "date_2024":f"2024-{m:02d}-{day:02d}","a":r.a,"b":r.b,
                                "delta":float(r.b>=2)-float(r.a>=2) if p=="GLOBAL" else r.b-r.a,
                                "unit":"cambio de indicador Mala o peor (0/1); no resta de categorías" if p=="GLOBAL" else N.UNITS[p]})
    csv_table(out/"pares_diarios.csv",paired_rows)
    csv_table(out/"meteorologia.csv",[{k:v for k,v in r.items() if k!="points"} for r in data["meteorology"]])
    csv_table(out/"pares_meteorologicos.csv",[{"year":r["year"],"month":r["month"],"pollutant":r["pollutant"],
        "variable":r["variable"],"date":pt[0],"meteorology":pt[1],"concentration":pt[2]} for r in data["meteorology"] for pt in r["points"]])
    csv_table(out/"episodios.csv",data["episodes"])
    csv_table(out/"horas_relevantes.csv",data["hourly_peaks"])
    csv_table(out/"dias_relevantes.csv",[{k:v for k,v in r.items() if k!="hours"} for r in data["events"]])
    csv_table(out/"contexto_dias_relevantes.csv",[{"event_date":r["date"],"pollutant":r["pollutant"],
        "datetime":pt[0],"raw_concentration":pt[1],"indicator":pt[2],"ET":pt[3],"WS":pt[4]} for r in data["events"] for pt in r["hours"]])
    write_json(out/"fuentes_hashes.json",data["sources"])
    return data

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bd-2023",type=Path);ap.add_argument("--bd-2024",type=Path)
    ap.add_argument("--out",type=Path,default=OUT)
    args=ap.parse_args()
    data=execute({2023:args.bd_2023,2024:args.bd_2024},args.out)
    print(json.dumps(native({"version":N.VERSION,"hours":sum(data['quality']['raw_hours'].values()),
                            "days":len(data['daily']),"flags":data['quality']['flags'],
                            "comparisons":{p:{k:v for k,v in data['comparisons'][p][0].items() if k!='dates'} for p in N.CORE}}),ensure_ascii=False))

if __name__=="__main__":main()
