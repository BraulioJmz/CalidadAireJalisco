"""Análisis histórico nuevo. Lee originales; no modifica inventario ni C05."""
from __future__ import annotations

import calendar
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import normativa as N
from inventario_sprint3 import inspect_source, VARIABLES
from pm10_modelado import ROOT, csv_save, read_json, sha, write_json

OUT = ROOT / 'data/processed/sprint-3/historico'
POLS = N.POLS + ['NO', 'NOX']
METEO = ['ET', 'RH', 'WS', 'WD']


def native(value):
    if isinstance(value, dict): return {str(k): native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [native(v) for v in value]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (bool, np.bool_)): return bool(value)
    if isinstance(value, (float, np.floating)): return float(value) if np.isfinite(value) else None
    if isinstance(value, pd.Timestamp): return value.isoformat()
    return value


def save_json(path, value):
    write_json(path, native(value))


def daily_tables(clean):
    """Bases, redondeo y bandas de 2024 reutilizados; ninguna normativa en JS."""
    ind = N.indicators(clean)
    co = N.co_base(clean.CO)
    start = clean.index[0]
    for p in ['PM10', 'PM2.5']:
        ind.loc[start:start + pd.Timedelta(hours=10), p] = np.nan
    co.loc[start:start + pd.Timedelta(hours=6)] = np.nan
    ind.loc[start:start + pd.Timedelta(hours=6), 'CO'] = np.nan
    daily = pd.DataFrame(index=pd.date_range(clean.index[0].normalize(), clean.index[-1].normalize(), freq='D'))
    for p in POLS:
        n = clean[p].resample('D').count()
        daily[f'N_{p}'] = n
        if p.startswith('PM'):
            base = clean[p].resample('D').apply(N.mean_decimal)
        elif p == 'CO':
            base = co.resample('D').max()
        elif p in N.POLS:
            base = clean[p].resample('D').max()
        else:
            base = clean[p].resample('D').mean()
        daily[f'EXACT_{p}'] = base.where(n >= 18)
        if p in N.POLS:
            daily[f'I_{p}'] = daily[f'EXACT_{p}'].map(lambda v: N.half_up(v, N.DEC[p]))
            daily[f'C_{p}'] = daily[f'I_{p}'].map(lambda v: N.category(v, p))
            daily[f'N_IND_{p}'] = ind[p].resample('D').count()
        else:
            daily[f'I_{p}'] = daily[f'EXACT_{p}']
            daily[f'C_{p}'] = np.nan
            daily[f'N_IND_{p}'] = n
    for var in METEO:
        daily[f'N_{var}'] = clean[var].resample('D').count()
        if var != 'WD':
            daily[f'M_{var}'] = clean[var].resample('D').mean().where(daily[f'N_{var}'] >= 18)
        else:
            vals = []
            for _, day in clean.groupby(clean.index.normalize()):
                pair = day[['WD', 'WS']].dropna()
                pair = pair[pair.WS > 0]
                angle = np.deg2rad(pair.WD)
                u, v = (np.sin(angle) * pair.WS).sum(), (np.cos(angle) * pair.WS).sum()
                resultant = np.hypot(u, v) / pair.WS.sum() if len(pair) else 0
                vals.append(float(np.degrees(np.arctan2(u, v)) % 360) if len(pair) >= 18 and resultant > 1e-9 else np.nan)
            daily['M_WD'] = vals
    daily.index.name = 'DATE'
    return ind, daily


def is_exploratory(pol, year):
    return pol in ['NO', 'NOX'] or (pol == 'NO2' and year == 2024)


