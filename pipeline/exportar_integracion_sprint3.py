"""Contrato web por consultas, derivado de histórico y evaluación C05 congelados."""
from __future__ import annotations

import calendar
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

import normativa as N
from historico_sprint3 import OUT as HIST, POLS, METEO, save_json, native
from pm10_modelado import ROOT, OUT as MODEL, sha, read_json, csv_save

PUBLIC = ROOT / 'web/public/datos/sprint-3'
DOWNLOADS = ROOT / 'web/public/descargas/sprint-3'
SLUG = {p: p.replace('.', '') for p in POLS}


def read_csv(path, **kwargs):
    return pd.read_csv(path, float_precision='round_trip', **kwargs)


def findings(periods, profiles, comparisons, coverage):
    rows = []
    def add(key, title, detail, figure, period, population, limitation, view):
        rows.append(dict(id=key, title=title, detail=detail, figure=figure, period=period, population=population, limitation=limitation, view=view))
    a = next(r for r in coverage if r['year'] == 2016 and r['variable'] == 'PM10')
    add('H01', 'Una rejilla completa puede ocultar mediciones ausentes', f"PM₁₀ tiene {a['usable_basic_hours']:,} / {a['expected_hours']:,} horas utilizables en 2016 ({a['usable_basic_pct']:.1f} %).",
        'historico-cobertura', '2016', 'Horas esperadas y PM10 del inventario', 'No permite sostener un cambio anual representativo.', 1)
    add('H02', 'PM₂.₅ empieza con una historia fragmentada', 'No hay mediciones numéricas de PM₂.₅ en 2015–2017. La cobertura mejora en 2022–2024.',
        'historico-cobertura', '2015–2024', 'Horas crudas PM2.5', 'Ausencia de mediciones no significa aire favorable; no se rellena.', 1)
    selected = [r for r in profiles if r['pollutant'] == 'PM10' and r['year'] == 0 and r['kind'] == 'hour' and r['mean'] is not None]
    top = max(selected, key=lambda r: r['mean'])
    add('H03', 'El perfil horario de PM₁₀ tiene un máximo matutino', f"La media observada más alta aparece a las {top['bin']:02d}:00: {top['mean']:.1f} µg/m³, con {top['n']:,} / {top['expected']:,} observaciones.",
        'historico-horas', '2015–2024', 'PM10 crudo observado, agrupado por hora', 'Mezcla años y estaciones con cobertura desigual; no identifica fuentes emisoras.', 1)
    pair = next(r for r in comparisons if r['year_a'] == 2023 and r['year_b'] == 2024 and r['pollutant'] == 'PM10' and r['month'] == 12)
    d = [next(r for r in periods if r['year'] == y and r['month'] == 12 and r['pollutant'] == 'PM10') for y in [2023, 2024]]
    add('H04', 'Diciembre de 2024 registra más días desfavorables de PM₁₀', f"{d[0]['bad']} / 31 frente a {d[1]['bad']} / 31 días Mala o peor. La media diaria pareada cambia {pair['change_pct']:+.1f} % ({pair['n']} / {pair['expected']} pares).",
        'comparacion-periodos', 'Diciembre 2023 y 2024', 'Fechas mes/día coincidentes con base diaria suficiente', 'Referencia retrospectiva de 2024; el pareamiento no controla meteorología ni actividades.', 2)
    metric_rows = read_csv(MODEL / 'metricas_globales.csv')
    errors = [float(metric_rows[(metric_rows.partition == 'test') & (metric_rows.model == 'HGB') & (metric_rows.horizon == h)].iloc[0].mae) for h in [1, 2, 3]]
    add('H05', 'C05 mejora el error global y aún subestima los picos', f'En 2024, MAE de {errors[0]:.2f}, {errors[1]:.2f} y {errors[2]:.2f} µg/m³ a +1, +2 y +3 h; subestimación en concentraciones altas.',
        'evaluacion-error', '2024', '6,225 orígenes comunes; 70.9 % de las horas del año', 'Evaluación retrospectiva; no acredita operación en tiempo real ni validez instrumental.', 5)
    episode = max([r for r in read_json(HIST / 'episodios.json') if r['pollutant'] == 'PM10'], key=lambda r: r['days'])
    add('H06', 'Una secuencia desfavorable cruza de 2021 a 2022', f"{episode['days']} días consecutivos de PM₁₀ Mala o peor: {episode['start']} a {episode['end']}.",
        'episodios-secuencia', f"{episode['start']} — {episode['end']}", 'Categorías de promedio diario PM10 con al menos 18 lecturas',
        'Criterio de episodio del proyecto y bandas retrospectivas; no demuestra una fuente o causa del evento.', 3)
    return rows


