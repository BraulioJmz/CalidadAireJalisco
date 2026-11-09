"""Diagnóstico de MIR 2015–2024, sin imputar, entrenar ni recalcular indicadores.

Lee OpenXML en flujo para no cargar las otras estaciones en memoria. Conserva
encabezados, tipos, filas, fórmulas/caché y metadatos de cada libro por separado.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
import csv
import json
import math
from pathlib import Path
import posixpath
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import pandas as pd
from openpyxl.utils.datetime import from_excel, WINDOWS_EPOCH, MAC_EPOCH

from descargar_historico_sprint3 import ROOT, MANIFEST, DOCS, digest, save

OUT = ROOT / 'data/processed/sprint-3'
VARIABLES = ['O3', 'NO', 'NO2', 'NOX', 'SO2', 'CO', 'PM10', 'PM2.5',
             'IT', 'ET', 'RH', 'WS', 'WD', 'PP', 'ATM', 'RS', 'UVI']
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
ALIASES = {'PM25': 'PM2.5', 'ESTACION': 'STATION', 'FECHA': 'DATE',
           'FECHAHORA': 'DATE', 'HORA': 'HOUR', 'NOX': 'NOX'}


def norm(value) -> str:
    text = ''.join(c for c in unicodedata.normalize('NFKD', str(value or '')) if not unicodedata.combining(c))
    return re.sub(r'[^A-Z0-9]', '', text.upper())


def header(value) -> str:
    key = norm(value)
    return ALIASES.get(key, key)


def column_index(address: str) -> int:
    n = 0
    for char in re.match(r'[A-Z]+', address).group():
        n = n * 26 + ord(char) - 64
    return n - 1


class Book:
    """Lector de valores almacenados, sin evaluar fórmulas ni editar el ZIP."""
    def __init__(self, path: Path):
        self.zip = zipfile.ZipFile(path)
        tree = ET.fromstring(self.zip.read('xl/workbook.xml'))
        props = tree.find(NS + 'workbookPr')
        self.epoch = MAC_EPOCH if props is not None and props.get('date1904') in ('1', 'true') else WINDOWS_EPOCH
        rels = ET.fromstring(self.zip.read('xl/_rels/workbook.xml.rels'))
        targets = {r.get('Id'): r.get('Target') for r in rels}
        self.sheets = []
        for s in tree.find(NS + 'sheets'):
            target = targets[s.get(RID)]
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            self.sheets.append({'name': s.get('name'), 'state': s.get('state', 'visible'), 'xml': target})
        self.strings = []
        if 'xl/sharedStrings.xml' in self.zip.namelist():
            with self.zip.open('xl/sharedStrings.xml') as stream:
                for event, elem in ET.iterparse(stream, events=('end',)):
                    if elem.tag == NS + 'si':
                        self.strings.append(''.join(t.text or '' for t in elem.iter(NS + 't')))
                        elem.clear()

    def cell(self, cell):
        kind = cell.get('t', 'n')
        val = cell.find(NS + 'v')
        if kind == 'inlineStr':
            return ''.join(t.text or '' for t in cell.iter(NS + 't'))
        if val is None or val.text is None:
            return None
        if kind == 's':
            return self.strings[int(val.text)]
        if kind in ('str', 'e', 'd'):
            return val.text
        if kind == 'b':
            return bool(int(val.text))
        try:
            return float(val.text)
        except ValueError:
            return val.text

    def rows(self, sheet, station_col=None):
        with self.zip.open(sheet['xml']) as stream:
            context = ET.iterparse(stream, events=('start', 'end'))
            _, root = next(context)
            for event, elem in context:
                if event == 'end' and elem.tag == NS + 'dimension':
                    sheet['declared_dimension'] = elem.get('ref')
                if event != 'end' or elem.tag != NS + 'row':
                    continue
                cells = {column_index(c.get('r')): c for c in elem if c.tag == NS + 'c'}
                station = self.cell(cells[station_col]) if station_col is not None and station_col in cells else None
                if station_col is None or norm(station) in ('MIR', 'MIRAVALLE'):
                    vals = {i: self.cell(c) for i, c in cells.items()}
                    formulas = [i for i, c in cells.items() if c.find(NS + 'f') is not None]
                    uncached = [i for i in formulas if vals[i] is None]
                    types = {i: c.get('t', 'n') for i, c in cells.items()}
                    yield int(elem.get('r')), vals, formulas, uncached, types
                elem.clear()
                # Eliminar filas procesadas del padre para mantener memoria acotada.
                root.clear()

    def close(self):
        self.zip.close()


def detect_header(book: Book, sheet: dict):
    for number, values, *_ in book.rows(sheet):
        names = {i: header(v) for i, v in values.items() if v is not None}
        if 'STATION' in names.values() and 'DATE' in names.values():
            if len(names.values()) != len(set(names.values())):
                raise ValueError(f'Encabezados duplicados en {sheet["name"]}:{number}')
            return number, names, {i: values[i] for i in names}
        if number >= 40:
            break
    return None


def as_datetime(value, epoch):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (float, int)):
        result = from_excel(value, epoch)
        return result if isinstance(result, datetime) else None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).strip())
    except ValueError:
        return None  # No adivinar orden día/mes de cadenas ambiguas.


def numeric(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def plausible(variable: str, value: float) -> bool:
    if variable in ('IT', 'ET'):
        return True  # Sin límites instrumentales documentados; negativos permitidos.
    if variable == 'RH':
        return 0 <= value <= 100
    if variable == 'WD':
        return 0 <= value <= 360
    if variable == 'ATM':
        return value > 0
    return value >= 0


def intervals(mask, index):
    """Intervalos inclusivos en rejilla real; nunca une horas faltantes."""
    padded = np.r_[False, np.asarray(mask, dtype=bool), False].astype(np.int8)
    starts = np.flatnonzero(np.diff(padded) == 1)
    ends = np.flatnonzero(np.diff(padded) == -1) - 1
    return [(index[a].isoformat(), index[b].isoformat(), int(b - a + 1)) for a, b in zip(starts, ends)]


def metadata(book, sheets):
    rows = []
    units = {}
    catalog = []
    flags = {}
    for sheet in sheets:
        data = []
        for number, vals, *_ in book.rows(sheet):
            if vals and any(v is not None for v in vals.values()):
                data.append({'row': number, 'values': [vals.get(i) for i in range(max(vals) + 1)]})
        rows.append({'sheet': sheet['name'], 'rows': data})
        for row in data:
            v = row['values']
            if any(norm(x) in ('MIR', 'MIRAVALLE') for x in v[:2]):
                catalog.append({'sheet': sheet['name'], **row})
        for title in data:
            values = title['values']
            for i, label in enumerate(values):
                key = norm(label)
                if key.startswith('UNIDAD'):
                    for row in data:
                        v = row['values']
                        if len(v) > i and i >= 1:
                            code = header(v[i - 1])
                            if code in VARIABLES and v[i] is not None:
                                units[code] = str(v[i])
                if key == 'BANDERA':
                    for row in data:
                        v = row['values']
                        if len(v) > i + 1 and v[i] is not None and row['row'] > title['row']:
                            flags[str(v[i])] = str(v[i + 1])
    declared = set()
    if catalog:
        for row in catalog:
            for value in row['values'][2:4]:
                for token in re.split(r'[,;/]', str(value or '')):
                    code = header(token)
                    if code in VARIABLES:
                        declared.add(code)
    return {'sheets': rows, 'units': units, 'catalog_MIR': catalog,
            'declared_MIR': sorted(declared), 'flags': flags}


def inspect_source(source: dict):
    year = source['year']
    path = ROOT / source['path']
    if digest(path) != source['sha256']:
        raise ValueError(f'Hash inesperado antes de leer {year}')
    book = Book(path)
    try:
        candidates = [(s, detect_header(book, s)) for s in book.sheets]
        candidates = [(s, h) for s, h in candidates if h is not None]
        if len(candidates) != 1:
            raise ValueError(f'{year}: {len(candidates)} hojas de datos; requiere revisión explícita')
        sheet, (header_row, names, raw_names) = candidates[0]
        meta = metadata(book, [s for s in book.sheets if s is not sheet])
        station_col = next(i for i, n in names.items() if n == 'STATION')
        records = []
        formula_counts = Counter()
        uncached_counts = Counter()
        type_counts = Counter()
        station_names = Counter()
        for row, values, formulas, uncached, types in book.rows(sheet, station_col):
            if row <= header_row:
                continue
            item = {names[i]: v for i, v in values.items() if i in names}
            station_names[str(item.get('STATION'))] += 1
            formula_counts.update(names[i] for i in formulas if i in names)
            uncached_counts.update(names[i] for i in uncached if i in names)
            type_counts.update(f'{names[i]}:{t}' for i, t in types.items() if i in names)
            item['_row'] = row
            item['_date_raw'] = item.get('DATE')
            item['_date'] = as_datetime(item.get('DATE'), book.epoch)
            records.append(item)
        expected = pd.date_range(f'{year}-01-01', f'{year}-12-31 23:00', freq='h')
        dates = Counter(r['_date'] for r in records if r['_date'] is not None)
        valid_keys = {t for t, n in dates.items() if n == 1 and t.year == year and t.minute == t.second == t.microsecond == 0 and t.tzinfo is None}
        keys_present = {t for t in dates if t in expected}
        eligible_rows = {r['_date']: r for r in records if r['_date'] in valid_keys}
        steps = Counter(str(b - a) for a, b in zip(sorted(keys_present), sorted(keys_present)[1:]))
        aux = {}
        for col, attr in [('HOUR', 'hour'), ('DIA', 'day'), ('MES', 'month')]:
            if col in names.values():
                aux[col] = sum(numeric(r.get(col)) != getattr(r['_date'], attr) for r in records if r['_date'] is not None)
        distinct_rows = len({tuple(str(r.get(names[i])) for i in sorted(names)) for r in records})
        detail = {'year': year, 'path': source['path'], 'sha256': source['sha256'], 'sheets': book.sheets,
                  'data_sheet': sheet['name'], 'header_row': header_row, 'headers_original': list(raw_names.values()),
                  'headers_normalized': list(names.values()), 'epoch': book.epoch.isoformat(),
                  'MIR_names': dict(station_names), 'rows_MIR': len(records), 'expected_hours': len(expected),
                  'missing_timestamp_hours': len(expected) - len(keys_present),
                  'duplicate_timestamp_extra_rows': sum(n - 1 for n in dates.values() if n > 1),
                  'duplicate_exact_extra_rows': len(records) - distinct_rows,
                  'duplicate_timestamps': [{'date': t.isoformat(), 'count': n} for t, n in dates.items() if n > 1],
                  'invalid_dates': sum(r['_date'] is None for r in records),
                  'outside_year': sum(r['_date'] is not None and r['_date'].year != year for r in records),
                  'unaligned_dates': sum(r['_date'] is not None and (r['_date'].minute or r['_date'].second or r['_date'].microsecond) != 0 for r in records),
                  'date_min': min(dates).isoformat() if dates else None, 'date_max': max(dates).isoformat() if dates else None,
                  'step_counts': dict(steps), 'auxiliary_mismatches': aux,
                  'formula_counts_MIR': dict(formula_counts), 'uncached_formulas_MIR': dict(uncached_counts),
                  'cell_types_MIR': dict(type_counts), 'metadata': meta, 'variables': []}
        arrays = {}
        month_rows = []
        run_rows = []
        for variable in VARIABLES:
            raw = [r.get(variable) for r in records]
            numbers = [numeric(v) for v in raw]
            usable = np.full(len(expected), np.nan)
            raw_grid = np.full(len(expected), np.nan)
            for j, timestamp in enumerate(expected):
                r = eligible_rows.get(timestamp.to_pydatetime())
                if r is None:
                    continue
                number = numeric(r.get(variable))
                if number is not None:
                    raw_grid[j] = number
                    if plausible(variable, number) and not (year == 2023 and variable == 'SO2'):
                        usable[j] = number
            arrays[variable] = usable
            good = np.isfinite(usable)
            finite = [v for v in numbers if v is not None]
            markers = Counter(str(v) for v in raw if v is not None and str(v).strip() and numeric(v) is None)
            runs = intervals(good, expected)
            gaps = intervals(~good, expected)
            stats = {'year': year, 'variable': variable, 'column_present': variable in names.values(),
                     'declared_MIR': variable in meta['declared_MIR'] if meta['catalog_MIR'] else None,
                     'unit_in_book': meta['units'].get(variable), 'expected_hours': len(expected),
                     'numeric_source_rows': len(finite), 'numeric_unique_hours': int(np.isfinite(raw_grid).sum()),
                     'numeric_pct': round(float(np.isfinite(raw_grid).mean() * 100), 4),
                     'usable_basic_hours': int(good.sum()), 'usable_basic_pct': round(float(good.mean() * 100), 4),
                     'blank_source_rows': sum(v is None or not str(v).strip() for v in raw),
                     'text_numeric_rows': sum(isinstance(v, str) and numeric(v) is not None for v in raw),
                     'non_numeric_markers': dict(markers), 'negative_rows': sum(v < 0 for v in finite),
                     'zero_rows': sum(v == 0 for v in finite), 'implausible_rows': sum(not plausible(variable, v) for v in finite),
                     'official_exclusion_hours': int(np.isfinite(raw_grid).sum()) if year == 2023 and variable == 'SO2' else 0,
                     'min_source': min(finite) if finite else None, 'max_source': max(finite) if finite else None,
                     'median_source': float(np.median(finite)) if finite else None,
                     'distinct_source_values': len(set(finite)),
                     'first_usable': runs[0][0] if runs else None, 'last_usable': runs[-1][1] if runs else None,
                     'max_consecutive_usable_hours': max((r[2] for r in runs), default=0),
                     'max_missing_or_excluded_hours': max((r[2] for r in gaps), default=0),
                     'months_ge75_basic': sum(float(good[expected.month == m].mean()) >= .75 for m in range(1, 13)),
                     'warning': 'Exclusión oficial SO2 2023 conservada del Sprint 2 (INECC p. 222)' if year == 2023 and variable == 'SO2' else
                                'Valores presentes pero variable no declarada para MIR en catálogo; procedencia por verificar' if finite and meta['catalog_MIR'] and variable not in meta['declared_MIR'] else ''}
            detail['variables'].append(stats)
            for state, segments in [('disponible_basico', runs), ('sin_dato_utilizable', gaps)]:
                for start, end, count in segments:
                    if count >= 24:
                        run_rows.append({'year': year, 'variable': variable, 'state': state, 'start': start, 'end': end, 'hours': count})
            for m in range(1, 13):
                pick = expected.month == m
                month_rows.append({'year': year, 'month': m, 'variable': variable,
                                   'expected_hours': int(pick.sum()), 'numeric_hours': int(np.isfinite(raw_grid[pick]).sum()),
                                   'usable_basic_hours': int(good[pick].sum()), 'usable_basic_pct': round(float(good[pick].mean() * 100), 4)})
        if digest(path) != source['sha256']:
            raise ValueError(f'El original {year} cambió durante la lectura')
        return detail, arrays, month_rows, run_rows
    finally:
        book.close()


def csv_write(path: Path, rows: list[dict]):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    # UTF-8 sin BOM, nulos vacíos; no modificar fuentes ni indicadores previos.
    with path.open('w', encoding='utf-8', newline='') as stream:
        fields = list(dict.fromkeys(k for row in rows for k in row))
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})


def forecast_windows(all_arrays):
    """Solo contar ventanas; no producir ejemplos de entrenamiento ni modelos."""
    global_index = pd.date_range('2015-01-01', '2024-12-31 23:00', freq='h')
    results = []
    for variable in VARIABLES:
        chunks = [all_arrays.get(y, {}).get(variable, np.full((8784 if y % 4 == 0 else 8760), np.nan)) for y in range(2015, 2025)]
        good = np.isfinite(np.concatenate(chunks))
        assert len(good) == len(global_index)
        for year in range(2015, 2025):
            anchor = global_index.year == year
            item = {'year': year, 'variable': variable}
            for h in (1, 2, 3):
                pair = np.zeros(len(good), dtype=bool)
                pair[:-h] = good[:-h] & good[h:]
                item[f'pair_t_tplus{h}'] = int((pair & anchor).sum())
            rolling = np.convolve(good.astype(np.int64), np.ones(27, dtype=np.int64), mode='valid') == 27
            # 24 observaciones pasadas (incluido t), seguidas de t+1,+2,+3.
            strict = np.zeros(len(good), dtype=bool)
            strict[23:len(good) - 3] = rolling
            item['windows_24past_3future'] = int((strict & anchor).sum())
            results.append(item)
    return results


def main():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    sources = {s['year']: s for s in manifest['fuentes']}
    details = []
    all_arrays = {}
    monthly = []
    runs = []
    OUT.mkdir(parents=True, exist_ok=True)
    for year in range(2015, 2025):
        source = sources.get(year)
        if not source or source['status'] != 'disponible':
            details.append({'year': year, 'error': 'Fuente no disponible; no se sustituye por datos sintéticos'})
            continue
        detail, arrays, months, segments = inspect_source(source)
        details.append(detail)
        all_arrays[year] = arrays
        monthly.extend(months)
        runs.extend(segments)
        save(OUT / f'libro_{year}.json', detail)
        print(f"{year}: {detail['rows_MIR']} filas MIR, {detail['duplicate_timestamp_extra_rows']} duplicados, diagnóstico terminado", flush=True)
    annual = [v for detail in details for v in detail.get('variables', [])]
    windows = forecast_windows(all_arrays)
    csv_write(OUT / 'cobertura_anual.csv', annual)
    csv_write(OUT / 'cobertura_mensual.csv', monthly)
    csv_write(OUT / 'intervalos_24h.csv', runs)
    csv_write(OUT / 'disponibilidad_horizontes.csv', windows)
    base = json.loads((DOCS / 'conservacion_inicial.json').read_text(encoding='utf-8'))
    changes = [name for name, sha in base['archivos'].items() if not (ROOT / name).is_file() or digest(ROOT / name) != sha]
    summary = {'schema': 'mir-s3-inventario-v1', 'ventana': [2015, 2024], 'variables': VARIABLES,
               'scope': 'Inventario y diagnóstico; sin modelos, imputación, normativa nueva ni cambios de interfaz',
               'books': [{k: v for k, v in d.items() if k not in ('variables', 'metadata', 'cell_types_MIR')} for d in details],
               'preservation': {'base_commit': base['commit_base'], 'files_checked': len(base['archivos']), 'changed': changes},
               'rules': {'coverage_denominator': 'Todas las horas del año local codificado, incluido 29 de febrero. Sin inferir UTC/DST.',
                         'numeric': 'Finito, clave de hora única y fecha del año alineada a hora. No se cuentan dos veces duplicados; se descartan claves ambiguas.',
                         'usable_basic': 'Numérico más plausibilidad mínima: contaminantes y WS/PP/RS/UVI >=0, RH 0..100, WD 0..360, ATM>0; ET/IT finitas. SO2 2023 excluido por evidencia previa. No acredita calibración.',
                         '75_percent': 'Descriptor exploratorio de meses, no suficiencia normativa ni selección automática de entrenamiento.',
                         'periods': 'Intervalos >=24 horas consecutivas; los huecos se preservan. Ventanas de 24 horas pasadas y 3 futuras se cuentan sobre rejilla global sin imputar.'}}
    save(OUT / 'inventario.json', summary)
    if changes:
        raise ValueError(f'Cambiaron archivos históricos: {changes}')
    print(f'Conservación: {len(base["archivos"])} archivos previos intactos. Sin entrenamiento.', flush=True)


if __name__ == '__main__':
    main()
