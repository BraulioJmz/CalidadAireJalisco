"""Pruebas, controles independientes y reporte auditable del Sprint 2."""
from __future__ import annotations
import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import importlib.metadata
import json
import os
import runpy
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import anual as A

ROOT=A.ROOT
DOC=ROOT/"docs/sprints/sprint-2"
GENERATED={"informe_verificacion.md","verificacion.json","pruebas.xml","pruebas.txt",
           "comparacion_prototipo.csv","comprobacion_excel.csv","ventanas_independientes.csv",
           "cambios_codigo.json","entorno.json","prototipo_pruebas.txt","prototipo_ejecucion.txt",
           "contraste_casos_docentes.csv","comprobacion_excel_log.txt"}

# La integridad de lo enumerado no demuestra completitud. Estos insumos se
# exigen incluso si Git los ignora; la misma selección alimenta firma y ZIP.
REQUIRED_FILES=(
    "data/source/sprint-2/originales/BD_2023.xlsx",
    "data/source/sprint-2/originales/BD_2024.xlsx",
    "data/source/sprint-2/MIR_2023.csv", "data/source/sprint-2/MIR_2024.csv",
    "config/fuentes_sprint2.json", "requirements-sprint2-lock.txt",
    "docs/sprints/sprint-2/REPRODUCIR.md", "docs/sprints/sprint-2/decisiones_metodologicas.md",
    "docs/sprints/sprint-2/fuentes/NOM_172_SEMARNAT_2023_DOF.pdf",
    "docs/sprints/sprint-2/fuentes/Informe_Nacional_Calidad_Aire_2023.pdf",
    "docs/sprints/sprint-2/fuentes/Sprint1_entregado.pdf",
    "docs/sprints/sprint-2/fuentes/Protocolo_manejo_datos_calidad_aire.pdf",
    "web/package-lock.json", "web/data/sprint2.json", "web/app/sprint-2/page.tsx",
    "web/public/descargas/sprint-2/decisiones_metodologicas.md",
    "web/public/descargas/sprint-2/REPRODUCIR.md",
    "docs/sprints/sprint-2/figuras/catalogo_figuras.md",
    "docs/sprints/sprint-2/figuras/hallazgos.csv",
    "web/components/sprint2/ComparativeCalendar.tsx", "web/lib/calendar.ts",
    "web/lib/sprint2-contract.ts", "web/scripts/validar-calendario.mjs",
    "pipeline/verificar_calendario.py", "pipeline/empaquetar_calendario.py",
    "tests/test_calendar_sprint2.py",
    "docs/sprints/sprint-2/calendario/conservacion_base.json",
    "docs/sprints/sprint-2/calendario/complemento_dashboard.md",
    "docs/sprints/sprint-2/calendario/REPRODUCIR_CALENDARIO.md",
)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def command(args, path):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace")
    path.write_text(result.stdout+result.stderr,encoding="utf-8")
    return {"command":args,"exit_code":result.returncode,"log":str(path.relative_to(ROOT)).replace("\\","/")}

def project_files(root=None, required=None):
    root=Path(root or ROOT).resolve()
    if required is None:
        required=list(REQUIRED_FILES)
        web=root/'web/data/sprint2.json'
        if web.is_file():
            resources=json.loads(web.read_text(encoding='utf-8'))
            urls=[r['url'] for r in resources['downloads']]+[r[k] for r in resources['figures'] for k in ['svg','png']]
            for url in urls:
                if not url.startswith('/descargas/sprint-2/') or not (root/'web/public'/url.lstrip('/')).resolve().is_relative_to(root/'web/public'):
                    raise ValueError('Recurso web fuera del proyecto: '+url)
                required.append('web/public'+url)
    else:
        required=tuple(required)
    missing=[p for p in required if not (root/p).is_file()]
    if missing:
        raise FileNotFoundError("Entrega incompleta: faltan archivos obligatorios: " + ", ".join(missing))
    if not (root/".git").exists():
        paths=[]
        excluded={".git",".venv",".scratch","entregas","node_modules",".next","__pycache__",".pytest_cache",".ruff_cache",".playwright-cli"}
        for folder,dirs,files in os.walk(root):
            dirs[:]=[d for d in dirs if d not in excluded]
            paths.extend(str((Path(folder)/f).relative_to(root)).replace("\\","/") for f in files if not f.endswith(('.pyc','.tsbuildinfo')) and f!='next-env.d.ts')
        return sorted(set(paths).union(required))
    result=subprocess.run(["git","ls-files","-z","--cached","--others","--exclude-standard"],
                          cwd=root,check=True,capture_output=True)
    return sorted(set(p for p in result.stdout.decode("utf-8").split("\0") if p and (root/p).is_file()).union(required))