def export():
    manifest = read_json(HIST / 'manifiesto.json')
    for name, expected in manifest['files'].items():
        if sha(HIST / name) != expected: raise ValueError(f'Resultado histórico cambiado: {name}')
    freeze = read_json(MODEL / 'config_congelada.json')
    final = read_json(MODEL / 'evaluacion_final.json')
    if sha(MODEL / 'config_congelada.json') != final['freeze_sha256']: raise ValueError('C05 no está congelado')
    for name, expected in final['outputs_sha256'].items():
        if sha(MODEL / name) != expected: raise ValueError(f'Evidencia C05 modificada: {name}')
    PUBLIC.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    periods = read_json(HIST / 'periodos.json')
    profiles = read_json(HIST / 'perfiles.json')
    pairs = read_json(HIST / 'comparaciones.json')
    coverage = read_csv(ROOT / 'data/processed/sprint-3/cobertura_anual.csv').to_dict('records')
    monthly_coverage = read_csv(ROOT / 'data/processed/sprint-3/cobertura_mensual.csv').to_dict('records')
    hourly = read_csv(HIST / 'horario.csv', parse_dates=['DATE']).set_index('DATE')
    daily = read_csv(HIST / 'diario.csv', parse_dates=['DATE']).set_index('DATE')
    episodes = read_json(HIST / 'episodios.json')
    peaks = read_json(HIST / 'maximos_horarios.json')
    anomalies = read_csv(HIST / 'atipicos_horarios.csv')
    for p in POLS:
        save_json(PUBLIC / f'historico/{SLUG[p]}.json', {'periods': [r for r in periods if r['pollutant'] == p],
                  'profiles': [r for r in profiles if r['pollutant'] == p],
                  'coverage': [r for r in coverage if r['variable'] == p],
                  'monthlyCoverage': [r for r in monthly_coverage if r['variable'] == p]})
        save_json(PUBLIC / f'episodios/{SLUG[p]}.json', {'episodes': [r for r in episodes if r['pollutant'] == p],
                  'peaks': [r for r in peaks if r['pollutant'] == p],
                  'anomalies': anomalies[anomalies.pollutant == p].to_dict('records')})
    save_json(PUBLIC / 'cobertura.json', coverage)
    for a in range(2015, 2025):
        for b in range(a + 1, 2025):
            save_json(PUBLIC / f'comparaciones/{a}-{b}.json', [r for r in pairs if r['year_a'] == a and r['year_b'] == b])
    relations = read_json(HIST / 'meteorologia.json')
    meteo_points = read_csv(HIST / 'pares_meteorologicos.csv')
    for year in range(2015, 2025):
        for month in range(1, 13):
            h = hourly[(hourly.index.year == year) & (hourly.index.month == month)]
            save_json(PUBLIC / f'horas/{year}-{month:02d}.json', {'time': [t.isoformat() for t in h.index], 'values': {p: h[p].tolist() for p in hourly.columns}})
            d = daily[(daily.index.year == year) & (daily.index.month == month)]
            calendar_rows = []
            for time, row in d.iterrows():
                calendar_rows.append({'date': time.date().isoformat(),
                    'pollutants': {p: {'value': row[f'I_{p}'], 'exact': row[f'EXACT_{p}'], 'category': row[f'C_{p}'],
                                      'n': int(row[f'N_{p}']), 'indN': int(row[f'N_IND_{p}'])} for p in POLS},
                    'weather': {v: {'mean': row[f'M_{v}'], 'n': int(row[f'N_{v}'])} for v in METEO}})
            save_json(PUBLIC / f'calendario/{year}-{month:02d}.json', calendar_rows)
            rows = []
            for r in relations:
                if r['year'] != year or r['month'] != month: continue
                points = meteo_points[(meteo_points.year == year) & (meteo_points.month == month) &
                                      (meteo_points.pollutant == r['pollutant']) & (meteo_points.variable == r['variable'])]
                rows.append({**r, 'points': points[['date', 'x', 'y']].to_dict('records')})
            save_json(PUBLIC / f'meteorologia/{year}-{month:02d}.json', rows)
    metrics = {kind: read_csv(MODEL / f'metricas_{kind}.csv').to_dict('records') for kind in ['globales', 'mensuales', 'altas']}
    save_json(PUBLIC / 'metricas.json', metrics)
    predictions = {p: read_csv(MODEL / f'predicciones/test_{p}.csv') for p in ['HGB', 'persistencia', 'diaria']}
    first = predictions['HGB']
    for month in range(1, 13):
        origins = sorted(set(first.loc[pd.to_datetime(first.origin).dt.month == month, 'origin']))
        indexed = {model: frame.set_index(['origin', 'horizon']) for model, frame in predictions.items()}
        records = []
        for origin in origins:
            targets = [indexed['HGB'].loc[(origin, h)] for h in [1, 2, 3]]
            records.append({'origin': origin, 'target': [r.target_time for r in targets], 'observed': [r.observed for r in targets],
                            'models': {model: {'predicted': [frame.loc[(origin, h)].predicted for h in [1, 2, 3]],
                                               'error': [frame.loc[(origin, h)].signed_error for h in [1, 2, 3]]} for model, frame in indexed.items()}})
        save_json(PUBLIC / f'predicciones/2024-{month:02d}.json', records)
    for horizon in [1, 2, 3]:
        data = first[first.horizon == horizon]
        for month in range(13):
            part = data if month == 0 else data[pd.to_datetime(data.target_time).dt.month == month]
            save_json(PUBLIC / f'evaluacion/h{horizon}-m{month}.json', part[['origin', 'target_time', 'observed', 'predicted', 'signed_error']].to_dict('records'))
    found = findings(periods, profiles, pairs, coverage)
    save_json(HIST / 'hallazgos.json', found)
    csv_save(pd.DataFrame(found), HIST / 'hallazgos.csv')
    downloads = []
    for source, name in [(HIST / n, n) for n in ['horario.csv', 'diario.csv', 'periodos.csv', 'perfiles.csv', 'episodios.csv', 'atipicos_horarios.csv', 'meteorologia.csv', 'pares_meteorologicos.csv', 'hallazgos.csv']]+[
        (ROOT / 'config/fuentes_sprint3.json', 'fuentes.json'), (ROOT / 'docs/sprints/sprint-3/integracion/CRITERIOS_HISTORICOS.md', 'criterios.md'),
        *[(MODEL / f'metricas_{kind}.csv', f'modelo_metricas_{kind}.csv') for kind in ['globales', 'mensuales', 'altas']],
        *[(MODEL / f'predicciones/test_{model}.csv', f'modelo_2024_{model}.csv') for model in predictions]]:
        target = DOWNLOADS / name
        shutil.copyfile(source, target)
        downloads.append({'name': name, 'url': '/descargas/sprint-3/' + name, 'sha256': sha(source), 'bytes': source.stat().st_size})
    summary = {'schema': 'academia-miravalle-v1', 'years': list(range(2015, 2025)), 'findings': found,
               'pollutants': [{'key': p, 'slug': SLUG[p], 'label': N.LABELS.get(p, p), 'unit': N.UNITS.get(p, 'ppm'),
                               'statistic': 'Promedio diario de partículas (24 h)' if p.startswith('PM') else 'Máximo diario del promedio móvil de 8 h' if p == 'CO' else 'Máximo horario del día' if p in N.POLS else 'Media diaria descriptiva (proyecto)',
                               'categoryApplicable': p in N.POLS} for p in POLS],
               'categories': [{'code': i, 'name': n, 'color': c, 'ink': ink} for i, (n, c, ink) in enumerate(zip(N.CATS,
                              ['#00e400', '#ffff00', '#ff7e00', '#ff0000', '#8f3f97'], ['#0b1f0b', '#262400', '#2a1400', '#1f0000', '#ffffff']))],
               'model': {'id': 'C05', 'n': 6225, 'expected': 8784, 'coverage': 100 * 6225 / 8784, 'rawN': 8051,
                         'threshold': freeze['high_diagnostic']['train_p90'], 'features': len(freeze['features']),
                         'parameters': freeze['selected']['parameters'], 'freezeSha256': final['freeze_sha256'],
                         'metrics': [r for r in metrics['globales'] if r['partition'] == 'test']},
               'sources': read_json(ROOT / 'config/fuentes_sprint3.json')['fuentes'], 'downloads': downloads,
               'warnings': ['Referencia retrospectiva común de 2024; no reconstruye avisos oficiales de cada año.',
                            'Cobertura y criterios adicionales del proyecto no acreditan representatividad ni calibración.',
                            'SO₂ 2023 excluido por falta de calibración documentada; NO₂ 2024 exploratorio.',
                            'La predicción es una evaluación retrospectiva de 2024. No se convierte directamente en categoría.']}
    save_json(ROOT / 'web/data/academia.json', summary)
    save_json(PUBLIC / 'resumen.json', summary)
    print('Contrato exportado: resumen', (ROOT / 'web/data/academia.json').stat().st_size, 'bytes;', len(list(PUBLIC.rglob('*.json'))), 'consultas JSON; C05 sin cambios.', flush=True)


if __name__ == '__main__':
    export()
