"""
Reporte de resultados en texto (para copiar al reporte en Word).

Lee Archivo1 (horario) y Archivo2 (diario) del periodo, imprime el análisis en consola y lo guarda en
data/processed/<AAAA-MM>/reporte_resultados_<AAAA-MM>.txt. Basado en el script de análisis original del equipo.

Uso (desde la raíz):
    python pipeline/reporte.py --periodo 2024-03
También lo ejecuta procesar.py al final.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import calculos
import etl
import nom172 as N

CONTAMINANTES = ["PM10", "PM2.5", "CO", "O3"]
UNIDAD = {"PM10": "µg/m³", "PM2.5": "µg/m³", "CO": "ppm", "O3": "ppm"}
DEC = {"PM10": 2, "PM2.5": 2, "CO": 2, "O3": 3}  # decimales de las estadísticas (los indicadores ya vienen redondeados por la NOM)
ORDEN = N.CATEGORIAS + [N.SIN_DATOS]


def ruta_reporte(periodo: str) -> Path:
    return etl.PROCESSED / periodo / f"reporte_resultados_{periodo}.txt"


def dias(n: int) -> str:
    return f"{n} día" if n == 1 else f"{n} días"


def generar(periodo: str) -> str:
    d = pd.read_csv(calculos.ruta_archivo2(periodo), keep_default_na=False, na_values=[""])
    h = pd.read_csv(calculos.ruta_archivo1(periodo), keep_default_na=False, na_values=[""], parse_dates=["DATE"])
    d["Responsable_Diario"] = d["Responsable_Diario"].fillna("")
    total = len(d)
    L: list[str] = []
    p = L.append
    sec = lambda t: (p(""), p("-" * 50), p(t), p("-" * 50))

    p("=" * 65)
    p(f"ANÁLISIS DE RESULTADOS DIARIOS - ESTACIÓN MIRAVALLE ({total} DÍAS)")
    p(f"Periodo {periodo} · NOM-172-SEMARNAT-2023")
    p("=" * 65)

    sec("1. EVALUACIÓN DE SUFICIENCIA DIARIA (≥ 18 de 24 horas válidas)")
    for c in CONTAMINANTES:
        cumple = int((d[f"Suficiencia_{c}"] == "Cumple").sum())
        p(f"{c:6}: {cumple} días Cumple ({100 * cumple / total:.1f}%) | {total - cumple} días No cumple")

    sec("2. ESTADÍSTICAS DE LOS INDICADORES DIARIOS")
    for c in CONTAMINANTES:
        s = d[f"Indicador_{c}"].dropna()
        k = DEC[c]
        p("")
        p(f"Indicador diario {c} ({UNIDAD[c]}) · {N.INDICADOR_DIARIO[c].lower()}:")
        p(f"  - Días evaluados: {len(s)}")
        if len(s):
            p(f"  - Media mensual:  {s.mean():.{k}f}")
            p(f"  - Desv. estándar: {s.std():.{k}f}")
            p(f"  - Mínimo:         {s.min():.{k}f}")
            p(f"  - Mediana (Q2):   {s.median():.{k}f}")
            p(f"  - Máximo:         {s.max():.{k}f}")

    sec("3. CATEGORÍAS DIARIAS POR CONTAMINANTE")
    for c in CONTAMINANTES:
        p("")
        p(f"Distribución para {c}:")
        conteo = d[f"Cat_{c}"].value_counts()
        for cat in ORDEN:
            if conteo.get(cat, 0):
                p(f"  - {cat:20}: {dias(int(conteo[cat]))}")

    sec("4. CATEGORÍA GLOBAL DIARIA DE LA ESTACIÓN (PEOR CONDICIÓN)")
    conteo = d["Cat_Global_Diaria"].value_counts()
    for cat in ORDEN:
        n = int(conteo.get(cat, 0))
        if n:
            p(f"  - {cat:20}: {dias(n)} ({100 * n / total:.1f}%)")

    sec("5. CONTAMINANTE RESPONSABLE DE LA CATEGORÍA DIARIA")
    resp = d.loc[d["Responsable_Diario"] != "", "Responsable_Diario"].value_counts()
    for c, n in resp.items():
        p(f"  - {c:6}: {dias(int(n))}")
    malos = d[d["Cat_Global_Diaria"].map(lambda c: N.ORDEN.get(c, -1) >= N.ORDEN["Mala"])]
    p(f"Días en Mala o peor: {len(malos)}")
    for c, n in malos["Responsable_Diario"].value_counts().items():
        p(f"  - Responsable {c}: {dias(int(n))}")

    sec("6. DÍAS MÁS DESFAVORABLES (peor categoría y cercanía al límite superior)")
    dd = d[d["Cat_Global_Diaria"] != N.SIN_DATOS].copy()
    dd["orden"] = dd["Cat_Global_Diaria"].map(N.ORDEN)
    dd["pos"] = [N.posicion_en_banda(r[f"Indicador_{r.Responsable_Diario}"], r.Responsable_Diario) for _, r in dd.iterrows()]
    for _, r in dd.sort_values(["orden", "pos"], ascending=False).head(5).iterrows():
        c = r.Responsable_Diario
        p(f"  - {r.Fecha}: {r.Cat_Global_Diaria:10} por {c:5} ({r[f'Indicador_{c}']:g} {UNIDAD[c]})")

    sec("7. PERSPECTIVA HORARIA (ARCHIVO 1)")
    con = h[h["Cat_Global_Horaria"] != N.SIN_DATOS]
    p(f"Horas del periodo: {len(h)} | con categoría: {len(con)} | sin datos: {len(h) - len(con)}")
    conteo = con["Cat_Global_Horaria"].value_counts()
    for cat in N.CATEGORIAS:
        n = int(conteo.get(cat, 0))
        if n:
            p(f"  - {cat:20}: {n} horas ({100 * n / len(con):.1f}%)")
    p("Contaminante responsable por hora:")
    for c, n in con["Responsable_Horario"].value_counts().items():
        p(f"  - {c:6}: {n} horas ({100 * n / len(con):.1f}%)")
    prev = h["Cat_Global_Horaria"].shift()
    cambios = int(((h["Cat_Global_Horaria"] != prev) & prev.notna()).sum())  # mismo criterio que el sitio
    p(f"Cambios de categoría horaria (incluye entradas y salidas de «Sin datos»): {cambios}")

    sec("8. COMPARACIÓN HORARIA VS DIARIA")
    dias_cat = d[d["Cat_Global_Diaria"] != N.SIN_DATOS]
    hb = int(conteo.get("Buena", 0))
    db = int((dias_cat["Cat_Global_Diaria"] == "Buena").sum())
    p(f"Horas en Buena: {100 * hb / len(con):.1f}% | Días en Buena: {100 * db / len(dias_cat):.1f}%")
    peores = 0
    for _, r in dias_cat.iterrows():
        g = N.ORDEN[r.Cat_Global_Diaria]
        hs = con[con["DATE"].dt.strftime("%Y-%m-%d") == r.Fecha]["Cat_Global_Horaria"]
        peores += int((hs.map(N.ORDEN) > g).sum())
    p(f"Horas con una categoría peor que la de su día: {peores}")

    texto = "\n".join(L) + "\n"
    ruta = ruta_reporte(periodo)
    ruta.write_text(texto, encoding="utf-8")
    return texto


def main() -> None:
    ap = argparse.ArgumentParser(description="Reporte de resultados en texto para el reporte en Word")
    ap.add_argument("--periodo", default="2024-03", help="Mes a reportar, formato AAAA-MM")
    periodo = ap.parse_args().periodo
    print(generar(periodo))
    print(f"Guardado en {ruta_reporte(periodo).relative_to(etl.RAIZ)}")


if __name__ == "__main__":
    main()
