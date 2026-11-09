"""Cotejo independiente de fuentes, cobertura y conservación del inventario."""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from descargar_historico_sprint3 import ROOT, MANIFEST, DOCS, digest, save, validate_xlsx
from inventario_sprint3 import OUT, VARIABLES, numeric


def main():
    assertions = 0

    def check(condition, message):
        nonlocal assertions
        if not condition:
            raise AssertionError(message)
        assertions += 1

    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    sources = manifest['fuentes']
    check([s['year'] for s in sources] == list(range(2015, 2025)), 'Deben estar los diez años')
    for s in sources:
        check(s['status'] == 'disponible', f"Fuente no disponible {s['year']}")
        p = ROOT / s['path']
        check(digest(p) == s['sha256'], f"Hash de {s['year']}")
        check(p.stat().st_size == s['bytes'], f"Tamaño de {s['year']}")
        validate_xlsx(p)
        if s['year'] <= 2022:
            check(s['http_status'] == 200 and s['descargado_en_utc'], f"Descarga de {s['year']}")
        else:
            check(s['reutilizado_sprint2'] and s['descargado_en_utc'] is None, f"No inventar fecha de {s['year']}")
    annual = pd.read_csv(OUT / 'cobertura_anual.csv')
    monthly = pd.read_csv(OUT / 'cobertura_mensual.csv')
    horizons = pd.read_csv(OUT / 'disponibilidad_horizontes.csv')
    check(len(annual) == 10 * len(VARIABLES), 'Dimensiones anuales')
    check(len(monthly) == 12 * len(annual), 'Dimensiones mensuales')
    check(len(horizons) == len(annual), 'Dimensiones de horizontes')
    check(not annual.duplicated(['year', 'variable']).any(), 'Claves anuales únicas')
    for row in annual.to_dict('records'):
        sub = monthly[(monthly.year == row['year']) & (monthly.variable == row['variable'])]
        check(int(sub.expected_hours.sum()) == row['expected_hours'], 'Denominador mensual/anual')
        check(int(sub.numeric_hours.sum()) == row['numeric_unique_hours'], 'Conteo numérico mensual/anual')
        check(int(sub.usable_basic_hours.sum()) == row['usable_basic_hours'], 'Conteo básico mensual/anual')
        check(0 <= row['usable_basic_hours'] <= row['numeric_unique_hours'] <= row['expected_hours'], 'Orden de conteos')
        check(abs(row['usable_basic_pct'] - 100 * row['usable_basic_hours'] / row['expected_hours']) <= .000051, 'Porcentaje reproducible')
        h = horizons[(horizons.year == row['year']) & (horizons.variable == row['variable'])].iloc[0]
        check(all(0 <= h[f'pair_t_tplus{k}'] <= row['usable_basic_hours'] for k in (1, 2, 3)), 'Pares no inventados')
        check(0 <= h.windows_24past_3future <= min(h[f'pair_t_tplus{k}'] for k in (1, 2, 3)), 'Ventanas sin huecos')
    # Contraste con extractos del Sprint 2, leídos con otro lector y sin regenerarlos.
    for year in (2023, 2024):
        raw = pd.read_csv(ROOT / f'data/source/sprint-2/MIR_{year}.csv', keep_default_na=False)
        raw.columns = [c.strip().upper() for c in raw.columns]
        expected_dates = pd.date_range(f'{year}-01-01', f'{year}-12-31 23:00', freq='h')
        check(pd.to_datetime(raw.DATE).tolist() == expected_dates.tolist(), f'Fechas extracto {year}')
        for variable in VARIABLES:
            count = sum(numeric(v) is not None for v in raw[variable])
            measured = int(annual[(annual.year == year) & (annual.variable == variable)].iloc[0].numeric_source_rows)
            check(count == measured, f'Cotejo numérico {year}/{variable}')
    baseline = json.loads((DOCS / 'conservacion_inicial.json').read_text(encoding='utf-8'))
    changed = [name for name, sha in baseline['archivos'].items() if not (ROOT / name).is_file() or digest(ROOT / name) != sha]
    check(not changed, 'Archivos históricos modificados: ' + str(changed))
    save(DOCS / 'verificacion_inventario.json', {
        'checks_passed': assertions, 'sources_sha256_crc_verified': len(sources),
        'verification_runtime': {'python': sys.version.split()[0], 'pandas': pd.__version__, 'numpy': np.__version__},
        'annual_rows': len(annual), 'monthly_rows': len(monthly), 'horizon_rows': len(horizons),
        'sprint2_raw_numeric_comparisons': 2 * len(VARIABLES),
        'historical_files_verified': len(baseline['archivos']), 'historical_changes': changed,
        'scope': 'Cotejos de datos y conservación. No acredita calibración, entrenamiento ni despliegue.'})
    print(f'{assertions} comprobaciones aprobadas; 10 fuentes SHA/CRC, 34 cotejos con Sprint 2 y {len(baseline["archivos"])} archivos históricos intactos.')


if __name__ == '__main__':
    main()
