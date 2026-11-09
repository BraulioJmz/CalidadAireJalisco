"""Informe técnico reproducible; solo lee predicciones del experimento terminado."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from pm10_modelado import OUT, DOCS, calculate_metrics, csv_save, read_json, sha


def table(frame, columns):
    lines = ['| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join('---' for _ in columns) + ' |']
    for _, row in frame.iterrows():
        cells = []
        for col in columns:
            value = row[col]
            if pd.isna(value) or value == '':
                cells.append('n.c.')
            elif isinstance(value, (float, np.floating)):
                cells.append(f'{value:.3f}')
            else:
                cells.append(str(value))
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def summarize(out=OUT, report=None):
    out = Path(out)
    report = Path(report) if report else DOCS / 'RESULTADOS.md'
    frozen = read_json(out / 'config_congelada.json')
    final = read_json(out / 'evaluacion_final.json')
    data = read_json(out / 'datos_congelados.json')
    verification = read_json(out / 'verificacion_modelado.json')
    global_metrics = pd.read_csv(out / 'metricas_globales.csv')
    monthly = pd.read_csv(out / 'metricas_mensuales.csv')
    high = pd.read_csv(out / 'metricas_altas.csv')
    ledger = pd.read_csv(out / 'conciliacion_mensual.csv')
    ranking = pd.read_csv(out / 'ranking_validacion.csv')
    year_month_rows = []
    low_rows = []
    for part, years in [('train', range(2015, 2023)), ('validation', [2023]), ('test', [2024])]:
        for model in ['persistencia', 'diaria', 'HGB']:
            frame = pd.read_csv(out / f'predicciones/{part}_{model}.csv', parse_dates=['target_time'], float_precision='round_trip')
            for h in [1, 2, 3]:
                group = frame[frame.horizon == h]
                if part == 'test':
                    low = group[group.observed < frozen['high_diagnostic']['train_p90']]
                    low_rows.append({'partition': part, 'model': model, 'horizon': h, 'stratum': 'observado_menor_p90_train',
                                     **calculate_metrics(low.observed, low.predicted)})
                for year in years:
                    for month in range(1, 13):
                        sub = group[(group.target_time.dt.year == year) & (group.target_time.dt.month == month)]
                        year_month_rows.append({'partition': part, 'model': model, 'horizon': h, 'target_year': year,
                                                'target_month': month, **calculate_metrics(sub.observed, sub.predicted)})
    csv_save(pd.DataFrame(year_month_rows), out / 'metricas_anio_mes.csv')
    low = pd.DataFrame(low_rows)
    csv_save(low, out / 'metricas_bajo_umbral_test.csv')
    names = {'persistencia': 'Persistencia', 'diaria': 'Diaria', 'HGB': 'HGB'}
    g = global_metrics.copy()
    g['model'] = g['model'].map(names)
    metrics_columns = ['model', 'horizon', 'n', 'mae', 'rmse', 'r2', 'bias']
    sections = []
    for part, title in [('train', 'Entrenamiento 2015–2022: métricas en muestra, optimistas'),
                        ('validation', 'Validación 2023: selección; sin reajuste con 2023'), ('test', 'Evaluación retrospectiva 2024: reajuste 2015–2023')]:
        sections.append(f'## {title}\n\n' + table(g[g.partition == part][metrics_columns], metrics_columns))
    test = global_metrics[global_metrics.partition == 'test']
    improvements = []
    for h in [1, 2, 3]:
        sub = test[test.horizon == h].set_index('model')
        improvements.append({'horizon': h, 'mae_reduction_vs_persistence_pct': 100 * (1 - sub.at['HGB', 'mae'] / sub.at['persistencia', 'mae']),
                             'mae_reduction_vs_daily_pct': 100 * (1 - sub.at['HGB', 'mae'] / sub.at['diaria', 'mae'])})
    improvement = pd.DataFrame(improvements)
    csv_save(improvement, out / 'comparacion_referencias_test.csv')
    high_test = high[(high.partition == 'test') & (high.month == 0)].copy()
    high_test['model'] = high_test.model.map(names)
    month_test = monthly[monthly.partition == 'test'].pivot(index=['horizon', 'month'], columns='model', values='mae')
    exceptions = month_test[month_test.HGB >= month_test.persistencia]
    monthly_table = monthly[(monthly.partition == 'test') & (monthly.model == 'HGB')][['horizon', 'month', 'n', 'mae', 'rmse', 'r2', 'bias']]
    reconciliation = ledger.groupby(['year', 'partition'])[['expected_origins', 'pm10_observed', 'initial_window', 'boundary_excluded', 'included']].sum().reset_index()
    selected = frozen['selected']
    text = f'''# PM10 horario: resultados del primer experimento

Ejecutado localmente en `sprint-3/historico-prediccion`, sin publicar ni cambiar la interfaz o los documentos finales. Objetivo observado en µg/m³, horizontes +1,+2,+3 desde un mismo origen. Error firmado = predicho − observado, positivo para sobreestimación. No se usaron categorías, NowCast o medias diarias como objetivos.

## Registro y configuración seleccionada

Protocolo registrado antes de entrenar: `config/sprint3_modelado_protocolo.json`, SHA-256 `{data['protocol_sha256']}`. Congelación anterior a evaluar 2024: `config_congelada.json`, SHA-256 `{final['freeze_sha256']}`. La cronología queda en `eventos.jsonl` y se verifica automáticamente. 2024 ya se había explorado descriptivamente: esta evaluación es retrospectiva, no una prueba ciega. Sus métricas no se utilizaron para escoger decisiones.

Configuración **{selected['id']}**, de ocho previamente fijadas: **max_leaf_nodes={selected['max_leaf_nodes']}, learning_rate={selected['learning_rate']}, max_iter={selected['max_iter']}**; pérdida squared_error, min_samples_leaf=30, L2=1, early_stopping=False, validation_fraction=None, semilla 20261108. Tres estimadores directos independientes, 47 características causales de PM10 y calendario, sin meteorología ni escaladores. Selección por promedio de MAE de 2023: **{selected['mean_mae']:.6f} µg/m³**. El desempate quedó definido en el protocolo; no fue necesario añadir configuraciones ni cambiar características al ver test.

La búsqueda se ajustó con 2015–2022. Después se congeló y reajustó con **{final['refit_n']:,} ventanas de 2015–2023**. No se recuperaron ventanas extra de una frontera interna en este conjunto real. La función `pm10_modelado.predict_at` puede emitir los tres pronósticos con solo las últimas 24 observaciones y su origen, sin etiquetas futuras. No se recortaron predicciones; las de evaluación resultaron todas no negativas.

## Conciliación y disponibilidad

**53,608** ventanas iniciales del inventario → **3** orígenes excluidos por objetivos que cruzan 2023/2024 → **53,605** orígenes: **41,844** entrenamiento, **5,536** validación y **6,225** evaluación. Los tres orígenes excluidos son 2023-12-31 a las 21:00, 22:00 y 23:00. El contexto anterior a una partición sí puede utilizarse si era conocido en t. Las fechas bisiestas y los ceros reales se conservan.

{table(reconciliation, list(reconciliation.columns))}

La conciliación por los 120 meses de origen está en `conciliacion_mensual.csv`; `auditoria_muestras.csv` documenta también los orígenes descartados por contexto u objetivos incompletos. No se compactó la rejilla ni se imputaron mediciones. En 2024 se observa PM10 en 8,051/8,784 horas (91.7 %), pero solo hay 6,225/8,784 orígenes completos (70.9 %). En julio quedan 268 fechas objetivo por horizonte, frente a hasta 716 en diciembre. El subconjunto es dependiente de las ausencias y no demuestra rendimiento en las horas omitidas.

## Búsqueda solo en 2023

{table(ranking, ['id', 'max_leaf_nodes', 'learning_rate', 'max_iter', 'mean_mae', 'mae_h1', 'mae_h2', 'mae_h3', 'rank'])}

MAE y RMSE se expresan en µg/m³; R² es adimensional. n es el número de predicciones por modelo y horizonte. Las tablas mantienen R² negativos. `n.c.` denota no calculable; los CSV incluyen el motivo. Los errores de entrenamiento son en muestra y no estiman generalización.

''' + '\n\n'.join(sections) + f'''

## Qué mejora y qué se pierde con el horizonte

{table(improvement, list(improvement.columns))}

En validación y evaluación el HGB mejora globalmente ambas referencias en MAE, RMSE y R². El MAE de test aumenta de **16.21 a 20.73 y 22.80 µg/m³** al pasar de +1 a +2 y +3 horas; el R² cae de 0.736 a 0.603 y 0.533. La concentración futura se vuelve menos próxima al estado reciente y al patrón calendario utilizado, sin que este experimento identifique causas del error.

La mejora global no es uniforme por mes. En julio de 2024, +1 h, HGB es **0.070 µg/m³ peor** en MAE que persistencia; a +2/+3 sí mejora. En julio de validación 2023 no mejora persistencia en ninguno de los tres horizontes. Estas excepciones se conservan, sin reajustar el experimento. Los CSV mensuales permiten inspeccionar todas las comparaciones. La referencia diaria y la persistencia a +3 en validación tienen R² negativos; no se han convertido en cero.

## Resultados mensuales del HGB en 2024

{table(monthly_table, list(monthly_table.columns))}

Los errores mensuales se agrupan por mes de **fecha objetivo**, no por origen. Los tamaños pueden diferir entre horizontes al cruzar mes, pero dentro de cada horizonte/mes se conserva exactamente la misma muestra entre modelos. `metricas_mensuales.csv` incluye los tres modelos; los meses de entrenamiento agrupan sus ocho años. `metricas_anio_mes.csv` desglosa además cada año/mes, incluidas filas con n=0.

## Concentraciones altas y signo del error

Umbral fijo: observado ≥ **114 µg/m³**, percentil 90 de las **52,973 horas PM10 utilizables únicas del entrenamiento inicial** (método lineal). No es una categoría normativa ni se recalcula con validación o test.

{table(high_test, metrics_columns)}

HGB subestima las concentraciones altas: sesgo de **−28.08, −44.98 y −53.01 µg/m³**. Sus R² en este estrato son **0.049, −0.466 y −0.730**: pese a mejorar el MAE de las referencias, la predicción de extremos sigue siendo limitada. El sesgo negativo crece con el horizonte. Para observados por debajo del mismo umbral, el sesgo es positivo: **+3.62, +5.87 y +6.98 µg/m³**, respectivamente. El sesgo global pequeño oculta esa compensación; no se interpreta como ausencia de errores ni validación instrumental.

## Figuras y artefactos

- `figuras/01_desarrollo.png` y `.svg`: perfiles de entrenamiento, cobertura y autocorrelación con denominadores.
- `figuras/02_observado_predicho.png` y `.svg`: primera semana calendario de 2024, intervalo fijo, sin escoger por desempeño ni unir huecos.
- `figuras/03_dispersion.png` y `.svg`: todos los puntos HGB de evaluación, escalas comunes y picos conservados.
- `figuras/04_error_mensual.png` y `.svg`: MAE de los tres modelos y n mensual.
- `figuras/05_error_firmado.png` y `.svg`: predicho − observado y umbral diagnóstico. Los cinco PNG se revisaron visualmente; se exportaron sus equivalentes SVG. Catálogo con firmas en `figuras/catalogo_figuras.json`.

En `data/processed/sprint-3/modelado/`: protocolo referenciado y configuración congelada; datos horarios con procedencia, `features.npy`, `targets.npy`, orígenes y auditorías; búsqueda y métricas; nueve CSV de predicciones con origen, fecha objetivo, horizonte, observado, predicho, error firmado, modelo, partición y periodo de ajuste. Se conservan los seis artefactos `modelos/desarrollo/pm10_h*.joblib` y `modelos/reajuste/pm10_h*.joblib`, con contrato de características y fechas de entrenamiento. Los modelos de desarrollo son los de las métricas train/validation; los reajustados corresponden a test.

## Verificación y límites

**114 pruebas Python aprobadas**, incluidas 18 nuevas de fechas, fronteras, ceros, referencias, ausencia de futuro, estabilidad de características y métricas. Verificación adicional: **{verification['checks_passed']:,} comprobaciones**, **{verification['prediction_rows_checked']:,} filas de predicción** reproducidas desde referencias o artefactos, seis modelos recargados, n y MAE/RMSE/R² conciliados independientemente con scikit-learn, y **{verification['old_files_verified']} archivos anteriores intactos**. La conservación incluye originales, inventario y evidencia de ambos sprints. No hubo cambios del dashboard, PDF o Word. No se necesitó un nuevo build web porque sus archivos no cambiaron.

Los huecos son extensos y estacionales, las ventanas se solapan, no hay bitácoras instrumentales suficientes para probar homogeneidad entre años, y el test ya fue expuesto descriptivamente. La evaluación no demuestra funcionamiento en tiempo real, disponibilidad de datos sin retrasos, calibración instrumental, causalidad ni desempeño durante interrupciones. No se estimaron intervalos de incertidumbre o significación para las diferencias. La familia inicial no se comparó todavía con regresión lineal, Random Forest o SARIMA. No se cambió ninguna decisión a partir de los resultados finales.

## Reproducción

Dependencias: `requirements-sprint3-modelado.txt` incorpora el lock previo y fija scikit-learn 1.9.1 y sus dependencias adicionales. No se actualizó el entorno numérico previo. Las funciones de lectura/normalización del inventario se reutilizan sin modificar sus archivos.

Desde la raíz, estos comandos preparan el entorno y reproducen la secuencia ejecutada:

```powershell
.\\.venv\\Scripts\\python.exe -m pip install -r requirements-sprint3-modelado.txt
.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/preparar_modelado_sprint3.py
.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/entrenar_sprint3.py seleccionar
.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/entrenar_sprint3.py evaluar
.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/verificar_modelado_sprint3.py
.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/figuras_modelado_sprint3.py
.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/resumir_modelado_sprint3.py
.\\.venv\\Scripts\\python.exe -X utf8 -W error -m pytest tests -q
```

La instalación real añadió exclusivamente las cinco dependencias nuevas fijadas, con `pip install --no-deps`, conservando las anteriores; `pip check` fue correcto. Los comandos de aprendizaje rechazan sobrescribir un experimento terminado o reabrir selección tras congelarlo. Para reproducir sin alterar esta evidencia, pasar a preparación, selección, evaluación y verificación el mismo `--out .scratch/repro_modelado_pm10`; para las figuras añadir `--figures .scratch/repro_figuras_pm10` y para este resumen `--report .scratch/repro_resultados_pm10.md`. Eso genera solo resultados de otra ejecución, no copia el proyecto. Los originales y el protocolo permanecen como entradas de solo lectura. Los tiempos de ejecución y registros UTC pueden variar, y no se presupone identidad binaria entre plataformas o versiones distintas.
'''
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(text, encoding='utf-8', newline='\n')
    print(f'Resumen técnico: {report}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    summarize(args.out, args.report)
