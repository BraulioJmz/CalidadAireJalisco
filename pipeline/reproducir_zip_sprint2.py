"""Validación autosuficiente del ZIP en carpeta temporal y entornos nuevos.

Solo biblioteca estándar en este orquestador; los cálculos se ejecutan con código,
datos, locks y dependencias de la extracción. No consulta el repositorio original.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

def extract_verified(archive,work):
    # tempfile puede devolver un alias Windows 8.3. Canonicalizar ambos lados
    # antes de comprobar límites evita rechazar un destino realmente seguro.
    work=Path(work).resolve();work.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None: raise ValueError('CRC incorrecto')
        manifest=json.loads(z.read('MANIFIESTO_SHA256.json'))
        for item in manifest['archivos']:
            if hashlib.sha256(z.read(item['archivo'])).hexdigest()!=item['sha256']: raise ValueError('SHA interno incorrecto')
        for name in z.namelist():
            if not (work/name).resolve().is_relative_to(work): raise ValueError('Ruta de extracción fuera del temporal')
        z.extractall(work)
    return manifest

def reproduce(archive,report_path):
    work=Path(tempfile.mkdtemp(prefix='miravalle_sprint2_')).resolve()
    logs=work/'logs';logs.mkdir()
    result={'status':'EN_CURSO','zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'temporary_directory':str(work),'steps':[],
            'aislamiento':'Extracción sin Git; venv nuevo y npm ci del lock extraído. Sin usar .venv, node_modules, paquetes o datos del checkout original.'}
    report_path.parent.mkdir(parents=True,exist_ok=True)
    def save(): report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    save();server=None
    try:
        manifest=extract_verified(archive,work)
        root=work/'CalidadAireJalisco';assert not (root/'.git').exists()
        sources=json.loads((root/'config/fuentes_sprint2.json').read_text(encoding='utf-8'))
        for y in [2023,2024]:
            p=root/f'data/source/sprint-2/originales/BD_{y}.xlsx'
            expected=next(r['sha256'] for r in sources['fuentes'] if r['archivo']==f'02_fuentes/BD_{y}.xlsx')
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise ValueError(f'Original {y} ausente/alterado')
        result['manifest_files']=len(manifest['archivos']);result['originales']='Ambos presentes y hashes correctos';save()
        environment=os.environ.copy();environment.pop('PYTHONPATH',None);environment.pop('VIRTUAL_ENV',None)
        def run(name,args,cwd=root):
            print('COMPROBANDO '+name,flush=True)
            cmd=subprocess.run([str(x) for x in args],cwd=cwd,env=environment,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=900)
            (logs/(name+'.txt')).write_text(cmd.stdout+cmd.stderr,encoding='utf-8')
            result['steps'].append({'name':name,'exit_code':cmd.returncode,'log':str(logs/(name+'.txt'))});save()
            if cmd.returncode: raise RuntimeError(name+' falló: '+(cmd.stdout+cmd.stderr)[-2500:])
            return cmd.stdout
        base=getattr(sys,'_base_executable',sys.executable)
        run('01_entorno_python',[base,'-m','venv',str(work/'env')])
        python=work/'env'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        run('02_instalacion_lock_python',[python,'-m','pip','install','-r',root/'requirements-sprint2-lock.txt'])
        run('03_originales_a_resultados',[python,'-X','utf8','-W','error',root/'pipeline/anual.py','--bd-2023',root/'data/source/sprint-2/originales/BD_2023.xlsx','--bd-2024',root/'data/source/sprint-2/originales/BD_2024.xlsx','--out',work/'desde_originales'])
        run('04_cotejo_24_resultados',[python,'-X','utf8',root/'pipeline/comprobar_resultados_sprint2.py','--esperado',root/'data/processed/sprint-2','--actual',work/'desde_originales','--informe',logs/'comparacion_24.json'])
        # El camino de extractos se ejecuta separado; no depende del primer resultado.
        run('05_extractos_a_resultados',[python,'-X','utf8','-W','error',root/'pipeline/anual.py','--out',work/'desde_extractos'])
        run('06_cotejo_extractos',[python,'-X','utf8',root/'pipeline/comprobar_resultados_sprint2.py','--esperado',root/'data/processed/sprint-2','--actual',work/'desde_extractos','--informe',logs/'comparacion_extractos.json'])
        run('07_exportacion_web',[python,'-X','utf8','-W','error',root/'pipeline/exportar_sprint2_web.py'])
        run('08_pruebas_pipeline',[python,'-X','utf8','-W','error','-m','pytest','tests','-q'])
        npm='npm.cmd' if os.name=='nt' else 'npm'
        run('09_instalacion_lock_web',[npm,'ci','--no-audit','--no-fund'],root/'web')
        run('10_contrato_typescript',['node','scripts/validar-sprint2.mjs'],root/'web')
        run('11_tipos',[npm,'run','lint'],root/'web')
        run('12_build_produccion',[npm,'run','build'],root/'web')
        web=json.loads((root/'web/data/sprint2.json').read_text(encoding='utf-8'))
        result['web_schema']=web['schema'];result['dias_calendario']=len(web.get('daily',[]))
        resources=[v['url'] for v in web['downloads']]+[v[k] for v in web['figures'] for k in ['svg','png']]
        for path in resources:
            p=root/'web/public'/path.lstrip('/')
            if not p.is_file(): raise FileNotFoundError('Recurso web ausente: '+path)
        # Arranque real de producción de la extracción. Directorio y binario Next propios.
        print('COMPROBANDO 13_arranque_http',flush=True)
        server_log=(logs/'13_servidor.txt').open('w',encoding='utf-8')
        server=subprocess.Popen(['node',str(root/'web/node_modules/next/dist/bin/next'),'start','--hostname','127.0.0.1','--port','3013'],cwd=root/'web',env=environment,stdout=server_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        for _ in range(60):
            if server.poll() is not None: raise RuntimeError('Servidor limpio terminó antes de arrancar')
            try:
                with urllib.request.urlopen('http://127.0.0.1:3013/sprint-2',timeout=2) as response:
                    if response.status==200: break
            except OSError: time.sleep(.5)
        else: raise RuntimeError('No arrancó el servidor de producción extraído')
        routes=['/','/sprint-1','/sprint-2','/metodologia']+resources
        statuses=[]
        for route in routes:
            with urllib.request.urlopen('http://127.0.0.1:3013'+route,timeout=10) as response:
                statuses.append({'route':route,'status':response.status,'bytes':len(response.read())})
        result['http']=statuses
        result['steps'].append({'name':'13_arranque_http','exit_code':0,'rutas':len(statuses)})
        result['status']='APROBADO';result['comparison']=json.loads((logs/'comparacion_24.json').read_text(encoding='utf-8'))
    except Exception as error:
        result['status']='FALLOS';result['error']=str(error)
    finally:
        if server:
            server.terminate();server.wait(timeout=30)
        save()
    print(json.dumps({'status':result['status'],'steps':len(result['steps']),'informe':str(report_path)}),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--zip',type=Path,required=True);p.add_argument('--informe',type=Path,required=True)
    args=p.parse_args();r=reproduce(args.zip.resolve(),args.informe.resolve());sys.exit(0 if r['status']=='APROBADO' else 1)
