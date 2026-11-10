"""Comprueba muestras, modelos serializados, métricas, causalidad y conservación."""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from threadpoolctl import threadpool_limits

from pm10_modelado import (ROOT, OUT, DOCS, PROTOCOL, causal_features, predict_at,
                          read_json, select_key, sha, utc, write_json)


def verify(out=OUT):
    out = Path(out)
    count = 0

    def check(condition, message):
        nonlocal count
        if not bool(condition):
            raise AssertionError(message)
        count += 1

    protocol = read_json(PROTOCOL)
    data = read_json(out / 'datos_congelados.json')
    freeze = read_json(out / 'config_congelada.json')
    final = read_json(out / 'evaluacion_final.json')
    check(sha(PROTOCOL) == data['protocol_sha256'] == freeze['protocol_sha256'] == final['protocol_sha256'], 'Protocolo inmutable')
    check(sha(out / 'config_congelada.json') == final['freeze_sha256'], 'Congelación inmutable')
    for name, expected in final['outputs_sha256'].items():
        check(sha(out / name) == expected, f'Integridad del resultado {name}')
    for name, expected in freeze['code_sha256'].items():
        check(sha(ROOT / name) == expected, f'Código posterior al entrenamiento {name}')
    baseline = read_json(DOCS / 'conservacion_antes.json')
    for name, expected in baseline['files'].items():
        check((ROOT / name).is_file() and sha(ROOT / name) == expected, f'Conservación de {name}')
    hourly = pd.read_csv(out / 'pm10_horario.csv', parse_dates=['DATE'], float_precision='round_trip').set_index('DATE')
    series = hourly.PM10
    check(series.index.equals(pd.date_range('2015-01-01', '2024-12-31 23:00', freq='h')), 'Rejilla horaria real')
    check(int(series.notna().sum()) == 69000, 'Horas utilizables del inventario')
    origins = pd.read_csv(out / 'origenes.csv', parse_dates=['origin', 'target_1', 'target_2', 'target_3'])
    x = np.load(out / 'features.npy', allow_pickle=False)
    y = np.load(out / 'targets.npy', allow_pickle=False)
    good = series.notna().to_numpy(dtype=np.int64)
    strict = np.convolve(good, np.ones(27, dtype=np.int64), mode='valid') == 27
    expected_origins = series.index[23:-3][strict]
    check(expected_origins.equals(pd.DatetimeIndex(origins.origin)), 'Conciliación independiente de ventanas consecutivas')
    check(len(origins) == 53608 and int(origins.included.sum()) == 53605, 'Ventanas iniciales y aceptadas')
    check(np.array_equal(x, causal_features(series).loc[origins.origin].to_numpy()), 'Características congeladas reproducibles')
    for column, horizon in enumerate((1, 2, 3)):
        check((origins[f'target_{horizon}'] == origins.origin + pd.Timedelta(hours=horizon)).all(), 'Fecha objetivo exacta')
        check(np.array_equal(y[:, column], series.reindex(origins[f'target_{horizon}']).to_numpy()), 'Objetivos originales sin transformación')
    monthly_ledger = pd.read_csv(out / 'conciliacion_mensual.csv')
    check(monthly_ledger.initial_window.sum() == 53608, 'Suma mensual inicial')
    check(monthly_ledger.boundary_excluded.sum() == 3 and monthly_ledger.included.sum() == 53605, 'Exclusiones mensuales')
    check(monthly_ledger.expected_origins.sum() == 87672, 'Denominadores completos por mes')
    threshold = float(np.quantile(series.loc[:'2022-12-31 23:00'].dropna().to_numpy(), .9, method='linear'))
    check(threshold == data['high_diagnostic']['train_p90'] == freeze['high_diagnostic']['train_p90'], 'Umbral solo entrenamiento')
    ranking = pd.read_csv(out / 'ranking_validacion.csv', float_precision='round_trip')
    winner = min(ranking.to_dict('records'), key=lambda row: select_key(row, row['mean_mae']))
    check(winner['id'] == freeze['selected']['id'], 'Selección según criterio prefijado')
    check(set(ranking.id) == {c['id'] for c in protocol['candidates']}, 'Ocho configuraciones previamente registradas')
    check(not freeze['selected']['parameters']['early_stopping'], 'Sin partición interna aleatoria')
    events = [__import__('json').loads(line) for line in (out / 'eventos.jsonl').read_text(encoding='utf-8').splitlines()]
    positions = {row['event']: i for i, row in enumerate(events)}
    check(positions['selection_frozen'] < positions['refit_started'] < positions['test_predictions_started'], 'Congelación anterior a test')
    check(protocol['registered_utc'] < events[positions['selection_started']]['utc'], 'Protocolo anterior a búsqueda')
    check(freeze['frozen_utc'] < final['evaluated_utc'], 'Cronología de evaluación')
    global_metrics = pd.read_csv(out / 'metricas_globales.csv', keep_default_na=False)
    monthly_metrics = pd.read_csv(out / 'metricas_mensuales.csv', keep_default_na=False)
    high_metrics = pd.read_csv(out / 'metricas_altas.csv', keep_default_na=False)
    year_month_path = out / 'metricas_anio_mes.csv'
    year_month_metrics = pd.read_csv(year_month_path, keep_default_na=False) if year_month_path.exists() else None
    artifacts = {}
    for stage in ('desarrollo', 'reajuste'):
        artifacts[stage] = {h: joblib.load(out / f'modelos/{stage}/pm10_h{h}.joblib') for h in (1, 2, 3)}
        for h, model in artifacts[stage].items():
            check(model['features'] == data['features'], 'Características del modelo serializado')
            check(model['estimator'].get_params() == {**model['estimator'].get_params(), **freeze['selected']['parameters']}, 'Parámetros congelados')
            check(model['estimator'].n_iter_ == freeze['selected']['parameters']['max_iter'] and not model['estimator'].do_early_stopping_, 'Iteraciones fijas')
            cutoff = '2023-01-01' if stage == 'desarrollo' else '2024-01-01'
            check(pd.Timestamp(model['last_target']) < pd.Timestamp(cutoff), 'Sin objetivos del periodo reservado')

    def metric_check(row, ytrue, ypred):
        n = len(ytrue)
        check(int(row['n']) == n, 'n de la métrica')
        if n:
            check(abs(float(row['mae']) - mean_absolute_error(ytrue, ypred)) < 1e-9, 'MAE independiente')
            check(abs(float(row['rmse']) - np.sqrt(mean_squared_error(ytrue, ypred))) < 1e-9, 'RMSE independiente')
            check(abs(float(row['bias']) - float(np.mean(ypred - ytrue))) < 1e-9, 'Signo del error')
        else:
            check(row['mae'] == row['rmse'] == '', 'Sin muestras no es error cero')
        if n >= 2 and np.var(ytrue) > 0:
            check(abs(float(row['r2']) - r2_score(ytrue, ypred)) < 1e-9, 'R² independiente, incluidos negativos')
        else:
            check(row['r2'] == '' and row['r2_reason'] != '', 'R² no calculable explícito')

    rows_checked = 0
    with threadpool_limits(limits=protocol['threads']):
        for part in ('train', 'validation', 'test'):
            expected = origins[(origins.partition == part) & origins.included]
            for model in ('persistencia', 'diaria', 'HGB'):
                pred = pd.read_csv(out / f'predicciones/{part}_{model}.csv', parse_dates=['origin', 'target_time'], float_precision='round_trip')
                for h in (1, 2, 3):
                    group = pred[pred.horizon == h]
                    check(group.sample_id.tolist() == expected.sample_id.tolist(), 'Mismos orígenes entre modelos y horizontes')
                    check((group.target_time == group.origin + pd.Timedelta(hours=h)).all(), 'Etiquetas temporales de predicciones')
                    observed = series.reindex(group.target_time).to_numpy()
                    check(np.array_equal(observed, group.observed.to_numpy()), 'Observado original')
                    if model == 'persistencia':
                        target_pred = series.reindex(group.origin).to_numpy()
                    elif model == 'diaria':
                        target_pred = series.reindex(group.target_time - pd.Timedelta(hours=24)).to_numpy()
                    else:
                        stage = 'reajuste' if part == 'test' else 'desarrollo'
                        target_pred = artifacts[stage][h]['estimator'].predict(x[group.sample_id])
                    check(np.allclose(target_pred, group.predicted.to_numpy(), rtol=0, atol=1e-10), 'Reproducción desde artefacto o referencia exacta')
                    check(np.allclose(group.signed_error, group.predicted - group.observed, rtol=0, atol=1e-10), 'Error firmado registrado')
                    tags = global_metrics[(global_metrics.partition == part) & (global_metrics.model == model) & (global_metrics.horizon == h)].iloc[0]
                    metric_check(tags, observed, group.predicted.to_numpy())
                    for month in range(1, 13):
                        sub = group[group.target_time.dt.month == month]
                        row = monthly_metrics[(monthly_metrics.partition == part) & (monthly_metrics.model == model) & (monthly_metrics.horizon == h) & (monthly_metrics.month == month)].iloc[0]
                        metric_check(row, sub.observed.to_numpy(), sub.predicted.to_numpy())
                    if year_month_metrics is not None:
                        years = range(2015, 2023) if part == 'train' else [2023 if part == 'validation' else 2024]
                        summed_n = 0
                        for year in years:
                            for month in range(1, 13):
                                sub = group[(group.target_time.dt.year == year) & (group.target_time.dt.month == month)]
                                row = year_month_metrics[(year_month_metrics.partition == part) & (year_month_metrics.model == model) &
                                                         (year_month_metrics.horizon == h) & (year_month_metrics.target_year == year) &
                                                         (year_month_metrics.target_month == month)].iloc[0]
                                metric_check(row, sub.observed.to_numpy(), sub.predicted.to_numpy())
                                summed_n += int(row['n'])
                        check(summed_n == len(group), 'Conciliación de todos los años/meses')
                    high = group[group.observed >= threshold]
                    row = high_metrics[(high_metrics.partition == part) & (high_metrics.model == model) & (high_metrics.horizon == h) & (high_metrics.month == 0)].iloc[0]
                    metric_check(row, high.observed.to_numpy(), high.predicted.to_numpy())
                    rows_checked += len(group)
            # API de inferencia real con solo las últimas 24 horas y sin etiquetas.
            for i in [0, len(expected) // 2, len(expected) - 1]:
                sample = expected.iloc[i]
                history = series.loc[:sample.origin].iloc[-24:]
                stage = 'reajuste' if part == 'test' else 'desarrollo'
                actual = predict_at(artifacts[stage], history, sample.origin)
                mutated = pd.concat([history, pd.Series([1e12], index=[sample.origin + pd.Timedelta(hours=1)])])
                no_future = predict_at(artifacts[stage], mutated, sample.origin)
                for h in (1, 2, 3):
                    direct = artifacts[stage][h]['estimator'].predict(x[[sample.sample_id]])[0]
                    check(actual[h] == no_future[h] == direct, 'Inferencia independiente de información futura')
    result = {'verified_utc': utc(), 'checks_passed': count, 'prediction_rows_checked': rows_checked,
              'old_files_verified': len(baseline['files']), 'old_files_changed': [],
              'model_artifacts_reloaded': 6, 'same_origins_all_models_and_horizons': True,
              'threshold_train_p90': threshold, 'protocol_sha256': sha(PROTOCOL), 'freeze_sha256': sha(out / 'config_congelada.json'),
              'year_month_metric_rows_verified': len(year_month_metrics) if year_month_metrics is not None else 0}
    write_json(out / 'verificacion_modelado.json', result)
    print(result, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=OUT)
    verify(parser.parse_args().out)
