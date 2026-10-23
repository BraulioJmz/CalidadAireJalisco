"""Sprint 2: comparación retrospectiva con un único esquema de bandas de 2024.

La implementación de referencia de Sprint 1 se conserva en nom172.py. Aquí se
aplica el factor de ajuste al cociente sin redondearlo antes, NOM 5.2.5.3, y se
redondea la concentración base final según 5.2.4. No reconstruye avisos oficiales.
"""
from decimal import Decimal, ROUND_HALF_UP
import math
import numpy as np
import pandas as pd

CATS = ["Buena", "Aceptable", "Mala", "Muy Mala", "Extremadamente Mala"]
POLS = ["PM10", "PM2.5", "O3", "CO", "NO2", "SO2"]
CORE = ["PM10", "PM2.5", "O3", "CO"]
BANDS = {"PM10": [45, 60, 132, 213], "PM2.5": [15, 33, 79, 130],
         "O3": [.058, .090, .135, .175], "CO": [5, 9, 12, 16],
         "NO2": [.053, .106, .160, .213], "SO2": [.035, .075, .185, .304]}
DEC = {"PM10": 0, "PM2.5": 0, "O3": 3, "CO": 2, "NO2": 3, "SO2": 3}
UNITS = {p: "µg/m³" if p.startswith("PM") else "ppm" for p in POLS}
LABELS = {"PM10": "PM₁₀", "PM2.5": "PM₂.₅", "O3": "O₃", "CO": "CO", "NO2": "NO₂", "SO2": "SO₂", "GLOBAL": "Global comparable"}
VERSION = "sprint2-revision01-nom172-bandas2024"

def half_up(x, decimals=0):
    if pd.isna(x) or not math.isfinite(float(x)):
        return np.nan
    return float(Decimal(str(float(x))).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP))

def category(x, pol):
    if pd.isna(x) or float(x) < 0 or not math.isfinite(float(x)):
        return np.nan
    return float(np.searchsorted(BANDS[pol], x, side="left"))

def nowcast(window, pol):
    if pol not in ("PM10", "PM2.5"):
        raise ValueError("NowCast solo admite PM10 o PM2.5")
    vals = np.asarray(window, dtype=float)
    if not 1 <= len(vals) <= 12:
        raise ValueError("La ventana NowCast debe tener entre 1 y 12 horas")
    good = np.isfinite(vals) & (vals >= 0)
    if good[-3:].sum() < 2:
        return np.nan
    # Aritmética decimal también en los promedios: 0.485 no debe convertirse
    # en 0.48499999999999993 antes del redondeo normativo.
    data = [(i, Decimal(str(v))) for i,v in enumerate(vals[::-1]) if np.isfinite(v) and v>=0]
    hi, lo = max(v for _,v in data), min(v for _,v in data)
    weight = max(Decimal('.5'), (lo/hi).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)) if hi else Decimal(1)
    mean = sum(v*weight**i for i,v in data)/sum(weight**i for i,v in data)
    factor = Decimal('.714') if pol == 'PM10' else Decimal('.694')
    return float((mean*factor).quantize(Decimal(1),rounding=ROUND_HALF_UP))

def mean_decimal(values):
    vals = [Decimal(str(v)) for v in values if pd.notna(v) and math.isfinite(float(v))]
    return float(sum(vals)/Decimal(len(vals))) if vals else np.nan

def co_base(s):
    return s.rolling(8,min_periods=6).apply(mean_decimal,raw=True)

def indicators(raw):
    if not isinstance(raw.index, pd.DatetimeIndex) or raw.index.has_duplicates:
        raise ValueError("Se requiere índice horario único")
    if len(raw) > 1 and not np.all(np.diff(raw.index.asi8) == pd.Timedelta(hours=1).value):
        raise ValueError("Reindexe a horas consecutivas antes de calcular")
    out = pd.DataFrame(index=raw.index)
    for p in POLS:
        s = raw[p]
        if p.startswith("PM"):
            out[p] = s.rolling(12, min_periods=1).apply(lambda a: nowcast(a, p), raw=True)
        elif p == "CO":
            out[p] = co_base(s).map(lambda a: half_up(a, 2))
        else:
            out[p] = s.map(lambda a: half_up(a, DEC[p]))
    return out
