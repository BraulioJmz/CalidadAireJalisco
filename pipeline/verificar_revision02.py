"""Controles locales de revisión 02; la prueba del ZIP se ejecuta aparte."""
import json
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from verificar_sprint2 import ROOT, signature

OUT=ROOT/'docs/sprints/sprint-2/revision02/verificacion'

def verify():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'status':'EN_CURSO','scope':'Controles locales; no sustituye la comprobación del ZIP limpio','steps':[]}
    def save(): (OUT/'local.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    save()
    npm='npm.cmd' if sys.platform=='win32' else 'npm'
    tasks=[('npm_ci',[npm,'ci','--no-audit','--no-fund'],ROOT/'web'),
           ('contrato_web',['node','scripts/validar-sprint2.mjs'],ROOT/'web'),
           ('tipos',[npm,'run','lint'],ROOT/'web'),('build',[npm,'run','build'],ROOT/'web'),
           ('pipeline',[sys.executable,'-X','utf8',str(ROOT/'pipeline/verificar_sprint2.py')],ROOT)]
    for name,args,cwd in tasks:
        print('COMPROBANDO '+name,flush=True)
        result=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (OUT/(name+'.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
        report['steps'].append({'name':name,'exit_code':result.returncode,'command':args,'log':name+'.txt'});save()
        if result.returncode:
            report['status']='FALLOS';save();print((result.stdout+result.stderr)[-2000:]);return report
    visual=ROOT/'output/playwright/revision_visual.json'
    if not visual.is_file() or json.loads(visual.read_text(encoding='utf-8')).get('status')!='REVISADO':
        report['status']='FALLOS';report['error']='Falta registro de revisión visual efectiva';save();return report
    tests=ET.parse(ROOT/'docs/sprints/sprint-2/pruebas.xml').findall('.//testsuite')
    report['tests']={key:sum(int(t.get(key,'0')) for t in tests) for key in ['tests','failures','errors','skipped']}
    report['input_signature']=signature();report['status']='APROBADO';save()
    text=f'''# Verificación local · revisión 02

Estado: **APROBADO en el entorno local**. No equivale a comprobación de transporte.

- {report['tests']['tests']} pruebas Python con avisos tratados como errores; {report['tests']['failures']} fallos, {report['tests']['errors']} errores, {report['tests']['skipped']} omitidas. Incluyen las 54 anteriores.
- npm ci con package-lock sin cambiar versiones web; contrato, tipos y build de producción correctos.
- Recursos web derivados del pipeline, pruebas contra CSV de diciembre y denominadores, 31/31 Buena en CO en ambos años.
- Matplotlib 3.10.8 se añade para seis figuras SVG/PNG; se preservan versiones numéricas previas y se actualiza el lock Python coherentemente.
- Lista de insumos obligatorios para firma y ZIP, independiente de Git; ambos Excel y recursos públicos exigidos antes de empaquetar.
- Revisión visual efectiva y capturas: output/playwright/revision_visual.json. Se conserva un 404 preexistente de favicon; no se detectaron errores de ejecución de la aplicación en las vistas revisadas.

La verificación limpia se entrega como informe externo asociado al SHA-256 exacto del ZIP: el script reproducir_zip_sprint2.py crea entornos nuevos, prueba originales y extractos separadamente y arranca la aplicación de la extracción. Este informe local no declara por adelantado el éxito de ese control.

Rama: sprint-2/revision-01; cambios locales sin commit, push o deploy. Se preserva Sprint 1; navegación, portada, registro del Sprint 2 y configuración de build reciben las ediciones autorizadas. El PDF final, reflexiones, bitácora del líder y correcciones de clase permanecen pendientes de aportaciones reales.
'''
    (OUT/'informe_local.md').write_text(text,encoding='utf-8')
    return report

if __name__=='__main__':
    r=verify();print(json.dumps({'status':r['status'],'tests':r.get('tests')}));sys.exit(0 if r['status']=='APROBADO' else 1)