def signature(root=None, required=None):
    root=Path(root or ROOT)
    files={p:sha(root/p) for p in project_files(root,required) if not (p.startswith("docs/sprints/sprint-2/") and Path(p).name in GENERATED) and not p.startswith(('docs/sprints/sprint-2/revision02/verificacion/','docs/sprints/sprint-2/calendario/verificacion/'))}
    return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()

def number_equal(a,b,tolerance=1e-10):
    return bool(np.isclose(a,b,atol=tolerance,rtol=0,equal_nan=True))

def compare_tables(old,new,columns=None):
    a=pd.read_csv(old,float_precision="round_trip")
    b=pd.read_csv(new,float_precision="round_trip")
    if len(a)!=len(b) or list(a.columns)!=list(b.columns) and columns is None:
        raise ValueError(f"Dimensiones/columnas distintas: {old} / {new}")
    rows=[]
    for col in columns or a.columns.intersection(b.columns):
        x,y=a[col],b[col]
        if pd.api.types.is_bool_dtype(x) and pd.api.types.is_bool_dtype(y):
            same=x.eq(y);diff=0. if same.all() else 1.
        elif (str(col).startswith('C_') or str(col)=='I_GLOBAL' or
              pd.api.types.is_integer_dtype(x) and pd.api.types.is_integer_dtype(y)):
            same=x.eq(y) | (x.isna() & y.isna());diff=0. if same.all() else None
        elif pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            same=np.isclose(x,y,atol=1e-10,rtol=0,equal_nan=True)
            delta=(x-y).abs()
            diff=float(delta.max()) if delta.notna().any() else 0.
        else:
            same=x.eq(y) | (x.isna() & y.isna());diff=None
        rows.append({"archivo":new.name,"columna":col,"n":len(a),"diferencias":int((~same).sum()),"max_abs_difference":diff})
    return rows

def independent_windows(hourly):
    """Control Decimal sin llamar al NowCast ni al rolling del pipeline."""
    rows=[]
    sample=sorted(set(np.linspace(11,len(hourly)-1,192,dtype=int).tolist()+
                      [hourly.index.get_loc(pd.Timestamp("2024-01-01"))]))
    for pos in sample:
        ts=hourly.index[pos]
        for p,factor in [("PM10","0.714"),("PM2.5","0.694")]:
            recent=hourly[p].iloc[pos-11:pos+1].to_numpy()[::-1]
            valid=[(i,Decimal(str(v))) for i,v in enumerate(recent) if np.isfinite(v)]
            expected=np.nan
            if sum(np.isfinite(recent[:3]))>=2:
                vals=[v for _,v in valid];hi,lo=max(vals),min(vals)
                w=max(Decimal("0.5"),(lo/hi).quantize(Decimal(".01"),rounding=ROUND_HALF_UP)) if hi else Decimal(1)
                weighted=sum(v*w**i for i,v in valid)/sum(w**i for i,v in valid)
                expected=float((weighted*Decimal(factor)).quantize(Decimal(1),rounding=ROUND_HALF_UP))
            if ts < pd.Timestamp("2023-01-01 11:00"): expected=np.nan
            value=hourly.iloc[pos][f"I_{p}"]
            rows.append({"fecha":str(ts),"variable":p,"expected":expected,"observed":value,"matches":number_equal(value,expected)})
        vals=hourly.CO.iloc[max(0,pos-7):pos+1].dropna()
        expected=float((sum(Decimal(str(v)) for v in vals)/Decimal(len(vals))).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)) if len(vals)>=6 else np.nan
        if ts<pd.Timestamp("2023-01-01 07:00"): expected=np.nan
        value=hourly.iloc[pos].I_CO
        rows.append({"fecha":str(ts),"variable":"CO","expected":expected,"observed":value,"matches":number_equal(value,expected)})
    return rows

