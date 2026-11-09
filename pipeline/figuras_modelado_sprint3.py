"""Figuras científicas desde resultados congelados; no entrena ni modifica decisiones."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pm10_modelado import OUT, DOCS, csv_save, read_json, sha, write_json

COLORS = {'Observado': '#20282e', 'HGB': '#b65327', 'persistencia': '#31688e', 'diaria': '#8a8294'}


def render(out=OUT, figures=None):
    out = Path(out)
    figures = Path(figures) if figures else DOCS / 'figuras'
    figures.mkdir(parents=True, exist_ok=True)
    freeze = read_json(out / 'config_congelada.json')
    final = read_json(out / 'evaluacion_final.json')
    if final['freeze_sha256'] != sha(out / 'config_congelada.json'):
        raise ValueError('La configuración dejó de ser la congelada')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.titleweight': 'semibold', 'svg.hashsalt': 'pm10-s3-v1',
                         'axes.grid': True, 'grid.alpha': .18, 'axes.axisbelow': True})
    global_metrics = pd.read_csv(out / 'metricas_globales.csv')
    monthly = pd.read_csv(out / 'metricas_mensuales.csv')
    profiles = pd.read_csv(out / 'eda_perfiles_train.csv')
    acf = pd.read_csv(out / 'eda_acf_train.csv')
    hourly = pd.read_csv(out / 'pm10_horario.csv', parse_dates=['DATE']).set_index('DATE').PM10
    pred = {model: pd.read_csv(out / f'predicciones/test_{model}.csv', parse_dates=['origin', 'target_time'])
            for model in ['HGB', 'persistencia', 'diaria']}
    catalog = []

    def save(fig, name, source, selection):
        for ext in ('png', 'svg'):
            path = figures / f'{name}.{ext}'
            fig.savefig(path, dpi=200, facecolor='white', metadata={'Creator': 'CalidadAireJalisco Sprint 3'})
        plt.close(fig)
        catalog.append({'figure': name, 'sources': source, 'selection': selection,
                        'freeze_sha256': final['freeze_sha256'], 'png_sha256': sha(figures / f'{name}.png'),
                        'svg_sha256': sha(figures / f'{name}.svg')})

    fig, axes = plt.subplots(2, 2, figsize=(12, 8.2), layout='constrained')
    for axis, kind, label in [(axes[0, 0], 'hour', 'Hora local codificada'), (axes[0, 1], 'month', 'Mes')]:
        data = profiles[profiles.grouping == kind]
        axis.plot(data.bin, data['mean'], '-o', color=COLORS['HGB'], ms=3)
        axis.set(xlabel=label, ylabel='PM10 medio observado (µg/m³)', title=f'Perfil por {"hora" if kind == "hour" else "mes"} · solo 2015–2022')
        axis.set_xticks(range(0, 24, 3) if kind == 'hour' else range(1, 13))
    data = profiles[profiles.grouping == 'month']
    axes[1, 0].bar(data.bin, data.coverage_pct, color=COLORS['persistencia'])
    for _, row in data.iterrows():
        axes[1, 0].text(row.bin, row.coverage_pct + 1, f'{int(row.n):,}', ha='center', fontsize=8)
    axes[1, 0].set(xlabel='Mes', ylabel='Horas observadas / esperadas (%)', ylim=(0, 110), xticks=range(1, 13),
                   title='Cobertura del desarrollo · etiquetas = n observado')
    data = acf[acf.lag_hours <= 48]
    axes[1, 1].plot(data.lag_hours, data.pearson_pairwise, '-o', color=COLORS['persistencia'], ms=3)
    axes[1, 1].axhline(0, color='gray', lw=.7)
    axes[1, 1].set(xlabel='Separación real (horas)', ylabel='Correlación por pares observados',
                   title='Autocorrelación sin compactar huecos', xticks=[1, 6, 12, 24, 36, 48])
    fig.suptitle('PM10 en entrenamiento: perfiles, ausencias y dependencia temporal\n52,973 / 70,128 horas observadas · n por lag disponible en CSV', fontsize=13)
    save(fig, '01_desarrollo', ['eda_perfiles_train.csv', 'eda_acf_train.csv'], 'Solo 2015–2022; ningún dato predictivo de 2024')

    start, end = pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-07 23:00')
    grid = pd.date_range(start, end, freq='h')
    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True, sharey=True, layout='constrained')
    for h, axis in enumerate(axes, 1):
        axis.plot(grid, hourly.reindex(grid), color=COLORS['Observado'], lw=1.3, label='Observado')
        for model in ['diaria', 'persistencia', 'HGB']:
            data = pred[model][pred[model].horizon.eq(h)].set_index('target_time').predicted.reindex(grid)
            axis.plot(grid, data, color=COLORS[model], lw=1.1, alpha=.9, label=model,
                      linestyle='--' if model == 'diaria' else '-')
        n = pred['HGB'].query('horizon == @h').target_time.between(start, end).sum()
        axis.set(ylabel='PM10 (µg/m³)', title=f'+{h} h · {n} predicciones; los huecos permanecen vacíos')
    axes[0].legend(ncol=4, loc='upper right', fontsize=9)
    axes[-1].xaxis.set_major_locator(mdates.DayLocator(interval=1))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    axes[-1].set_xlabel('Fecha objetivo · hora local codificada')
    fig.suptitle('Observado frente a predicho: primera semana calendario de evaluación\n01–07 enero 2024 · intervalo fijo, sin seleccionar por desempeño', fontsize=13)
    save(fig, '02_observado_predicho', ['pm10_horario.csv', 'predicciones/test_*.csv'], 'Primera semana calendario de 2024; sin interpolar ni conectar huecos')

    fig, axes = plt.subplots(1, 3, figsize=(13, 5.8), sharex=True, sharey=True)
    fig.subplots_adjust(left=.07, right=.99, bottom=.16, top=.74, wspace=.12)
    maximum = float(max(pred['HGB'].observed.max(), pred['HGB'].predicted.max())) * 1.04
    minimum = min(0, float(pred['HGB'].predicted.min()))
    for h, axis in enumerate(axes, 1):
        data = pred['HGB'][pred['HGB'].horizon.eq(h)]
        axis.scatter(data.observed, data.predicted, s=8, alpha=.17, color=COLORS['HGB'], edgecolors='none')
        axis.plot([minimum, maximum], [minimum, maximum], '--', color='gray', lw=1)
        met = global_metrics[(global_metrics.partition == 'test') & (global_metrics.model == 'HGB') & (global_metrics.horizon == h)].iloc[0]
        axis.set(xlabel='Observado (µg/m³)', title=f'+{h} h · n={len(data):,}\nMAE={met.mae:.2f}; R²={met.r2:.3f}', xlim=(minimum, maximum), ylim=(minimum, maximum))
        axis.set_aspect('equal', adjustable='box')
    axes[0].set_ylabel('Predicho (µg/m³)')
    fig.suptitle('Dispersión HGB en 2024 · mismas escalas y todos los picos conservados\nLa diagonal indica coincidencia, no validación instrumental', fontsize=12, y=.98)
    save(fig, '03_dispersion', ['predicciones/test_HGB.csv', 'metricas_globales.csv'], 'Todos los 6,225 orígenes de evaluación en cada horizonte')

    fig, axes = plt.subplots(2, 3, figsize=(13, 6.5), sharex=True, gridspec_kw={'height_ratios': [3, 1]}, layout='constrained')
    sub = monthly[monthly.partition.eq('test')]
    ymax = float(sub.mae.max()) * 1.15
    for h in (1, 2, 3):
        axis, den = axes[0, h - 1], axes[1, h - 1]
        for model in ['diaria', 'persistencia', 'HGB']:
            data = sub[(sub.model == model) & (sub.horizon == h)]
            axis.plot(data.month, data.mae, '-o', ms=4, color=COLORS[model], label=model)
        data = sub[(sub.model == 'HGB') & (sub.horizon == h)]
        den.bar(data.month, data.n, color='#a1adb6')
        for _, row in data.iterrows():
            den.text(row.month, row.n + 14, str(int(row.n)), ha='center', va='bottom', fontsize=7)
        axis.set(title=f'+{h} h', ylim=(0, ymax))
        den.set(xlabel='Mes de la fecha objetivo', xticks=range(1, 13), ylim=(0, 850))
    axes[0, 0].set_ylabel('MAE (µg/m³)')
    axes[1, 0].set_ylabel('n')
    axes[0, 0].legend(fontsize=9)
    fig.suptitle('Error mensual en 2024 y número de predicciones evaluadas\nEl mismo conjunto entre modelos; n puede variar al cruzar un mes entre horizontes', fontsize=12)
    save(fig, '04_error_mensual', ['metricas_mensuales.csv'], 'Mes de fecha objetivo; n visible sin convertir ausencias en errores cero')

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.9), sharex=True, sharey=True, layout='constrained')
    limit = float(np.abs(pred['HGB'].signed_error).max()) * 1.05
    threshold = freeze['high_diagnostic']['train_p90']
    for h, axis in enumerate(axes, 1):
        data = pred['HGB'][pred['HGB'].horizon == h]
        axis.axvspan(threshold, maximum, color='#f4d3be', alpha=.45)
        axis.scatter(data.observed, data.signed_error, s=8, alpha=.16, color=COLORS['HGB'], edgecolors='none')
        axis.axhline(0, color='#27323b', lw=1)
        axis.axvline(threshold, color='#9e613d', ls='--', lw=.8)
        high = data[data.observed >= threshold]
        axis.set(xlabel='Observado (µg/m³)', title=f'+{h} h · altas n={len(high):,}\nSesgo en altas={high.signed_error.mean():.2f} µg/m³', xlim=(minimum, maximum), ylim=(-limit, limit))
    axes[0].set_ylabel('Predicho − observado (µg/m³)')
    fig.suptitle('Error firmado HGB en 2024: positivo sobreestima; negativo subestima\nZona sombreada ≥114 µg/m³: percentil 90 de entrenamiento, sin significado normativo', fontsize=12)
    save(fig, '05_error_firmado', ['predicciones/test_HGB.csv', 'config_congelada.json'], 'Todas las predicciones; umbral aprendido solo de horas 2015–2022')
    write_json(figures / 'catalogo_figuras.json', {'figures': catalog, 'source_run': str(out), 'freeze_sha256': final['freeze_sha256']})
    print(f'{len(catalog)} figuras verificables exportadas en PNG y SVG: {figures}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=OUT)
    parser.add_argument('--figures', type=Path)
    args = parser.parse_args()
    render(args.out, args.figures)
