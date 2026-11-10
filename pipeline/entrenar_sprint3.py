"""Selección con 2023; congelación; reajuste y evaluación retrospectiva 2024."""
from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from pm10_modelado import (ROOT, OUT, PROTOCOL, HORIZONS, audit, baselines, calculate_metrics,
                          csv_save, metrics_tables, read_json, select_key, sha, utc, write_json)


def load_data(out):
    data = read_json(out / 'datos_congelados.json')
    if data['protocol_sha256'] != sha(PROTOCOL):
        raise ValueError('El protocolo cambió después de preparar las muestras')
    for name, signature in data['files_sha256'].items():
        if sha(out / name) != signature:
            raise ValueError(f'Datos modificados: {name}')
    origins = pd.read_csv(out / 'origenes.csv', parse_dates=['origin', 'target_1', 'target_2', 'target_3'])
    x = np.load(out / 'features.npy', allow_pickle=False)
    y = np.load(out / 'targets.npy', allow_pickle=False)
    if x.shape != (len(origins), len(data['features'])) or y.shape != (len(origins), 3):
        raise ValueError('Dimensiones del contrato incorrectas')
    return data, origins, x, y


def fit_direct(x, y, parameters):
    estimators = {}
    for column, horizon in enumerate(HORIZONS):
        estimator = HistGradientBoostingRegressor(**parameters)
        estimator.fit(x, y[:, column])
        if estimator.do_early_stopping_ or estimator.n_iter_ != parameters['max_iter']:
            raise ValueError('Se alteró el número de iteraciones prefijado')
        estimators[horizon] = estimator
    return estimators


def predict_direct(estimators, x):
    result = np.column_stack([estimators[h].predict(x) for h in HORIZONS])
    if not np.isfinite(result).all():
        raise ValueError('Predicción no finita; no eliminar ni imputar filas')
    return result


def save_models(out, stage, estimators, data, parameters, train_origins):
    folder = out / 'modelos' / stage
    folder.mkdir(parents=True, exist_ok=True)
    for h, estimator in estimators.items():
        artifact = {'schema': 'mir-pm10-directo-v1', 'horizon': h, 'unit': 'µg/m³',
                    'estimator': estimator, 'features': data['features'], 'parameters': parameters,
                    'protocol_sha256': data['protocol_sha256'], 'train_n': len(train_origins),
                    'first_origin': train_origins.origin.min().isoformat(), 'last_origin': train_origins.origin.max().isoformat(),
                    'last_target': train_origins.target_3.max().isoformat(), 'fit_stage': stage,
                    'sklearn_version': importlib.metadata.version('scikit-learn')}
        joblib.dump(artifact, folder / f'pm10_h{h}.joblib', compress=3)


def save_predictions(out, meta, y, predictions, part, fit_period):
    folder = out / 'predicciones'
    folder.mkdir(parents=True, exist_ok=True)
    for model, array in predictions.items():
        frames = []
        for column, h in enumerate(HORIZONS):
            frames.append(pd.DataFrame({'sample_id': meta.sample_id.to_numpy(), 'origin': meta.origin.to_numpy(),
                                        'target_time': meta[f'target_{h}'].to_numpy(), 'horizon': h,
                                        'observed': y[:, column], 'predicted': array[:, column],
                                        'signed_error': array[:, column] - y[:, column], 'model': model,
                                        'partition': part, 'fit_period': fit_period if model == 'HGB' else 'sin_ajuste'}))
        csv_save(pd.concat(frames, ignore_index=True), folder / f'{part}_{model}.csv')


