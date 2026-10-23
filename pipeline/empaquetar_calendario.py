"""Paquete actualizado del calendario, independiente de las entregas históricas."""
import argparse
import json
from pathlib import Path
from empaquetar_sprint2 import archive_project
from verificar_sprint2 import ROOT, signature

def package(destination):
    local=ROOT/'docs/sprints/sprint-2/calendario/verificacion/local.json'
    report=json.loads(local.read_text(encoding='utf-8'))
    if report.get('status')!='APROBADO' or report.get('input_signature')!=signature():
        raise ValueError('Verificación del calendario ausente o desactualizada: ejecute pipeline/verificar_calendario.py')
    if destination.exists(): raise FileExistsError('Conserve el ZIP existente y elija otro destino: '+str(destination))
    return archive_project(ROOT,destination)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=ROOT/'entregas/sprint2_calendario_comparativo.zip')
    package(p.parse_args().out)
