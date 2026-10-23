"""Regresiones reales de completitud: una exclusión Git no puede ocultar insumos."""
import subprocess
import zipfile
import json
import hashlib
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"pipeline"))
from empaquetar_sprint2 import archive_project
from verificar_sprint2 import signature

def repository(tmp_path):
    root=tmp_path/"repo";root.mkdir()
    subprocess.run(["git","init",str(root)],check=True,capture_output=True)
    (root/".gitignore").write_text("obligatorio.xlsx\n",encoding="utf-8")
    (root/"obligatorio.xlsx").write_bytes(b"fuente original controlada")
    assert subprocess.run(["git","check-ignore","obligatorio.xlsx"],cwd=root,capture_output=True).returncode==0
    return root

def test_ignored_source_is_packaged_and_changes_signature(tmp_path):
    root=repository(tmp_path);target=tmp_path/"entrega.zip";required=["obligatorio.xlsx"]
    before=signature(root,required)
    archive_project(root,target,required)
    with zipfile.ZipFile(target) as z:
        assert z.read("CalidadAireJalisco/obligatorio.xlsx")==b"fuente original controlada"
    (root/"obligatorio.xlsx").write_bytes(b"otra fuente")
    assert signature(root,required)!=before

def test_missing_required_source_prevents_any_archive(tmp_path):
    root=repository(tmp_path);(root/"obligatorio.xlsx").unlink()
    target=tmp_path/"no_debe_existir.zip"
    with pytest.raises(FileNotFoundError,match="obligatorio.xlsx"):
        archive_project(root,target,["obligatorio.xlsx"])
    assert not target.exists()
    with pytest.raises(FileNotFoundError,match="obligatorio.xlsx"):
        signature(root,["obligatorio.xlsx"])

def test_cross_platform_comparison_preserves_categories_and_nulls():
    from comprobar_resultados_sprint2 import compare_json
    assert not compare_json({'M_WD':359.123},{'M_WD':359.123+8.53e-14})
    assert compare_json({'categories':{'PM10':1.}},{'categories':{'PM10':1.+1e-12}})
    assert compare_json({'value':None},{'value':0})
    assert compare_json({'date':'2024-01-01'},{'date':'2024-01-02'})

def test_zip_extraction_accepts_noncanonical_root(tmp_path,monkeypatch):
    from reproducir_zip_sprint2 import extract_verified
    archive=tmp_path/'sample.zip';payload=b'fuente controlada'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('CalidadAireJalisco/fuente.txt',payload)
        z.writestr('MANIFIESTO_SHA256.json',json.dumps({'archivos':[{'archivo':'CalidadAireJalisco/fuente.txt','sha256':hashlib.sha256(payload).hexdigest()}]}))
    monkeypatch.chdir(tmp_path)
    extract_verified(archive,Path('relative')/'..'/'clean')
    assert (tmp_path/'clean/CalidadAireJalisco/fuente.txt').read_bytes()==payload

def test_zip_path_escape_is_rejected_before_extraction(tmp_path):
    from reproducir_zip_sprint2 import extract_verified
    archive=tmp_path/'escape.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('MANIFIESTO_SHA256.json',json.dumps({'archivos':[]}));z.writestr('../outside.txt',b'invalido')
    with pytest.raises(ValueError,match='fuera del temporal'): extract_verified(archive,tmp_path/'clean')
    assert not (tmp_path/'outside.txt').exists()
