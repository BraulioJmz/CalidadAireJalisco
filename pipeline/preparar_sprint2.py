"""Verifica el paquete y preserva originales; nunca descarga ni modifica fuentes.

python pipeline/preparar_sprint2.py --paquete ../Sprint2_Miravalle_Para_Codex/Sprint2_Miravalle_Para_Codex
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import pandas as pd
import anual as A

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def copy_verified(source, destination):
    if destination.exists() and sha(source) != sha(destination):
        raise ValueError(f"No se sobrescribirá un archivo diferente: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists(): shutil.copy2(source, destination)

def prepare(package):
    package=package.resolve()
    manifest=json.loads((package/"MANIFIESTO_SHA256.json").read_text(encoding="utf-8"))
    for item in manifest["archivos"]:
        source=(package/item["archivo"]).resolve()
        if not source.is_relative_to(package): raise ValueError("Ruta ajena al paquete")
        if sha(source)!=item["sha256"]: raise ValueError(f"Hash incorrecto: {source}")
    sources=json.loads((package/"fuentes.json").read_text(encoding="utf-8"))
    for item in sources["fuentes"]:
        if sha(package/item["archivo"])!=item["sha256"]: raise ValueError("fuentes.json no coincide")
    extracted={}
    for year in [2023,2024]:
        source=package/"02_fuentes"/f"BD_{year}.xlsx"
        dest=A.SOURCE/"originales"/source.name
        copy_verified(source,dest)
        raw=A.source_extract(dest,year)
        csv=A.SOURCE/f"MIR_{year}.csv"
        param=pd.read_excel(dest,sheet_name="Param",header=None)
        units=param.iloc[1:,-3:].dropna(subset=[param.columns[-2]])
        units.columns=["parametro","abreviatura","unidad"]
        units.to_csv(A.SOURCE/f"parametros_{year}.csv",index=False)
        station=param[param.iloc[:,1].astype(str).str.strip().eq("MIR")]
        catalog={"contaminantes":str(station.iloc[0,2]),"meteorologia":str(station.iloc[0,3])}
        extracted[str(year)]={"archivo":str(csv.relative_to(A.ROOT)).replace("\\","/"),
            "sha256":sha(csv),"bytes":csv.stat().st_size,"n_filas":int(raw.SOURCE_ROW.sum()),
            "rejilla_esperada":len(raw),"periodo":[str(raw.index.min()),str(raw.index.max())],
            "transformaciones":["Filtro STATION=MIR", "Encabezados strip y upper", "Añade archivo y número de fila Excel; mediciones originales sin imputación"],
            "unidades":{**A.N.UNITS,"ET":"°C","IT":"°C (interior de caseta)","RH":"%","WS":"m/s","WD":"grados","PP":"mm","ATM":"mmHg","RS":"W/m²","UVI":"mW/m²"},
            "catalogo_MIR":catalog,
            "NO2_procedencia":"Lecturas de Data; revisar procedencia instrumental. El catálogo MIR de Param no enumera NO2 en 2024; se conserva solo como complemento exploratorio.",
            "unidades_meteo":"Según hoja Param del mismo Excel, preservada en parametros_AAAA.csv; PP, ATM, RS y UVI no entran en correlaciones."}
    evidence=["NOM_172_SEMARNAT_2023_DOF.pdf","Informe_Nacional_Calidad_Aire_2023.pdf",
              "Sprint1_entregado.pdf","Protocolo_manejo_datos_calidad_aire.pdf"]
    for name in evidence:
        copy_verified(package/"02_fuentes"/name,A.ROOT/"docs/sprints/sprint-2/fuentes"/name)
    copy_verified(package/"MANIFIESTO_SHA256.json",A.ROOT/"docs/sprints/sprint-2/manifiesto_paquete.json")
    sources["extractos"]=extracted
    sources["manifest_verified_files"]=len(manifest["archivos"])
    sources["normativa_url"]="https://sidof.segob.gob.mx/notas/docFuente/5715154"
    sources["copias_originales"]=[f"data/source/sprint-2/originales/BD_{y}.xlsx" for y in [2023,2024]]
    sources["evidencia_copiada"]=[f"docs/sprints/sprint-2/fuentes/{n}" for n in evidence]
    A.write_json(A.ROOT/"config/fuentes_sprint2.json",sources)
    return sources

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paquete",type=Path,required=True)
    result=prepare(parser.parse_args().paquete)
    print(json.dumps({"archivos_verificados":result["manifest_verified_files"],"extractos":result["extractos"]},ensure_ascii=False))
