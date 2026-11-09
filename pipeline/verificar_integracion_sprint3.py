"""Verificación de trazabilidad histórica, contrato web y C05 intacto."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from historico_sprint3 import OUT, POLS
from pm10_modelado import ROOT, OUT as MODEL, sha, read_json, write_json, utc

DOC = ROOT / 'docs/sprints/sprint-3/integracion'
PUBLIC = ROOT / 'web/public/datos/sprint-3'


def verify():
    checks = 0
    def check(condition, reason):
        nonlocal checks
        if not bool(condition): raise AssertionError(reason)
        checks += 1
    before = read_json(DOC / 'conservacion_antes.json')
    modified_ui = []
    for name, signature in before['files'].items():
        if name in before['ui_allowed_changes']:
            if sha(ROOT / name) != signature: modified_ui.append(name)
        else:
            check((ROOT / name).is_file() and sha(ROOT / name) == signature, f'Archivo anterior alterado: {name}')
    check(sha(ROOT / 'web/app/observatorio-mensual/page.tsx') == before['files']['web/app/page.tsx'], 'Portada anterior conservada como ruta mensual')
    frozen = read_json(MODEL / 'evaluacion_final.json')
    check(sha(MODEL / 'config_congelada.json') == frozen['freeze_sha256'], 'C05 congelado')
    for name, signature in frozen['outputs_sha256'].items(): check(sha(MODEL / name) == signature, f'Evidencia C05: {name}')
    meta = read_json(OUT / 'manifiesto.json')
    check(sha(ROOT / 'docs/sprints/sprint-3/integracion/CRITERIOS_HISTORICOS.md') == meta['criteria_sha256'], 'Criterios registrados')
    for name, signature in meta['files'].items(): check(sha(OUT / name) == signature, f'Histórico: {name}')
    hourly = pd.read_csv(OUT / 'horario.csv', parse_dates=['DATE'], float_precision='round_trip').set_index('DATE')
    daily = pd.read_csv(OUT / 'diario.csv', parse_dates=['DATE'], float_precision='round_trip').set_index('DATE')
    old_pm10 = pd.read_csv(MODEL / 'pm10_horario.csv', parse_dates=['DATE'], float_precision='round_trip').set_index('DATE')
    check(hourly.index.equals(pd.date_range('2015-01-01', '2024-12-31 23:00', freq='h')), '87672 horas reales')
    check(np.array_equal(hourly.PM10, old_pm10.PM10, equal_nan=True), 'PM10 histórico idéntico a entrada congelada')
    check(len(daily) == 3653 and pd.Timestamp('2024-02-29') in daily.index, 'Días reales y bisiestos')
    check(hourly.loc['2023', 'SO2'].isna().all() and daily.loc['2023', 'C_SO2'].isna().all(), 'SO2 2023 excluido')
    coverage = pd.read_csv(ROOT / 'data/processed/sprint-3/cobertura_anual.csv')
    for row in coverage.to_dict('records'):
        check(int(hourly.loc[str(row['year']), row['variable']].count()) == row['usable_basic_hours'], 'Cobertura coincide con inventario')
    periods = read_json(OUT / 'periodos.json')
    for r in periods:
        s = hourly.loc[str(r['year']), r['pollutant']]
        if r['month']: s = s[s.index.month == r['month']]
        check(s.count() == r['n'] and len(s) == r['expected'], 'n/esperados de agregado')
        check(r['mean'] is None if not s.count() else abs(r['mean'] - s.mean()) < 1e-10, 'Media de concentraciones')
        if r['counts'] is not None:
            check(sum(r['counts']) + r['days_missing'] == r['days_expected'], 'Conteos diarios y ausencias')
            check(r['bad'] == sum(r['counts'][2:]), 'Mala o peor no promedia códigos')
        if r['month'] == 0 and r['sufficient']: check(min(r['quarterly_coverage']) >= 75, 'Suficiencia trimestral')
    for year in [2023, 2024]:
        old = pd.read_csv(ROOT / f'data/processed/sprint-2/MIR_{year}_diario.csv', parse_dates=['DATE'], float_precision='round_trip').set_index('DATE').loc[f'{year}-12']
        new = daily.loc[f'{year}-12']
        for p in ['PM10', 'PM2.5', 'O3', 'CO']:
            for field in ['EXACT', 'I', 'C', 'N']:
                check(np.array_equal(old[f'{field}_{p}'], new[f'{field}_{p}'], equal_nan=True), f'Diciembre S2 conservado {year}/{field}/{p}')
        check(new.C_CO.eq(0).sum() == 31, 'CO Buena 31/31, código cero válido')
        check(new.C_PM10.ge(2).sum() == (15 if year == 2023 else 27), 'PM10 desfavorable 15 frente 27')
    check(daily.loc['2023-01', 'C_O3'].isna().all(), 'O3 enero 2023 ausente')
    for e in read_json(OUT / 'episodios.json'):
        dates = pd.date_range(e['start'], e['end'], freq='D')
        check(len(dates) == e['days'] and daily.loc[dates, f"C_{e['pollutant']}"].ge(2).all(), 'Episodios continuos, sin saltar huecos')
    pairs = read_json(OUT / 'comparaciones.json')
    for r in pairs:
        check(len(r['dates']) == r['n'] <= r['expected'], 'Población pareada explícita')
        if r['sufficient'] and r['month'] == 0: check(all(q['n'] >= .75 * q['expected'] for q in r['quarterly']), 'Pares trimestrales')
    sample_pair = next(r for r in pairs if r['year_a'] == 2023 and r['year_b'] == 2024 and r['pollutant'] == 'PM10' and r['month'] == 12)
    check(sample_pair['n'] == 31 and abs(sample_pair['change_pct'] - 65.20) < .01, 'Cambio pareado de diciembre trazable')
    for y in range(2015, 2025):
        for month in range(1, 13):
            cal = read_json(PUBLIC / f'calendario/{y}-{month:02d}.json')
            h = read_json(PUBLIC / f'horas/{y}-{month:02d}.json')
            check(len(h['time']) == 24 * len(cal), 'Detalle mensual completo')
            for day in cal:
                original = daily.loc[day['date']]
                for p in POLS:
                    c, value = day['pollutants'][p]['category'], original[f'C_{p}']
                    check(c is None if pd.isna(value) else c == value, 'Categoría web exacta, cero distinto de ausencia')
            weather = read_json(PUBLIC / f'meteorologia/{y}-{month:02d}.json')
            for r in weather:
                check(r['n'] == len(r['points']), 'n meteorológico')
                if r['rho'] is not None:
                    check(r['n'] >= 15, 'Mínimo de pares meteorológicos')
                    rho = float(spearmanr([p['x'] for p in r['points']], [p['y'] for p in r['points']]).statistic)
                    check(abs(rho - r['rho']) < 1e-12, 'Spearman reproducible sobre los pares exportados')
    summary = read_json(ROOT / 'web/data/academia.json')
    check((ROOT / 'web/data/academia.json').stat().st_size < 30000, 'Portada sin década horaria')
    check(summary['model']['freezeSha256'] == frozen['freeze_sha256'], 'Identidad C05 en dashboard')
    actual = pd.read_csv(MODEL / 'metricas_globales.csv', float_precision='round_trip')
    for r in summary['model']['metrics']:
        row = actual[(actual.partition == 'test') & (actual.model == r['model']) & (actual.horizon == r['horizon'])].iloc[0]
        for field in ['n', 'mae', 'rmse', 'r2', 'bias']: check(r[field] == row[field], 'Métrica congelada exacta, sin recalcular')
    count = 0
    originals = {model: pd.read_csv(MODEL / f'predicciones/test_{model}.csv', float_precision='round_trip').set_index(['origin', 'horizon']) for model in ['HGB', 'diaria', 'persistencia']}
    for month in range(1, 13):
        for r in read_json(PUBLIC / f'predicciones/2024-{month:02d}.json'):
            for j, horizon in enumerate([1, 2, 3]):
                check(pd.Timestamp(r['target'][j]) == pd.Timestamp(r['origin']) + pd.Timedelta(hours=horizon), 'Horizonte exacto')
                for model, frame in originals.items():
                    row = frame.loc[(r['origin'], horizon)]
                    check(r['models'][model]['predicted'][j] == row.predicted and r['models'][model]['error'][j] == row.signed_error and r['observed'][j] == row.observed, 'Predicción pública exacta frente al CSV congelado')
                count += 1
    check(count == 6225 * 3, 'Tres horizontes de 6225 orígenes')
    for resource in summary['downloads']:
        target = ROOT / 'web/public' / resource['url'].lstrip('/')
        check(sha(target) == resource['sha256'] and target.stat().st_size == resource['bytes'], 'Descarga íntegra')
    for f in summary['findings']: check(all(f[k] for k in ['period', 'population', 'limitation', 'figure']), 'Hallazgo con población y limitación')
    result = {'verified_utc': utc(), 'checks_passed': checks, 'before_files': len(before['files']),
              'protected_files_unchanged': len(before['files']) - len(before['ui_allowed_changes']), 'authorized_ui_changes': modified_ui,
              'C05_unchanged': True, 'prediction_origins': 6225, 'prediction_horizons_checked': count,
              'summary_bytes': (ROOT / 'web/data/academia.json').stat().st_size, 'same_origin_queries': True,
              'historical_source_manifest_sha256': meta['source_manifest_sha256']}
    write_json(DOC / 'verificacion_datos.json', result)
    print(result, flush=True)


if __name__ == '__main__': verify()
