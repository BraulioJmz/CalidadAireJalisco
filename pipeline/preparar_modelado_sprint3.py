"""Extrae PM10 y registra muestras/EDA según protocolo anterior al ajuste."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from inventario_sprint3 import Book, as_datetime, detect_header, numeric, norm, plausible
from pm10_modelado import (ROOT, OUT, DOCS, PROTOCOL, audit, causal_features,
                          csv_save, read_json, sample_audit, sha, utc, write_json)


def extract_pm10():
    manifest = read_json(ROOT / 'config/fuentes_sprint3.json')
    expected_coverage = pd.read_csv(ROOT / 'data/processed/sprint-3/cobertura_anual.csv')
    pieces = []
    for source in manifest['fuentes']:
        year = source['year']
        path = ROOT / source['path']
        if sha(path) != source['sha256']:
            raise ValueError(f'Original {year} distinto al inventario')
        book = Book(path)
        try:
            detail = read_json(ROOT / f'data/processed/sprint-3/libro_{year}.json')
            sheet = next(s for s in book.sheets if s['name'] == detail['data_sheet'])
            header_row, names, original = detect_header(book, sheet)
            if list(original.values()) != detail['headers_original']:
                raise ValueError('Cambió la estructura del original')
            station_col = next(i for i, n in names.items() if n == 'STATION')
            records = []
            for number, vals, *_ in book.rows(sheet, station_col):
                if number <= header_row:
                    continue
                row = {names[i]: value for i, value in vals.items() if i in names}
                date = as_datetime(row.get('DATE'), book.epoch)
                if date is None or date.year != year or date.tzinfo is not None or date.minute or date.second or date.microsecond:
                    raise ValueError(f'Fecha no utilizable: {year}:{number}')
                value = numeric(row.get('PM10'))
                usable = value is not None and plausible('PM10', value)
                reason = 'utilizable' if usable else 'ausencia' if row.get('PM10') is None or not str(row.get('PM10')).strip() else 'valor_no_utilizable'
                records.append({'DATE': date, 'PM10': value if usable else np.nan,
                                'raw_value': row.get('PM10'), 'usable': usable, 'reason': reason,
                                'source_file': source['path'], 'source_excel_row': number})
            dates = Counter(r['DATE'] for r in records)
            if any(n > 1 for n in dates.values()):
                raise ValueError('Fechas duplicadas: no se compactan ni promedian')
            frame = pd.DataFrame(records).set_index('DATE').sort_index()
            index = pd.date_range(f'{year}-01-01', f'{year}-12-31 23:00', freq='h')
            frame = frame.reindex(index)
            frame.index.name = 'DATE'
            frame['reason'] = frame.reason.fillna('fila_ausente')
            frame['usable'] = frame.PM10.notna()
            expected = int(expected_coverage[(expected_coverage.year == year) & (expected_coverage.variable == 'PM10')].iloc[0].usable_basic_hours)
            if int(frame.usable.sum()) != expected or sha(path) != source['sha256']:
                raise ValueError(f'No concilia PM10 {year} con el inventario')
            pieces.append(frame)
            print(f'{year}: PM10 extraído; {expected}/{len(index)} horas utilizables', flush=True)
        finally:
            book.close()
    return pd.concat(pieces)


def eda_training(series, out):
    training = series.loc[:'2022-12-31 23:00']
    rows = []
    for grouping, bins, values in [('hour', range(24), training.index.hour), ('month', range(1, 13), training.index.month)]:
        for key in bins:
            sub = training[values == key]
            available = sub.dropna()
            rows.append({'grouping': grouping, 'bin': key, 'expected': len(sub), 'n': len(available),
                         'missing': int(sub.isna().sum()), 'mean': available.mean(), 'median': available.median(),
                         'p90': available.quantile(.9), 'coverage_pct': 100 * len(available) / len(sub)})
    csv_save(pd.DataFrame(rows), out / 'eda_perfiles_train.csv')
    acf = []
    for lag in [*range(1, 49), 72, 168]:
        previous = training.shift(lag)
        both = training.notna() & previous.notna()
        acf.append({'lag_hours': lag, 'n_pairs': int(both.sum()), 'possible_pairs': len(training) - lag,
                    'pearson_pairwise': training[both].corr(previous[both])})
    csv_save(pd.DataFrame(acf), out / 'eda_acf_train.csv')
    threshold = float(np.quantile(training.dropna().to_numpy(), .9, method='linear'))
    return {'population': 'Horas PM10 utilizables únicas 2015–2022', 'n': int(training.notna().sum()),
            'expected': len(training), 'train_p90': threshold, 'quantile_method': 'linear'}


def prepare(out=OUT):
    out = Path(out)
    if (out / 'datos_congelados.json').exists():
        raise ValueError('Preparación ya registrada; no sobrescribir. Use --out para una reproducción separada de resultados.')
    protocol = read_json(PROTOCOL)
    if sha(ROOT / 'config/fuentes_sprint3.json') != protocol['source_manifest_sha256']:
        raise ValueError('Cambió el manifiesto de fuentes frente al protocolo')
    out.mkdir(parents=True, exist_ok=True)
    audit(out, 'preparation_started', protocol_sha256=sha(PROTOCOL))
    frame = extract_pm10()
    series = frame.PM10
    csv_save(frame.reset_index(), out / 'pm10_horario.csv')
    features = causal_features(series)
    if list(features.columns) != protocol['features']:
        raise ValueError('Características distintas del protocolo')
    labels = pd.DataFrame({f'target_{h}': series.shift(-h) for h in (1, 2, 3)})
    audit_frame = sample_audit(series)
    accepted_initial = audit_frame.initial_window
    initial = audit_frame.loc[accepted_initial].copy()
    initial['sample_id'] = np.arange(len(initial))
    initial['target_1'] = initial.index + pd.Timedelta(hours=1)
    initial['target_2'] = initial.index + pd.Timedelta(hours=2)
    initial['target_3'] = initial.index + pd.Timedelta(hours=3)
    reference = pd.read_csv(ROOT / 'data/processed/sprint-3/disponibilidad_horizontes.csv')
    expected_by_year = reference[reference.variable == 'PM10'].set_index('year').windows_24past_3future
    if not initial.groupby('year').size().eq(expected_by_year).all() or len(initial) != protocol['initial_inventory_windows']:
        raise ValueError('No concilian las 53,608 ventanas iniciales')
    x = features.loc[initial.index].to_numpy(dtype=float)
    y = labels.loc[initial.index].to_numpy(dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Una muestra completa contiene ausencias')
    np.save(out / 'features.npy', x, allow_pickle=False)
    np.save(out / 'targets.npy', y, allow_pickle=False)
    csv_save(initial.reset_index(drop=True), out / 'origenes.csv')
    csv_save(audit_frame.reset_index(drop=True), out / 'auditoria_muestras.csv')
    columns = ['pm10_observed', 'context_complete', 'targets_complete', 'initial_window', 'boundary_excluded', 'included', 'refit_included']
    counts = audit_frame.groupby(['year', 'month', 'partition'])[columns].sum().astype(int)
    counts['expected_origins'] = audit_frame.groupby(['year', 'month', 'partition']).size()
    csv_save(counts.reset_index(), out / 'conciliacion_mensual.csv')
    threshold = eda_training(series, out)
    excluded = initial[initial.boundary_excluded]
    files = ['pm10_horario.csv', 'features.npy', 'targets.npy', 'origenes.csv', 'auditoria_muestras.csv',
             'conciliacion_mensual.csv', 'eda_perfiles_train.csv', 'eda_acf_train.csv']
    result = {'prepared_utc': utc(), 'protocol_sha256': sha(PROTOCOL), 'features': list(features.columns),
              'sources_manifest_sha256': sha(ROOT / 'config/fuentes_sprint3.json'),
              'initial_windows': len(initial), 'boundary_excluded': len(excluded), 'comparison_windows': int(initial.included.sum()),
              'comparison_counts': initial[initial.included].groupby('partition').size().astype(int).to_dict(),
              'final_refit_n': int(initial.refit_included.sum()), 'high_diagnostic': threshold,
              'boundary_origins': excluded[['origin', 'partition', 'target_3']].astype(str).to_dict('records'),
              'files_sha256': {name: sha(out / name) for name in files}}
    write_json(out / 'datos_congelados.json', result, exclusive=True)
    audit(out, 'preparation_finished', **{k: result[k] for k in ['initial_windows', 'boundary_excluded', 'comparison_windows', 'comparison_counts', 'final_refit_n']})
    print(result['comparison_counts'], 'exclusiones de frontera:', len(excluded), 'p90 train:', threshold['train_p90'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=OUT)
    prepare(parser.parse_args().out)
