"""Controles de la ampliación de calendario; conserva informes históricos anteriores."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from verificar_sprint2 import ROOT, signature

OUT=ROOT/'docs/sprints/sprint-2/calendario/verificacion'
VISUAL=ROOT/'output/playwright/calendario_2026-10-23/revision_visual.json'

def verify():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'status':'EN_CURSO','scope':'Verificación local del calendario; extracción limpia se registra por separado','steps':[]}
    def save(): (OUT/'local.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    save()
    try:
        baseline=json.loads((ROOT/'docs/sprints/sprint-2/calendario/conservacion_base.json').read_text(encoding='utf-8'))
        changed=[p for p,h in baseline.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
        if changed: raise ValueError('Archivos protegidos modificados: '+', '.join(changed))
        report['protected_unchanged']=len(baseline)
        visual=json.loads(VISUAL.read_text(encoding='utf-8'))
        if visual['status']!='REVISADO' or visual['browser_checks']!=38: raise ValueError('Revisión de navegador incompleta')
        for p,h in {**visual['code_hashes'],**visual['screenshots']}.items():
            if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h: raise ValueError('Evidencia visual desactualizada: '+p)
        npm='npm.cmd' if sys.platform=='win32' else 'npm'
        tasks=[('npm_ci',[npm,'ci','--no-audit','--no-fund'],ROOT/'web'),
               ('contrato_y_recorrido',['node','scripts/validar-sprint2.mjs'],ROOT/'web'),
               ('tipos',[npm,'run','lint'],ROOT/'web'),('build',[npm,'run','build'],ROOT/'web'),
               ('pruebas',[sys.executable,'-X','utf8','-W','error','-m','pytest','tests','-q'],ROOT)]
        for name,args,cwd in tasks:
            print('COMPROBANDO '+name,flush=True)
            r=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace')
            (OUT/(name+'.txt')).write_text(r.stdout+r.stderr,encoding='utf-8')
            report['steps'].append({'name':name,'exit_code':r.returncode,'command':args,'log':name+'.txt'});save()
            if r.returncode: raise RuntimeError(name+' falló: '+(r.stdout+r.stderr)[-2000:])
        report['input_signature']=signature()
        report['status']='APROBADO'
    except Exception as error:
        report['status']='FALLOS';report['error']=str(error)
    save();print(json.dumps({'status':report['status'],'error':report.get('error')}),flush=True)
    return report

if __name__=='__main__':
    sys.exit(0 if verify()['status']=='APROBADO' else 1)
