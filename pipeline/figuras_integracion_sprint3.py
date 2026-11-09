"""Figuras históricas nuevas y vínculo explícito hallazgo–población–fuente."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from historico_sprint3 import OUT, read_json, save_json
from pm10_modelado import ROOT, sha

FIG = ROOT / 'docs/sprints/sprint-3/integracion/figuras'


def run():
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'svg.hashsalt': 'mir-historico-v1', 'axes.axisbelow': True,
                         'axes.grid': True, 'grid.alpha': .18})
    records = []
    def save(fig, name, ids, sources, period, population, limitation):
        for ext in ['png', 'svg']:
            fig.savefig(FIG / f'{name}.{ext}', dpi=180, facecolor='white', metadata={'Creator': 'Academia Miravalle'})
        plt.close(fig)
        records.append({'name': name, 'graph_ids': ids, 'sources_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sources},
                        'period': period, 'population': population, 'limitation': limitation,
                        'png_sha256': sha(FIG / f'{name}.png'), 'svg_sha256': sha(FIG / f'{name}.svg')})
    coverage = pd.read_csv(ROOT / 'data/processed/sprint-3/cobertura_anual.csv')
    variables = ['PM10', 'PM2.5', 'O3', 'CO', 'NO2', 'SO2', 'ET', 'RH', 'WS', 'WD']
    matrix = coverage.pivot(index='variable', columns='year', values='usable_basic_pct').reindex(variables)
    fig, ax = plt.subplots(figsize=(13, 7), layout='constrained')
    heat = ax.imshow(matrix.values, vmin=0, vmax=100, cmap='Blues', aspect='auto')
    for i in range(len(variables)):
        for j in range(10):
            value = matrix.iloc[i, j]
            ax.text(j, i, f'{value:.1f} %', ha='center', va='center', color='white' if value > 55 else '#152640', fontsize=9)
    ax.set(xticks=range(10), xticklabels=matrix.columns, yticks=range(len(variables)), yticklabels=variables,
           title='Cobertura utilizable: el denominador es todo el año, no solo las filas con medición')
    ax.grid(False); fig.colorbar(heat, ax=ax, label='% de horas esperadas (8,760 / 8,784)')
    fig.suptitle('Miravalle 2015–2024 · disponibilidad y discontinuidades\n0 % no significa concentración cero; SO₂ 2023 se excluye por calibración', fontsize=13)
    save(fig, '01_cobertura', ['historico-cobertura'], [ROOT / 'data/processed/sprint-3/cobertura_anual.csv'], '2015–2024',
         'Horas utilizables / todas las horas del año, por variable', 'Cobertura básica no acredita validez instrumental; NO₂ 2024 exploratorio.')

    profiles = pd.read_csv(OUT / 'perfiles.csv')
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout='constrained')
    for ax, kind, xlabel in [(axes[0], 'hour', 'Hora local codificada'), (axes[1], 'season', 'Mes calendario')]:
        data = profiles[(profiles.pollutant == 'PM10') & (profiles.year == 0) & (profiles.kind == kind)]
        ax.plot(data.bin, data['mean'], '-o', color='#2c56cf', ms=4)
        ax.set(xlabel=xlabel, ylabel='Media de concentración horaria PM10 (µg/m³)')
        for _, r in data.iloc[::2 if kind == 'hour' else 1].iterrows():
            ax.annotate(f'n={int(r.n):,}', (r.bin, r['mean']), xytext=(0, 9), textcoords='offset points', ha='center', fontsize=6.5)
        ax.margins(y=.2)
    fig.suptitle('Perfiles observados de PM10 · 2015–2024\nPoblación disponible; mezcla años y temporadas con cobertura diferente', fontsize=13)
    save(fig, '02_perfiles_pm10', ['historico-horas'], [OUT / 'perfiles.csv'], '2015–2024',
         'PM10 horario utilizable agrupado por hora y mes; n visible', 'No es comparación pareada ni identificación de fuentes o mecanismos.')

    daily = pd.read_csv(OUT / 'diario.csv', parse_dates=['DATE']).set_index('DATE')
    colors = ['#00e400', '#ffff00', '#ff7e00', '#ff0000', '#8f3f97']
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), layout='constrained')
    for ax, pol in zip(axes, ['PM10', 'CO']):
        left = np.zeros(2)
        for i, name in enumerate(['Buena', 'Aceptable', 'Mala', 'Muy Mala', 'Extremadamente Mala']):
            counts = [int(daily.loc[(daily.index.year == y) & (daily.index.month == 12), f'C_{pol}'].eq(i).sum()) for y in [2023, 2024]]
            ax.barh([0, 1], counts, left=left, color=colors[i], edgecolor='#555555', linewidth=.4, label=name)
            for j, n in enumerate(counts):
                if n: ax.text(left[j] + n / 2, j, str(n), ha='center', va='center', color='white' if i == 4 else '#14202c')
            left += counts
        ax.set(yticks=[0, 1], yticklabels=['2023', '2024'], xlabel='Días con categoría (de 31 esperados)', xlim=(0, 31), title=pol)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=5, loc='outside lower center', fontsize=8)
    fig.suptitle('Diciembre 2023 frente a 2024 · categorías diarias bajo referencia de 2024\nPM10: promedio diario; CO: máximo diario de medias móviles de 8 h', fontsize=12)
    save(fig, '03_diciembre', ['comparacion-periodos'], [OUT / 'diario.csv', OUT / 'comparaciones.json'], 'Diciembre 2023 y 2024',
         '31 fechas pareadas; días con base suficiente por contaminante', 'Referencias retrospectivas; parear fechas no controla meteorología ni actividades.')

    episode = max([r for r in read_json(OUT / 'episodios.json') if r['pollutant'] == 'PM10'], key=lambda r: r['days'])
    d = daily.loc['2021-12-01':'2022-01-31']
    fig, ax = plt.subplots(figsize=(13, 4.6), layout='constrained')
    ax.plot(d.index, d.I_PM10, color='#657790', linewidth=1)
    for i in range(5):
        selected = d[d.C_PM10 == i]
        ax.scatter(selected.index, selected.I_PM10, color=colors[i], edgecolors='#333333', linewidths=.4, zorder=3, s=27)
    ax.axhline(60, color='#8c5627', linestyle='--', linewidth=.8, label='Límite Aceptable/Mala: referencia 2024')
    ax.set(ylabel='Promedio diario PM10 redondeado (µg/m³)', xlabel='Fecha real')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m-%Y'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=10))
    ax.legend(fontsize=8)
    fig.suptitle(f"Episodio descriptivo PM10: {episode['days']} días Mala o peor\n{episode['start']} — {episode['end']} · faltantes interrumpen episodios; no se atribuye causa", fontsize=12)
    save(fig, '04_episodio', ['episodios-secuencia'], [OUT / 'diario.csv', OUT / 'episodios.json'], f"{episode['start']} — {episode['end']}",
         'Días con promedio diario PM10 suficiente, mínimo 18 lecturas', 'Episodio del proyecto con bandas de 2024, sin atribución causal ni aprobación instrumental.')
    save_json(FIG / 'catalogo.json', {'figures': records, 'model_figure_reference': 'docs/sprints/sprint-3/modelado/figuras/05_error_firmado.png'})
    found = read_json(OUT / 'hallazgos.json')
    lines = ['# Hallazgos trazables y recursos de integración', '',
             'Documento técnico de revisión; no es el informe final ni la presentación del Sprint 3.', '',
             '| ID | Hallazgo | Figura / vista | Periodo | Población | Limitación |', '|---|---|---|---|---|---|']
    mapping = {'historico-cobertura': '01_cobertura', 'historico-horas': '02_perfiles_pm10', 'comparacion-periodos': '03_diciembre', 'episodios-secuencia': '04_episodio'}
    for f in found:
        file = f"figuras/{mapping[f['figure']]}.png" if f['figure'] in mapping else '../modelado/figuras/05_error_firmado.png'
        lines.append(f"| {f['id']} | {f['detail']} | [{f['figure']}]({file}) | {f['period']} | {f['population']} | {f['limitation']} |")
    lines += ['', '## Reproducir y verificar', '', 'Los originales, el inventario y todo el experimento C05 se conservan. La portada recibe solo el resumen (aproximadamente 22 KB), y los detalles se cargan por año/mes, contaminante o consulta. No hay API de entrenamiento ni peticiones entre dominios para datos. CORS no se modifica.', '',
              '```powershell', '.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/historico_sprint3.py',
              '.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/exportar_integracion_sprint3.py',
              '.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/figuras_integracion_sprint3.py',
              '.\\.venv\\Scripts\\python.exe -X utf8 -W error pipeline/verificar_integracion_sprint3.py',
              '.\\.venv\\Scripts\\python.exe -X utf8 -W error -m pytest tests -q', 'Set-Location web',
              'node scripts/validar-integracion.mjs', 'npm run lint', 'npm run build',
              'node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3033', '```', '',
              'El histórico rechaza sobrescribir un análisis terminado; si ya existe su manifiesto, usar los verificadores y exportador sobre la evidencia existente. Los resultados completos están en `data/processed/sprint-3/historico/`; C05 sigue en su carpeta `modelado/` sin cambios. La navegación conserva `/sprint-1`, `/sprint-2` y la antigua portada en `/observatorio-mensual`.', '',
              'Suficiencia: ver `CRITERIOS_HISTORICOS.md`, registrado antes del análisis. Los pisos del diagnóstico robusto conservan PM10=10, PM2.5=5 y CO=0.1 del Sprint 2, y usan 0.005 para O3, NO2 y los gases adicionales SO2/NO/NOX; esos límites no son normativos y las señales nunca se eliminan.', '',
              'La continuidad histórica utiliza el contexto disponible desde 2015 y puede diferir del arranque de 2023 del Sprint 2 (que no disponía de 2022). Las páginas y resultados originales de los sprints 1 y 2 siguen disponibles. La comparación de categorías utiliza la referencia retrospectiva de 2024; no reconstruye avisos históricos.']
    (FIG.parent / 'INTEGRACION_TECNICA.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('Cuatro figuras históricas PNG/SVG y tabla de seis hallazgos generadas.', flush=True)


if __name__ == '__main__': run()
