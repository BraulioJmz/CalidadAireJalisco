"""Funciones causales compartidas del primer experimento PM10, sin interfaz."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/sprint-3/modelado'
DOCS = ROOT / 'docs/sprints/sprint-3/modelado'
PROTOCOL = ROOT / 'config/sprint3_modelado_protocolo.json'
HORIZONS = (1, 2, 3)
PARTS = ('train', 'validation', 'test')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def csv_save(frame, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format='%.17g', lineterminator='\n', date_format='%Y-%m-%dT%H:%M:%S')


def audit(out, event, **data):
    with (Path(out) / 'eventos.jsonl').open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps({'utc': utc(), 'event': event, **data}, ensure_ascii=False, allow_nan=False) + '\n')


def feature_names():
    return ([f'pm10_lag_{lag}' for lag in range(24)] +
            [f'pm10_{stat}_{w}h' for w in (3, 6, 12, 24) for stat in ('mean', 'std', 'min', 'max')] +
            ['hour_sin', 'hour_cos', 'weekday_sin', 'weekday_cos', 'annual_sin', 'annual_cos', 'weekend'])


def require_grid(series):
    if not len(series):
        raise ValueError('Serie vacía')
    if not isinstance(series.index, pd.DatetimeIndex) or series.index.tz is not None:
        raise ValueError('Se requiere DatetimeIndex local sin zona explícita, conforme a la fuente')
    if series.index.has_duplicates or not series.index.is_monotonic_increasing:
        raise ValueError('Fechas duplicadas o desordenadas')
    if not series.index.equals(pd.date_range(series.index[0], series.index[-1], freq='h')):
        raise ValueError('La serie debe mantener las horas ausentes en la rejilla, como NaN')
    if np.isinf(series.to_numpy(dtype=float)).any() or series.lt(0).any():
        raise ValueError('PM10 no utilizable: infinito o negativo')


def causal_features(series):
    """Cada fila en t depende exclusivamente de PM10[t-23:t] y su calendario."""
    require_grid(series)
    values = {f'pm10_lag_{lag}': series.shift(lag) for lag in range(24)}
    for w in (3, 6, 12, 24):
        past = np.lib.stride_tricks.sliding_window_view(np.pad(series.to_numpy(dtype=float), (w - 1, 0), constant_values=np.nan), w)
        # Recalcular cada resumen a partir de su propio pasado evita incluso
        # dependencia numérica de acumuladores de ventanas anteriores a t-23.
        values.update({f'pm10_mean_{w}h': past.mean(axis=1), f'pm10_std_{w}h': past.std(axis=1, ddof=0),
                       f'pm10_min_{w}h': past.min(axis=1), f'pm10_max_{w}h': past.max(axis=1)})
    index = series.index
    annual = ((index.dayofyear - 1) + index.hour / 24) / np.where(index.is_leap_year, 366, 365)
    for name, phase in [('hour', index.hour / 24), ('weekday', index.dayofweek / 7), ('annual', annual)]:
        values[f'{name}_sin'] = np.sin(2 * np.pi * phase)
        values[f'{name}_cos'] = np.cos(2 * np.pi * phase)
    values['weekend'] = (index.dayofweek >= 5).astype(float)
    return pd.DataFrame(values, index=index)[feature_names()]


def sample_audit(series):
    require_grid(series)
    index = series.index
    context = series.rolling(24, min_periods=24).count().eq(24)
    target_good = pd.concat([series.shift(-h).notna() for h in HORIZONS], axis=1).all(axis=1)
    initial = context & target_good
    end = index + pd.Timedelta(hours=3)
    partition = np.where(index.year <= 2022, 'train', np.where(index.year == 2023, 'validation', 'test'))
    cross = ((partition == 'train') & (end >= pd.Timestamp('2023-01-01'))) | ((partition == 'validation') & (end >= pd.Timestamp('2024-01-01')))
    accepted = initial & ~cross
    reasons = np.where(~context, 'contexto_incompleto', np.where(~target_good, 'objetivos_incompletos', np.where(cross, 'objetivos_cruzan_frontera', 'incluida')))
    return pd.DataFrame({'origin': index, 'year': index.year, 'month': index.month, 'partition': partition,
                         'pm10_observed': series.notna().to_numpy(), 'context_complete': context.to_numpy(),
                         'targets_complete': target_good.to_numpy(), 'initial_window': initial.to_numpy(),
                         'boundary_excluded': (initial & cross).to_numpy(), 'included': accepted.to_numpy(),
                         'refit_included': (initial & (end < pd.Timestamp('2024-01-01'))).to_numpy(),
                         'reason': reasons}, index=index)


def baselines(matrix, names):
    x = np.asarray(matrix, dtype=float)
    last = x[:, names.index('pm10_lag_0')]
    daily = np.column_stack([x[:, names.index(f'pm10_lag_{24 - h}')] for h in HORIZONS])
    return {'persistencia': np.repeat(last[:, None], 3, axis=1), 'diaria': daily}


def calculate_metrics(observed, predicted):
    y = np.asarray(observed, dtype=float)
    p = np.asarray(predicted, dtype=float)
    if y.shape != p.shape or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError('Métricas requieren pares finitos de igual tamaño; no eliminar filas silenciosamente')
    n = len(y)
    if not n:
        return {'n': 0, 'mae': None, 'rmse': None, 'r2': None, 'r2_reason': 'sin_muestras',
                'bias': None, 'over_fraction': None, 'under_fraction': None}
    error = p - y
    total = float(np.square(y - y.mean()).sum())
    r2 = None if n < 2 or total == 0 else float(1 - np.square(error).sum() / total)
    return {'n': n, 'mae': float(np.abs(error).mean()), 'rmse': float(np.sqrt(np.square(error).mean())),
            'r2': r2, 'r2_reason': 'n_menor_2' if n < 2 else 'observado_constante' if total == 0 else '',
            'bias': float(error.mean()), 'over_fraction': float((error > 0).mean()), 'under_fraction': float((error < 0).mean())}


def metrics_tables(frames, threshold):
    global_rows, monthly_rows, high_rows = [], [], []
    for frame in frames:
        for (part, model, horizon, fit), group in frame.groupby(['partition', 'model', 'horizon', 'fit_period'], sort=True):
            tags = {'partition': part, 'model': model, 'horizon': int(horizon), 'fit_period': fit}
            global_rows.append({**tags, **calculate_metrics(group.observed, group.predicted)})
            high = group[group.observed >= threshold]
            high_rows.append({**tags, 'month': 0, 'threshold_train_p90': threshold, **calculate_metrics(high.observed, high.predicted)})
            month = pd.to_datetime(group.target_time).dt.month
            for m in range(1, 13):
                sub = group[month.eq(m)]
                monthly_rows.append({**tags, 'month': m, **calculate_metrics(sub.observed, sub.predicted)})
                high = sub[sub.observed >= threshold]
                high_rows.append({**tags, 'month': m, 'threshold_train_p90': threshold, **calculate_metrics(high.observed, high.predicted)})
    return pd.DataFrame(global_rows), pd.DataFrame(monthly_rows), pd.DataFrame(high_rows)


def select_key(candidate, mean_mae):
    return (round(float(mean_mae), 8), candidate['max_leaf_nodes'], candidate['max_iter'], candidate['learning_rate'], candidate['id'])


def predict_at(artifacts, history, origin):
    """Predicción operable solo con historia hasta t. Nunca accede a etiquetas."""
    origin = pd.Timestamp(origin)
    index = pd.date_range(origin - pd.Timedelta(hours=23), origin, freq='h')
    if history.index.has_duplicates:
        raise ValueError('Historia con fechas duplicadas')
    context = history.reindex(index).astype(float)
    if context.isna().any():
        raise ValueError('No están disponibles las 24 observaciones pasadas')
    x = causal_features(context).iloc[[-1]]
    results = {}
    for h in HORIZONS:
        item = artifacts[h]
        if item['features'] != list(x.columns):
            raise ValueError('Contrato de características incompatible')
        results[h] = float(item['estimator'].predict(x.to_numpy())[0])
    return results
