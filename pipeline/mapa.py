"""
Mapa de referencia: Jalisco, Área Metropolitana de Guadalajara y estaciones de SEMADET.

Entradas:
    - Límites municipales de Jalisco (INEGI, Marco Geoestadístico), en GeoJSON. Se descarga una vez a
      data/external/jalisco_municipios.json (no se versiona: pesa ~14 MB).
    - Coordenadas de las estaciones: hoja Param de BD_<AÑO>.xlsx.
Salidas:
    - web/data/mapa_jalisco.json            geometría simplificada lista para dibujar en SVG
    - data/processed/estaciones_semadet.csv catálogo de estaciones con coordenadas

Uso (desde la raíz):
    python pipeline/mapa.py
"""
from __future__ import annotations

import argparse
import json
import math
import re
import urllib.request
from pathlib import Path

import pandas as pd

import etl

URL_MUNICIPIOS = "https://raw.githubusercontent.com/PhantomInsights/mexico-geojson/main/2023/states/Jalisco.json"
GEOJSON = etl.RAIZ / "data" / "external" / "jalisco_municipios.json"
SALIDA = etl.RAIZ / "web" / "data" / "mapa_jalisco.json"
CATALOGO = etl.PROCESSED / "estaciones_semadet.csv"

# Municipios del Área Metropolitana de Guadalajara (se resaltan en el mapa estatal)
AMG = {"Guadalajara", "Zapopan", "San Pedro Tlaquepaque", "Tonalá", "Tlajomulco de Zúñiga", "El Salto",
       "Juanacatlán", "Ixtlahuacán de los Membrillos", "Zapotlanejo", "Acatlán de Juárez"}
ETIQUETAS_AMG = {"Guadalajara", "Zapopan", "San Pedro Tlaquepaque", "Tonalá", "Tlajomulco de Zúñiga", "El Salto"}
# Ajuste manual (px) de etiquetas que caen sobre una estación
DESPLAZA = {"Guadalajara": (8, -28)}


def estaciones(bd: Path) -> pd.DataFrame:
    p = pd.read_excel(bd, sheet_name="Param")
    filas = []
    for _, r in p.iloc[:, :7].dropna(subset=[p.columns[1]]).iterrows():
        nombre, clave = str(r.iloc[0]).strip(), str(r.iloc[1]).strip()
        # En tres estaciones de 2024 (COU, SAN, SMT) la hoja trae el nombre y la abreviatura intercambiados
        if re.fullmatch(r"[A-Z]{3}", nombre) and not re.fullmatch(r"[A-Z]{3}", clave):
            nombre, clave = clave, nombre
        txt = str(r.iloc[4])
        lat = float(re.search(r"Latitud:\s*(-?[\d.]+)", txt).group(1))
        lon = float(re.search(r"Longitud:\s*(-?[\d.]+)", txt).group(1))
        alt = re.search(r"Altitud:\s*([\d.]+)", txt)
        filas.append({"clave": clave, "nombre": nombre, "lat": lat, "lon": lon,
                      "altitud": int(float(alt.group(1))) if alt else None,
                      "contaminantes": "" if pd.isna(r.iloc[2]) else str(r.iloc[2]).replace("PM 2.5", "PM2.5"),
                      "anio_instalacion": int(r.iloc[6]) if pd.notna(r.iloc[6]) else None})
    return pd.DataFrame(filas)


