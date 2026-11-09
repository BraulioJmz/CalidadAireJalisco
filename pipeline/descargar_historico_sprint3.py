"""Adquisición conservadora 2015–2024: originales inmutables y trazabilidad.

No ejecuta los pipelines previos, no transforma Excel y nunca sobrescribe fuentes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'config/fuentes_sprint3.json'
SOURCE = ROOT / 'data/source/sprint-3/originales'
DOCS = ROOT / 'docs/sprints/sprint-3'
URL = 'https://aire.jalisco.gob.mx/reportes/BD_{year}.xlsx'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def validate_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path) as book:
        names = set(book.namelist())
        if not {'[Content_Types].xml', 'xl/workbook.xml'}.issubset(names):
            raise ValueError('La respuesta no es un libro XLSX válido')
        bad = book.testzip()
        if bad:
            raise ValueError(f'CRC incorrecto en {bad}')


def baseline() -> None:
    dest = DOCS / 'conservacion_inicial.json'
    if dest.exists():
        return
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode('utf-8').strip('\0').split('\0')
    save(dest, {'commit_base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'rama': subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
                'archivos': {name: digest(ROOT / name) for name in files if (ROOT / name).is_file()}})


def acquire(years: list[int]) -> dict:
    baseline()
    old = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}
    records = {r['year']: r for r in old.get('fuentes', [])}
    s2 = json.loads((ROOT / 'config/fuentes_sprint2.json').read_text(encoding='utf-8'))
    for year in years:
        url = URL.format(year=year)
        prior = records.get(year)
        if prior and prior.get('status') == 'disponible':
            path = ROOT / prior['path']
            if not path.exists() or digest(path) != prior['sha256']:
                raise ValueError(f'Cambió o falta el original registrado de {year}; no se reemplaza')
            print(f'{year}: original registrado conservado', flush=True)
            continue
        # Reutilizar sin copiar los originales del Sprint 2.
        path = ROOT / f'data/source/sprint-2/originales/BD_{year}.xlsx'
        if path.exists():
            ref = next(r for r in s2['fuentes'] if r['archivo'] == f'02_fuentes/BD_{year}.xlsx')
            sha = digest(path)
            if sha != ref['sha256']:
                raise ValueError(f'El original {year} no coincide con la evidencia del Sprint 2')
            validate_xlsx(path)
            record = {'year': year, 'status': 'disponible', 'path': path.relative_to(ROOT).as_posix(),
                      'sha256': sha, 'bytes': path.stat().st_size, 'url': ref.get('url') or None,
                      'url_patron_solicitado': url, 'descargado_en_utc': None,
                      'origen': ref['procedencia'], 'reutilizado_sprint2': True,
                      'nota_fecha': 'Fecha de descarga original no acreditada; no se sustituye por la fecha de inventario.'}
        else:
            path = SOURCE / f'BD_{year}.xlsx'
            if path.exists():
                raise ValueError(f'{path} existe sin registro; inspeccionar antes de descargar, no sobrescribir')
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_suffix('.xlsx.part')
            if partial.exists():
                raise ValueError(f'Existe una descarga parcial previa: {partial}')
            attempt = datetime.now(timezone.utc).isoformat()
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'CalidadAireJalisco-Sprint3-inventario/1.0'})
                with urllib.request.urlopen(req, timeout=90) as response, partial.open('xb') as dest:
                    final_url = response.url
                    status = response.status
                    headers = {k: response.headers.get(k) for k in ['Content-Type', 'Content-Length', 'Last-Modified', 'ETag']}
                    while block := response.read(1024 * 1024):
                        dest.write(block)
                validate_xlsx(partial)
                partial.rename(path)
                record = {'year': year, 'status': 'disponible', 'path': path.relative_to(ROOT).as_posix(),
                          'sha256': digest(path), 'bytes': path.stat().st_size, 'url': url,
                          'url_final': final_url, 'descargado_en_utc': datetime.now(timezone.utc).isoformat(),
                          'inicio_solicitud_utc': attempt, 'http_status': status, 'http_headers': headers,
                          'origen': 'Descarga oficial SEMADET para inventario Sprint 3', 'reutilizado_sprint2': False}
            except (urllib.error.URLError, TimeoutError, ValueError, zipfile.BadZipFile, OSError) as error:
                # No guardar HTML u otras respuestas como si fueran Excel originales.
                if partial.exists():
                    partial.unlink()
                record = {'year': year, 'status': 'no_disponible', 'url': url,
                          'intento_en_utc': attempt, 'error': f'{type(error).__name__}: {error}'}
        records[year] = record
        manifest = {'ventana': [2015, 2024], 'estacion': 'MIR / Miravalle',
                    'nota': 'Originales sin edición; 2023–2024 reutilizados sin duplicar ni fingir fecha de descarga.',
                    'fuentes': [records[y] for y in sorted(records)]}
        save(MANIFEST, manifest)
        print(f"{year}: {record['status']} {record.get('bytes', '')} {record.get('error', '')}", flush=True)
    return {'fuentes': [records[y] for y in sorted(records)]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--years', type=int, nargs='+', default=list(range(2015, 2025)))
    args = parser.parse_args()
    if any(y < 2015 or y > 2024 for y in args.years):
        parser.error('La ventana autorizada es 2015–2024')
    acquire(args.years)