def select(out=OUT):
    out = Path(out)
    if (out / 'config_congelada.json').exists() or (out / 'evaluacion_final.json').exists():
        raise ValueError('Selección ya congelada: no reabrir búsqueda después de consultar 2024')
    protocol = read_json(PROTOCOL)
    data, meta, x, y = load_data(out)
    train = (meta.partition.eq('train') & meta.included).to_numpy()
    val = (meta.partition.eq('validation') & meta.included).to_numpy()
    if not (meta.loc[train].target_3 < '2023-01-01').all() or not (meta.loc[val].target_3 < '2024-01-01').all():
        raise ValueError('Objetivos que cruzan fronteras temporales')
    if not train.any() or not val.any():
        raise ValueError('Partición vacía')
    audit(out, 'selection_started', train_n=int(train.sum()), validation_n=int(val.sum()), test_metrics_accessed=False)
    ranking, horizon_scores = [], []
    winner_key, winner_models, winner = None, None, None
    with threadpool_limits(limits=protocol['threads']):
        for candidate in protocol['candidates']:
            params = {**protocol['fixed_parameters'], **{k: v for k, v in candidate.items() if k != 'id'}}
            start = time.perf_counter()
            models = fit_direct(x[train], y[train], params)
            pred = predict_direct(models, x[val])
            errors = []
            for j, h in enumerate(HORIZONS):
                result = calculate_metrics(y[val, j], pred[:, j])
                horizon_scores.append({'candidate': candidate['id'], 'partition': 'validation', 'horizon': h, **result})
                errors.append(result['mae'])
            score = float(np.mean(errors))
            ranking.append({**candidate, 'mean_mae': score, 'mae_h1': errors[0], 'mae_h2': errors[1], 'mae_h3': errors[2],
                            'fit_seconds': time.perf_counter() - start})
            key = select_key(candidate, score)
            if winner_key is None or key < winner_key:
                winner_key, winner_models, winner = key, models, {**candidate, 'mean_mae': score, 'parameters': params}
            print(f"{candidate['id']}: MAE validación medio={score:.6f} h1/h2/h3={errors}", flush=True)
        ordered = sorted(ranking, key=lambda row: select_key(row, row['mean_mae']))
        for rank, row in enumerate(ordered, 1):
            row['rank'] = rank
        csv_save(pd.DataFrame(ordered), out / 'ranking_validacion.csv')
        csv_save(pd.DataFrame(horizon_scores), out / 'busqueda_metricas_2023.csv')
        save_models(out, 'desarrollo', winner_models, data, winner['parameters'], meta.loc[train])
        for part, mask in [('train', train), ('validation', val)]:
            preds = {**baselines(x[mask], data['features']), 'HGB': predict_direct(winner_models, x[mask])}
            save_predictions(out, meta.loc[mask], y[mask], preds, part, '2015-2022')
    code = ['pipeline/pm10_modelado.py', 'pipeline/preparar_modelado_sprint3.py', 'pipeline/entrenar_sprint3.py']
    frozen = {'frozen_utc': utc(), 'protocol_sha256': sha(PROTOCOL), 'data_metadata_sha256': sha(out / 'datos_congelados.json'),
              'selected': winner, 'features': data['features'], 'high_diagnostic': data['high_diagnostic'],
              'selection_rule': protocol['selection'], 'test_metrics_accessed': False,
              'code_sha256': {name: sha(ROOT / name) for name in code},
              'packages': {name: importlib.metadata.version(name) for name in ['numpy', 'pandas', 'scipy', 'scikit-learn', 'joblib', 'threadpoolctl']}}
    write_json(out / 'config_congelada.json', frozen, exclusive=True)
    audit(out, 'selection_frozen', selected=winner['id'], freeze_sha256=sha(out / 'config_congelada.json'), mean_mae_2023=winner['mean_mae'])
    print('Congelado:', winner['id'], 'Todavía no se calcularon métricas predictivas de 2024.', flush=True)


def evaluate(out=OUT):
    out = Path(out)
    if not (out / 'config_congelada.json').exists():
        raise ValueError('Se requiere selección congelada antes de evaluar 2024')
    if (out / 'evaluacion_final.json').exists():
        raise ValueError('Evaluación final ya registrada; no modificar decisiones. Reproducir en --out separado.')
    freeze = read_json(out / 'config_congelada.json')
    signature = sha(out / 'config_congelada.json')
    if sha(PROTOCOL) != freeze['protocol_sha256'] or sha(out / 'datos_congelados.json') != freeze['data_metadata_sha256']:
        raise ValueError('Cambió la configuración congelada')
    for name, expected in freeze['code_sha256'].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f'Código cambiado después de la selección: {name}')
    data, meta, x, y = load_data(out)
    fit = meta.refit_included.to_numpy(dtype=bool)
    test = (meta.partition.eq('test') & meta.included).to_numpy()
    if not (meta.loc[fit].target_3 < '2024-01-01').all():
        raise ValueError('El reajuste ve etiquetas de evaluación')
    audit(out, 'refit_started', n=int(fit.sum()), freeze_sha256=signature, test_metrics_accessed=False)
    with threadpool_limits(limits=read_json(PROTOCOL)['threads']):
        models = fit_direct(x[fit], y[fit], freeze['selected']['parameters'])
        save_models(out, 'reajuste', models, data, freeze['selected']['parameters'], meta.loc[fit])
        audit(out, 'refit_finished', last_train_target=meta.loc[fit].target_3.max().isoformat())
        audit(out, 'test_predictions_started', freeze_sha256=signature, n=int(test.sum()))
        predictions = {**baselines(x[test], data['features']), 'HGB': predict_direct(models, x[test])}
        save_predictions(out, meta.loc[test], y[test], predictions, 'test', '2015-2023')
    frames = [pd.read_csv(path, float_precision='round_trip') for path in sorted((out / 'predicciones').glob('*.csv'))]
    global_metrics, monthly, high = metrics_tables(frames, freeze['high_diagnostic']['train_p90'])
    csv_save(global_metrics, out / 'metricas_globales.csv')
    csv_save(monthly, out / 'metricas_mensuales.csv')
    csv_save(high, out / 'metricas_altas.csv')
    result = {'evaluated_utc': utc(), 'freeze_sha256': signature, 'protocol_sha256': sha(PROTOCOL),
              'selected': freeze['selected']['id'], 'refit_n': int(fit.sum()), 'test_n_per_model_horizon': int(test.sum()),
              'recovered_internal_boundary_windows': int((fit & ~meta.included.to_numpy(dtype=bool)).sum()),
              'negative_predictions': {model: int((array < 0).sum()) for model, array in predictions.items()},
              'no_reselection_after_test': True,
              'outputs_sha256': {path.relative_to(out).as_posix(): sha(path) for path in sorted(out.rglob('*'))
                                 if path.is_file() and path.name not in ('evaluacion_final.json', 'eventos.jsonl')}}
    write_json(out / 'evaluacion_final.json', result, exclusive=True)
    audit(out, 'test_evaluation_finished', freeze_sha256=signature, decision_changes=0)
    print(global_metrics[global_metrics.partition.eq('test')].to_string(index=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['seleccionar', 'evaluar'])
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()
    (select if args.stage == 'seleccionar' else evaluate)(args.out)