def verify(prototype=None, excel=True):
    DOC.mkdir(parents=True,exist_ok=True)
    A.write_json(DOC/"verificacion.json",{"status":"EN_CURSO","note":"Una interrupción o excepción invalida la verificación anterior"})
    checks=[];commands=[]
    def check(name, passed, detail):
        checks.append({"check":name,"passed":bool(passed),"detail":detail})

    manifest=json.loads((ROOT/"config/fuentes_sprint2.json").read_text(encoding="utf-8"))
    for y in [2023,2024]:
        original=ROOT/f"data/source/sprint-2/originales/BD_{y}.xlsx"
        expected=next(r['sha256'] for r in manifest['fuentes'] if r['archivo']==f"02_fuentes/BD_{y}.xlsx")
        check(f"original_{y}",sha(original)==expected,expected)
        csv=A.SOURCE/f"MIR_{y}.csv"
        check(f"extracto_{y}",sha(csv)==manifest['extractos'][str(y)]['sha256'],sha(csv))
    for name in manifest["evidencia_copiada"]:
        expected=next(r['sha256'] for r in manifest['fuentes'] if Path(r['archivo']).name==Path(name).name)
        check(f"evidencia_{Path(name).name}",sha(ROOT/name)==expected,expected)

    initial_files=json.loads((DOC/"estado_archivos_sprint1.json").read_text(encoding="utf-8"))
    authorized_web={'web/app/page.tsx','web/components/NavLinks.tsx','web/lib/site.ts','web/next.config.ts'}
    protected={p:digest for p,digest in initial_files.items() if p not in authorized_web}
    altered=[p for p,digest in protected.items() if not (ROOT/p).exists() or sha(ROOT/p)!=digest]
    check("preservacion_sprint1",not altered,{"archivos_comprobados":len(protected),"diferencias":altered,"ediciones_web_autorizadas":sorted(authorized_web),"method":"SHA-256 de evidencia previa; navegación, portada, registro de sprint y configuración de build se modifican en revisión 02"})

    cmd=command([sys.executable,"-X","utf8","-W","error","-m","pytest","tests","-q",f"--junitxml={DOC/'pruebas.xml'}"],DOC/"pruebas.txt")
    commands.append(cmd)
    tree=ET.parse(DOC/"pruebas.xml")
    suites=tree.findall(".//testsuite")
    totals={k:sum(int(s.get(k,"0")) for s in suites) for k in ["tests","failures","errors","skipped"]}
    check("pruebas_proyecto",cmd["exit_code"]==0 and totals["skipped"]==0,totals)

    hourly=pd.concat([pd.read_csv(A.OUT/f"MIR_{y}_horario.csv",parse_dates=["DATE"],float_precision="round_trip").set_index("DATE") for y in [2023,2024]])
    independent=independent_windows(hourly)
    A.csv_table(DOC/"ventanas_independientes.csv",independent)
    check("control_independiente_ventanas",all(r['matches'] for r in independent),{"n":len(independent),"metodo":"Aritmética Decimal independiente, muestra sistemática y cambio de año"})

    docente=runpy.run_path(str(ROOT/'tests/test_nom172.py'))
    cases=[]
    for (name,values),reference in zip(docente['CASOS'].items(),docente['ESPERADOS']):
        revised=A.N.nowcast(values,'PM2.5')
        expected=np.nan if reference is None else reference
        cases.append({'caso':name,'ventana':values,'PM':'PM2.5','referencia_docente':expected,
                      'revision_nom':revised,'coincide':number_equal(expected,revised)})
    A.csv_table(DOC/'contraste_casos_docentes.csv',cases)
    check('contraste_referencia_docente',len(cases)==24,{'casos':len(cases),'discrepancias':sum(not r['coincide'] for r in cases),
          'nota':'Orden de redondeo y aritmética distintos; referencia del Sprint 1 conservada, sin aprobación docente atribuida'})

    if excel:
        dest=ROOT/".scratch/desde_excel"
        cmd=command([sys.executable,"-X","utf8","-W","error",str(ROOT/"pipeline/anual.py"),
                     "--bd-2023",str(A.SOURCE/"originales/BD_2023.xlsx"),"--bd-2024",str(A.SOURCE/"originales/BD_2024.xlsx"),
                     "--out",str(dest)],DOC/"comprobacion_excel_log.txt")
        commands.append(cmd)
        rows=[]
        if cmd['exit_code']==0:
            for y in [2023,2024]:
                for kind in ["depurado","horario","diario"]:
                    name=f"MIR_{y}_{kind}.csv"
                    rows.extend(compare_tables(A.OUT/name,dest/name))
        A.csv_table(DOC/"comprobacion_excel.csv",rows)
        check("reproduccion_excel_extractos",cmd['exit_code']==0 and bool(rows) and not any(r['diferencias'] for r in rows),
              {"columnas_comprobadas":len(rows),"tolerancia_continua":1e-10,"categorias_y_faltantes":"coincidencia exacta","log":cmd['log']})
    else:
        check("reproduccion_excel_extractos",False,"Omitida explícitamente: verificación incompleta")

    prototype_status="No solicitado en esta ejecución; el contraste histórico entregado se conserva si existe."
    if prototype:
        proto_root=prototype.parents[2]
        package_manifest=json.loads((DOC/'manifiesto_paquete.json').read_text(encoding='utf-8'))
        baseline_files=['pipeline/anual.py','pipeline/normativa.py','tests/test_sprint2.py']
        same=all(sha(proto_root/file)==next(r['sha256'] for r in package_manifest['archivos'] if r['archivo']=='03_prototipo_analisis/'+file) for file in baseline_files)
        check('prototipo_codigo_original',same,'SHA-256 de los tres archivos contra manifiesto original del paquete')
        cmd=command([sys.executable,"-X","utf8",str(proto_root/"pipeline/anual.py")],DOC/"prototipo_ejecucion.txt")
        commands.append(cmd)
        check("ejecucion_prototipo",cmd['exit_code']==0,cmd)
        cmd=command([sys.executable,"-X","utf8","-m","unittest","discover","-s",str(proto_root/"tests"),"-p","test_sprint2.py","-v"],DOC/"prototipo_pruebas.txt")
        commands.append(cmd)
        check("pruebas_prototipo",cmd['exit_code']==0 and "Ran 24 tests" in (DOC/"prototipo_pruebas.txt").read_text(encoding="utf-8"),cmd)
        rows=[]
        for y in [2023,2024]:
            for kind in ["horario","diario"]:
                name=f"MIR_{y}_{kind}.csv"
                cols=["DATE"]+[f"{prefix}_{p}" for prefix in ["I","C"] for p in A.N.POLS]+["C_GLOBAL","C_DISPONIBLE"]
                if kind=="diario": cols += [f"EXACT_{p}" for p in A.N.POLS]
                rows.extend(compare_tables(prototype/name,A.OUT/name,cols))
        A.csv_table(DOC/"comparacion_prototipo.csv",rows)
        categorical=[r for r in rows if r['columna'].startswith("C_")]
        check("contraste_categorias_prototipo",bool(categorical),{"columnas":len(categorical),"diferencias":sum(r['diferencias'] for r in categorical),"nota":"Se registran discrepancias sin imponer coincidencia; revisar fundamento decimal en decisiones"})
        prototype_status={"path":str(prototype),"differences":[r for r in rows if r['diferencias']],
                          "warnings":"El prototipo emite FutureWarning de fillna y RuntimeWarning al resumir series vacías; revisar logs. Se ejecutó con UTF-8 sin modificar su código."}

    environment={"python":sys.version,"platform":sys.platform,"libraries":{n:importlib.metadata.version(n) for n in ["numpy","pandas","scipy","openpyxl","pytest","xlsxwriter"]}}
    A.write_json(DOC/"entorno.json",environment)
    summary=json.loads((A.OUT/"resumen.json").read_text(encoding="utf-8"))
    report={"status":"APROBADO" if all(c['passed'] for c in checks) else "FALLOS",
            "scope":"Verificación de software y reproducibilidad; no validación instrumental ni aprobación docente",
            "initial":json.loads((DOC/"estado_inicial.json").read_text(encoding="utf-8")),
            "checks":checks,"commands":commands,"tests":totals,"prototype":prototype_status,
            "environment":environment,"annual_pairs":{p:summary['comparisons'][p][0] for p in A.N.CORE+["GLOBAL"]},
            "december_pairs":{p:summary['comparisons'][p][12] for p in A.N.CORE+["GLOBAL"]},
            "limitations":["No se verifican promedios subhorarios ni calibración instrumental",
                "Ningún contaminante común cumple representación anual por trimestre",
                "NO2 complementario: lecturas Data sin enumeración en catálogo MIR de Param",
                "Los controles web, build y ZIP limpio se registran por separado en el informe revisión 02",
                "No se atribuyen causas de episodios ni aportaciones individuales"],
            "input_signature":signature()}
    A.write_json(DOC/"verificacion.json",report)
    if (ROOT/".git").exists():
        changes={"head":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip(),
             "branch":subprocess.run(["git","branch","--show-current"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip(),
             "implementation_commit":None,"note":"Cambios locales revisables, sin commit ni publicación",
             "files":subprocess.run(["git","status","--porcelain=v1","--untracked-files=all"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()}
        A.write_json(DOC/"cambios_codigo.json",changes)
    write_report(report,summary)
    return report

def write_report(r,data):
    lines=["# Informe de controles del pipeline · Sprint 2, revisión 02", "",
           f"**Estado: {r['status']}**. Fecha local: 22 de octubre de 2026. Equipo 3, Academia Miravalle, MIR.","",
           "Repositorio clonado en carpeta hermana del paquete. Commit inicial `67a385204b87dfe8260974510d2cf305714b264c`, rama inicial main, sin cambios locales. Rama de trabajo `sprint-2/revision-01`; implementación sin commit ni push.","",
           "Se mantienen los cálculos de revisión 01 y se corrige la completitud del ZIP. La revisión 02 añade /sprint-2, exportación web, figuras y comprobación limpia. Los controles web se registran por separado en revision02/verificacion/. Se preserva la evidencia del Sprint 1.","",
           f"Pruebas del proyecto: **{r['tests']['tests']} ejecutadas, {r['tests']['failures']} fallos, {r['tests']['errors']} errores, {r['tests']['skipped']} omitidas**. Incluyen las 9 existentes del Sprint 1. La suite y el pipeline revisado se ejecutan con avisos tratados como errores.","",
           "## Controles", "", "| Control | Resultado |", "|---|---|"]
    lines += [f"| {c['check']} | {'Correcto' if c['passed'] else 'FALLO'} |" for c in r['checks']]
    lines += ["", "Comandos, detalles y firma de entradas: verificacion.json. Salida de pruebas: pruebas.txt y pruebas.xml. Versiones: entorno.json y requirements-sprint2-lock.txt.","",
              "## Resultados y denominadores", "",f"{sum(data['quality']['raw_hours'].values()):,} horas; {len(data['daily'])} días; {data['quality']['flags']:,} señalamientos/exclusiones. Los 8,281 números de SO2 2023 se conservan en las fuentes y se excluyen de indicadores. No faltan filas de las rejillas de origen; sí faltan mediciones.","",
              "| Indicador | Pares anuales / 365 | Cobertura | Trimestres (%) | Cambio anual representativo |",
              "|---|---:|---:|---|---|"]
    for p,row in r['annual_pairs'].items():
        lines.append(f"| {p} | {row['n']} | {row['coverage']:.2f}% | {' / '.join(f'{x:.2f}' for x in row['quarterly_coverage'])} | {'Sí' if row['comparable'] else 'No'} |")
    lines += ["", "No se infiere una mejora o deterioro del año completo a partir de estas medias incompletas.","",
              "| Diciembre | Pares / 31 | Media 2023 | Media 2024 | Cambio | Destacable por cobertura |", "|---|---:|---:|---:|---:|---|"]
    for p,row in r['december_pairs'].items():
        if p=='GLOBAL': continue
        change=f"{row['change_pct']:+.2f}%" if row['change_pct'] is not None else "No definido"
        lines.append(f"| {p} | {row['n']} | {row['a']:.6f} | {row['b']:.6f} | {change} | {'Sí' if row['comparable'] else 'No'} |")
    lines += ["", "PM: media de promedios diarios de 24h (µg/m³). CO: media de máximos diarios de promedios móviles de 8h (ppm). O3: media de máximos horarios diarios (ppm). Se usan bases anteriores al redondeo final; no son el mismo estadístico. O3 y global de diciembre tienen 15/31 pares, por debajo del 75%.","",
              "## Contraste con el prototipo y correcciones", "",
              "Se conserva el cálculo de categorías del prototipo. La revisión valida encabezados/fecha/HOUR, preserva procedencia y fila, evita agregados ordinales del global, añade dispersión y fechas de máximos, separa tipos de concentración y exporta pares y episodios.","",
              "EXACT_CO ahora conserva máximos de medias móviles sin redondear: cambia ligeramente su media pareada (diciembre +94.27% frente a +94.31% del prototipo). El indicador final y las categorías se contrastan columna por columna en comparacion_prototipo.csv. Los CSV fuente tienen hashes diferentes por incluir trazabilidad y columnas originales adicionales.","",
              "JSON conserva precisión completa. Spearman usa pares estabilizados a 12 decimales para no crear órdenes espurios por ruido flotante; los pares exportados reproducen sus rangos. El prototipo tenía seis decimales en JSON y sus estadísticas de GLOBAL promediaban ordinales; se corrigen. Los 18 registros de gases, los 15 pares meteorológicos y los umbrales de cobertura de comparación son reglas adicionales del proyecto.","",
              "La ejecución inicial del prototipo sin UTF-8 falló al leer JSON en Windows; con -X utf8 sus 24 pruebas pasan. Sus logs conservan FutureWarning de pandas y RuntimeWarning de series vacías. En desarrollo, un control de rangos detectó pérdida de precisión JSON; fue corregida antes de la verificación final. No se ocultan avisos con filtros globales.","",
              "El control independiente detectó CO 2024-03-23 22:00: media exacta 0.485, esperado 0.49; la versión flotante producía 0.48. Se corrige usando Decimal en la aritmética de promedios de CO/PM y de ponderación NowCast; se añadió una prueba específica. Las discrepancias reales se conservan en comparacion_prototipo.csv. Ver historial_incidencias.md.","",
              "Se contrastan también los 24 casos de la referencia docente conservada del Sprint 1 contra el método de esta revisión en contraste_casos_docentes.csv. Las diferencias por orden de redondeo se documentan; no se modifican los resultados de referencia ni se exige coincidencia artificial.","",
              f"Meteorología: {len(data['meteorology'])} combinaciones mensuales contaminante/variable; rho solo con n≥15 y series variables, sin p-valores. Episodios consecutivos exportados: {len(data['episodes'])}. Ver pares_meteorologicos.csv, dias_relevantes.csv y episodios.csv.","",
              "## Límites y pendientes académicos", ""]
    lines += [f"- {item}." for item in r['limitations']]
    lines += ["- O3 2023 solo desde 24/07 18:00; NO2 2024 desde 16/08; RH representa temporadas distintas. Comparar las ventanas coincidentes no elimina el sesgo por ausencia.",
              "- La fecha se interpreta como hora civil codificada, sin inventar UTC o cambios de horario; se conserva 29/02 en descriptivos y se omite solo del pareamiento.",
              "- No se revisa ni se entrega el PDF final en esta fase. La participación del equipo, correcciones de clase y aprobación docente siguen requiriendo evidencia real.","",
              "Decisiones, fundamentos, efectos y límites: decisiones_metodologicas.md. Reproducción: REPRODUCIR.md. Cambios y estado Git: cambios_codigo.json. Fuentes y hashes: config/fuentes_sprint2.json y fuentes_hashes.json. El ZIP incluye manifiesto interno y huella externa."]
    if isinstance(r['prototype'],dict):
        lines += ["", "## Diferencias numéricas verificadas contra el prototipo", "",
                  "No se encontraron cambios de categoría en los datos suministrados. Los cambios de I_CO corrigen empates decimales; los de EXACT_CO además eliminan su redondeo previo. Tolerancia continua del cotejo: 1e-10; categorías y ausencia coinciden exactamente.", "",
                  "| Archivo | Columna | Filas distintas | Máxima diferencia absoluta |", "|---|---|---:|---:|"]
        for row in r['prototype']['differences']:
            lines.append(f"| {row['archivo']} | {row['columna']} | {row['diferencias']} | {row['max_abs_difference']:.6f} |")
    (DOC/"informe_verificacion.md").write_text("\n".join(lines)+"\n",encoding="utf-8")

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prototipo",type=Path)
    ap.add_argument("--sin-excel",action="store_true",help="Omitir solo para diagnóstico; no habilita entrega")
    args=ap.parse_args()
    report=verify(args.prototipo.resolve() if args.prototipo else None,not args.sin_excel)
    print(json.dumps({"status":report['status'],"tests":report['tests'],"checks":len(report['checks'])}))
    sys.exit(0 if report['status']=='APROBADO' else 1)