def _dp(pts, tol):
    """Simplificación de Douglas-Peucker."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    norma = math.hypot(dx, dy) or 1e-12
    dist = [abs(dy * x - dx * y + x2 * y1 - y2 * x1) / norma for x, y in pts[1:-1]]
    i = max(range(len(dist)), key=dist.__getitem__)
    if dist[i] > tol:
        return _dp(pts[: i + 2], tol)[:-1] + _dp(pts[i + 1:], tol)
    return [pts[0], pts[-1]]


class Proyeccion:
    """Equirectangular con corrección por coseno de la latitud; y crece hacia el sur."""

    def __init__(self, lon0, lon1, lat0, lat1, ancho):
        self.k = math.cos(math.radians((lat0 + lat1) / 2))
        self.lon0, self.lat1 = lon0, lat1
        self.s = ancho / ((lon1 - lon0) * self.k)
        self.w, self.h = ancho, (lat1 - lat0) * self.s

    def __call__(self, lon, lat):
        return (lon - self.lon0) * self.k * self.s, (self.lat1 - lat) * self.s


def _anillos(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [ring for poly in polys for ring in poly]


def _dp_anillo(pts, tol):
    """Douglas-Peucker para un anillo cerrado: se parte en el punto más lejano al inicio para no colapsarlo."""
    if len(pts) < 4:
        return pts
    x0, y0 = pts[0]
    m = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
    return _dp(pts[: m + 1], tol)[:-1] + _dp(pts[m:], tol)


def _path(anillos, proy, tol):
    partes = []
    for ring in anillos:
        pts = _dp_anillo([proy(lon, lat) for lon, lat in ring], tol)
        if len(pts) >= 3:
            partes.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(partes)


def generar(bd: Path) -> None:
    if not GEOJSON.exists():
        GEOJSON.parent.mkdir(parents=True, exist_ok=True)
        print(f"Descargando límites municipales de INEGI → {GEOJSON.relative_to(etl.RAIZ)}")
        urllib.request.urlretrieve(URL_MUNICIPIOS, GEOJSON)
    muni = json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]
    est = estaciones(bd)
    est.to_csv(CATALOGO, index=False)

    # Vista estatal
    todos = [pt for f in muni for ring in _anillos(f["geometry"]) for pt in ring]
    lons, lats = [p[0] for p in todos], [p[1] for p in todos]
    pe = Proyeccion(min(lons), max(lons), min(lats), max(lats), 420)
    # Recuadro del acercamiento: estaciones con margen
    m = 0.07
    b = (est.lon.min() - m, est.lon.max() + m, est.lat.min() - m, est.lat.max() + m)
    x0, y0 = pe(b[0], b[3])
    x1, y1 = pe(b[1], b[2])
    mir = est[est.clave == etl.STATION_CODE].iloc[0]
    estado = {
        "w": round(pe.w), "h": round(pe.h), "px_km": round(pe.s / 111.32, 4),
        "municipios": [{"nombre": f["properties"]["NOMGEO"], "amg": f["properties"]["NOMGEO"] in AMG,
                        "d": _path(_anillos(f["geometry"]), pe, 0.6)} for f in muni],
        "recuadro": {"x": round(x0, 1), "y": round(y0, 1), "w": round(x1 - x0, 1), "h": round(y1 - y0, 1)},
        "mir": [round(v, 1) for v in pe(mir.lon, mir.lat)],
    }

    # Acercamiento al AMG
    pz = Proyeccion(b[0], b[1], b[2], b[3], 520)
    zona = []
    for f in muni:
        anillos = _anillos(f["geometry"])
        dentro = [(lon, lat) for ring in anillos for lon, lat in ring if b[0] <= lon <= b[1] and b[2] <= lat <= b[3]]
        if not dentro:
            continue
        nombre = f["properties"]["NOMGEO"]
        lx, ly = pz(sum(p[0] for p in dentro) / len(dentro), sum(p[1] for p in dentro) / len(dentro))
        zona.append({"nombre": nombre, "d": _path(anillos, pz, 0.8),
                     "etiqueta": [round(lx + DESPLAZA.get(nombre, (0, 0))[0], 1), round(ly + DESPLAZA.get(nombre, (0, 0))[1], 1)]
                     if nombre in ETIQUETAS_AMG else None})
    datos = {
        "fuente": "Límites municipales: INEGI, Marco Geoestadístico (vía PhantomInsights/mexico-geojson). "
                  "Estaciones: SEMADET, hoja Param de BD_2024.xlsx.",
        "estado": estado,
        "zona": {"w": round(pz.w), "h": round(pz.h), "px_km": round(pz.s / 111.32, 4), "municipios": zona,
                 "estaciones": [{"clave": r.clave, "nombre": r.nombre, "xy": [round(v, 1) for v in pz(r.lon, r.lat)],
                                 "lat": r.lat, "lon": r.lon, "altitud": r.altitud, "contaminantes": r.contaminantes,
                                 "anio": r.anio_instalacion} for r in est.itertuples()]},
    }
    SALIDA.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    print(f"Mapa generado: {SALIDA.relative_to(etl.RAIZ)} ({SALIDA.stat().st_size / 1024:.0f} KB) · {len(est)} estaciones")


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera el mapa de referencia de Jalisco y las estaciones SEMADET")
    ap.add_argument("--bd", type=Path, default=etl.ruta_bd(2024), help="Base anual con la hoja Param")
    generar(ap.parse_args().bd)


if __name__ == "__main__":
    main()
