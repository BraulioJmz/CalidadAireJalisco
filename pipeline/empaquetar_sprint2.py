"""Entrega ZIP con manifiesto de contenido y firma externa; exige controles vigentes."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from verificar_sprint2 import ROOT, DOC, project_files, signature

def package(destination):
    report=json.loads((DOC/"verificacion.json").read_text(encoding="utf-8"))
    if report['status']!='APROBADO' or report['input_signature']!=signature():
        raise ValueError("La verificación falta, tiene fallos o quedó desactualizada; ejecute verificar_sprint2.py")
    web_report=DOC/'revision02/verificacion/local.json'
    if not web_report.is_file(): raise ValueError('Falta la verificación local de revisión 02; ejecute verificar_revision02.py')
    local=json.loads(web_report.read_text(encoding='utf-8'))
    if local.get('status')!='APROBADO' or local.get('input_signature')!=signature():
        raise ValueError('Controles web ausentes o desactualizados; ejecute verificar_revision02.py')
    return archive_project(ROOT,destination)

def archive_project(root, destination, required=None):
    """Selección completa antes de escribir; se usa también en regresiones Git."""
    root=Path(root).resolve()
    selected=project_files(root,required)
    destination=destination.resolve()
    destination.parent.mkdir(parents=True,exist_ok=True)
    items=[]
    for relative in selected:
        path=root/relative
        if path.resolve()==destination or path.suffix.lower()=='.zip': continue
        if any(p in {".git",".venv","node_modules","__pycache__",".pytest_cache",".scratch",".next"} for p in path.relative_to(root).parts):
            raise ValueError(f"Dependencia/caché inesperada: {relative}")
        items.append((relative,path))
    files=[{"archivo":"CalidadAireJalisco/"+r,"bytes":p.stat().st_size,
            "sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for r,p in items]
    manifest={"archivos":files,"scope":"Proyecto, insumos originales, evidencia, cálculos y verificación; sin dependencias ni cachés"}
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for relative,path in items: archive.write(path,"CalidadAireJalisco/"+relative)
        archive.writestr("MANIFIESTO_SHA256.json",json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None: raise ValueError("CRC incorrecto en ZIP")
        for item in files:
            if hashlib.sha256(archive.read(item['archivo'])).hexdigest()!=item['sha256']:
                raise ValueError(f"SHA-256 de contenido incorrecto: {item['archivo']}")
    digest=hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix('.zip.sha256').write_text(f"{digest}  {destination.name}\n",encoding='utf-8')
    print(json.dumps({"zip":str(destination),"archivos":len(files),"bytes":destination.stat().st_size,"sha256":digest}))
    return destination

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=ROOT/'entregas/sprint2_revision_02.zip')
    package(ap.parse_args().out)