def aggregates(clean, daily):
    periods, profiles = [], []
    for p in POLS:
        for year in range(2015, 2025):
            hour = clean.loc[clean.index.year == year, p]
            day = daily.loc[daily.index.year == year]
            for month in range(13):
                s = hour if month == 0 else hour[hour.index.month == month]
                d = day if month == 0 else day[day.index.month == month]
                count, expected = int(s.count()), len(s)
                quarters = [float(hour[hour.index.quarter == q].notna().mean()) for q in range(1, 5)] if month == 0 else []
                sufficient = count >= np.ceil(.75 * expected) and (month > 0 or min(quarters) >= .75) and not is_exploratory(p, year)
                cats = d[f'C_{p}']
                valid = int(cats.count()) if p in N.POLS else None
                counts = [int(cats.eq(i).sum()) for i in range(5)] if p in N.POLS else None
                periods.append({'year': year, 'month': month, 'pollutant': p, 'n': count, 'expected': expected,
                                 'coverage': 100 * count / expected, 'mean': s.mean() if count else None, 'median': s.median() if count else None, 'max': s.max() if count else None,
                                 'p95': s.quantile(.95) if count else None, 'sufficient': bool(sufficient), 'quarterly_coverage': [100 * q for q in quarters],
                                 'category_applicable': p in N.POLS, 'counts': counts, 'days_valid': valid, 'days_expected': len(d),
                                 'days_missing': len(d) - valid if valid is not None else None,
                                 'bad': sum(counts[2:]) if counts is not None else None,
                                 'bad_pct': 100 * sum(counts[2:]) / valid if valid else None,
                                 'daily_sufficient': valid >= np.ceil(.75 * len(d)) if valid is not None else False,
                                 'exploratory': is_exploratory(p, year)})
        for year in [0, *range(2015, 2025)]:
            s = clean[p] if year == 0 else clean.loc[clean.index.year == year, p]
            for kind, values, bins in [('hour', s.index.hour, range(24)), ('season', s.index.month, range(1, 13))]:
                for value in bins:
                    part = s[values == value]
                    profiles.append({'pollutant': p, 'year': year, 'kind': kind, 'bin': value, 'n': int(part.count()),
                                     'expected': len(part), 'mean': part.mean(), 'coverage': 100 * part.count() / len(part)})
    return periods, profiles


def paired(daily, a, b, p, month):
    first = daily[daily.index.year == a]
    second = daily[daily.index.year == b]
    if month:
        first, second = first[first.index.month == month], second[second.index.month == month]
    first = first.set_axis(first.index.strftime('%m-%d'))
    second = second.set_axis(second.index.strftime('%m-%d'))
    common = first.index.intersection(second.index)
    pairs = pd.concat([first[f'EXACT_{p}'].reindex(common).rename('a'), second[f'EXACT_{p}'].reindex(common).rename('b')], axis=1).dropna()
    quarters = []
    for quarter in range(4):
        keys = [key for key in common if int(key[:2]) in range(quarter * 3 + 1, quarter * 3 + 4)]
        if keys:
            quarters.append({'quarter': quarter + 1, 'expected': len(keys), 'n': sum(key in pairs.index for key in keys)})
    sufficient = len(pairs) >= np.ceil(.75 * len(common)) and (month > 0 or all(q['n'] >= .75 * q['expected'] for q in quarters))
    sufficient = sufficient and not (is_exploratory(p, a) or is_exploratory(p, b))
    av, bv = pairs.a.mean(), pairs.b.mean()
    return native({'year_a': a, 'year_b': b, 'month': month, 'pollutant': p, 'n': len(pairs), 'expected': len(common),
                   'a': av, 'b': bv, 'delta': bv - av, 'change_pct': 100 * (bv - av) / av if len(pairs) and av != 0 else None,
                   'sufficient': sufficient, 'quarterly': quarters, 'dates': list(pairs.index)})


def events_and_anomalies(clean, daily):
    episodes, peaks, anomalies = [], [], []
    for p in POLS:
        if p in N.POLS:
            active = daily[f'C_{p}'].ge(2)
            groups = active.ne(active.shift()).cumsum()
            for _, g in daily[active].groupby(groups[active]):
                if len(g) >= 2:
                    episodes.append({'pollutant': p, 'start': g.index[0].date().isoformat(), 'end': g.index[-1].date().isoformat(),
                                     'days': len(g), 'max_category': int(g[f'C_{p}'].max()), 'max_indicator': g[f'I_{p}'].max(),
                                     'n_hours': int(g[f'N_{p}'].sum()), 'expected_hours': 24 * len(g)})
        for year in range(2015, 2025):
            s = clean.loc[clean.index.year == year, p].dropna().sort_values(ascending=False, kind='stable')
            chosen = []
            for time, value in s.items():
                if any(abs(time - old) < pd.Timedelta(hours=24) for old in chosen): continue
                chosen.append(time)
                peaks.append({'pollutant': p, 'year': year, 'date': time.isoformat(), 'value': value,
                              'exploratory': is_exploratory(p, year)})
                if len(chosen) == 3: break
        floors = {'PM10': 10, 'PM2.5': 5, 'O3': .005, 'CO': .1, 'NO2': .005, 'SO2': .005, 'NO': .005, 'NOX': .005}
        s = clean[p]
        keys = [s.index.year, s.index.month, s.index.hour]
        med = s.groupby(keys).transform('median')
        mad = (s - med).abs().groupby(keys).transform('median')
        z = (s - med) / np.maximum(1.4826 * mad, floors[p])
        for time in z.index[z.abs() > 3.5]:
            anomalies.append({'date': time.isoformat(), 'pollutant': p, 'value': s.at[time], 'robust_z': z.at[time],
                              'action': 'conservar_y_revisar', 'source_year': time.year})
    return native(episodes), native(peaks), native(anomalies)


def meteorology(daily):
    rows, points = [], []
    for year in range(2015, 2025):
        for month in range(1, 13):
            d = daily[(daily.index.year == year) & (daily.index.month == month)]
            for p in POLS:
                for variable in ['ET', 'RH', 'WS']:
                    pair = d[[f'EXACT_{p}', f'M_{variable}']].dropna().round(12)
                    rho = float(spearmanr(pair.iloc[:, 0], pair.iloc[:, 1]).statistic) if len(pair) >= 15 and pair.iloc[:, 0].nunique() > 1 and pair.iloc[:, 1].nunique() > 1 else None
                    group = {'year': year, 'month': month, 'pollutant': p, 'variable': variable, 'n': len(pair),
                             'expected': len(d), 'rho': rho, 'status': 'descriptivo_no_causal' if rho is not None else 'pares_insuficientes_o_constantes'}
                    rows.append(group)
                    for time, r in pair.iterrows():
                        points.append({'date': time.date().isoformat(), **{k: group[k] for k in ['year', 'month', 'pollutant', 'variable']},
                                       'x': r.iloc[1], 'y': r.iloc[0]})
    return native(rows), native(points)


def run():
    if (OUT / 'manifiesto.json').exists():
        raise ValueError('Histórico ya calculado: conservar resultados y verificar; no sobrescribir silenciosamente')
    OUT.mkdir(parents=True, exist_ok=True)
    sources = read_json(ROOT / 'config/fuentes_sprint3.json')
    frames = []
    for source in sources['fuentes']:
        detail, arrays, _, _ = inspect_source(source)
        year = source['year']
        index = pd.date_range(f'{year}-01-01', f'{year}-12-31 23:00', freq='h')
        frames.append(pd.DataFrame(arrays, index=index))
        print(f'{year}: datos del inventario reutilizados en memoria, sin modificar sus archivos', flush=True)
    clean = pd.concat(frames)
    clean.index.name = 'DATE'
    csv_save(clean.reset_index(), OUT / 'horario.csv')
    ind, daily = daily_tables(clean)
    csv_save(ind.reset_index().rename(columns={'index': 'DATE'}), OUT / 'indicadores_horarios.csv')
    csv_save(daily.reset_index(), OUT / 'diario.csv')
    periods, profiles = aggregates(clean, daily)
    for name, value in [('periodos', periods), ('perfiles', profiles)]:
        save_json(OUT / f'{name}.json', value)
        csv_save(pd.DataFrame([{k: json.dumps(native(v)) if isinstance(v, (list, dict)) else v for k, v in r.items()} for r in native(value)]), OUT / f'{name}.csv')
    pairs = [paired(daily, a, b, p, m) for a in range(2015, 2025) for b in range(a + 1, 2025) for p in POLS for m in range(13)]
    save_json(OUT / 'comparaciones.json', pairs)
    episodes, peaks, anomalies = events_and_anomalies(clean, daily)
    for name, records in [('episodios', episodes), ('maximos_horarios', peaks), ('atipicos_horarios', anomalies)]:
        save_json(OUT / f'{name}.json', records)
        csv_save(pd.DataFrame(records), OUT / f'{name}.csv')
    meteo, points = meteorology(daily)
    save_json(OUT / 'meteorologia.json', meteo)
    csv_save(pd.DataFrame(meteo), OUT / 'meteorologia.csv')
    csv_save(pd.DataFrame(points), OUT / 'pares_meteorologicos.csv')
    save_json(OUT / 'manifiesto.json', {'schema': 'mir-historico-v1', 'source_manifest_sha256': sha(ROOT / 'config/fuentes_sprint3.json'),
                                      'criteria_sha256': sha(ROOT / 'docs/sprints/sprint-3/integracion/CRITERIOS_HISTORICOS.md'),
                                      'normativa_version': N.VERSION, 'normativa_sha256': sha(ROOT / 'pipeline/normativa.py'),
                                      'sources': sources['fuentes'], 'hours': len(clean), 'days': len(daily),
                                      'files': {p.name: sha(p) for p in OUT.iterdir() if p.is_file()}})
    print('Histórico terminado:', len(clean), 'horas,', len(daily), 'días,', len(pairs), 'comparaciones', flush=True)


if __name__ == '__main__':
    run()
