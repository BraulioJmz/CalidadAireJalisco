"""Cotejo semántico de los 24 resultados: no exige bytes trigonométricos idénticos."""
import argparse
import json
import math
from pathlib import Path
from verificar_sprint2 import compare_tables

def compare_json(a,b,where=''):
    if a is None or b is None or isinstance(a,(str,bool)) or isinstance(b,(str,bool)):
        return [] if type(a)==type(b) and a==b else [where]
    if isinstance(a,dict) and isinstance(b,dict):
        if a.keys()!=b.keys(): return [where+':keys']
        return [v for k in a for v in compare_json(a[k],b[k],where+'/'+k)]
    if isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b): return [where+':length']
        return [v for i,(x,y) in enumerate(zip(a,b)) for v in compare_json(x,y,where+f'/{i}')]
    if isinstance(a,int) and isinstance(b,int): return [] if a==b else [where]
    if isinstance(a,(float,int)) and isinstance(b,(float,int)):
        exact={'categories','counts','valid','missing','bad','expected','n','category','available_category','year','month','hour'}
        if any(part in exact for part in where.split('/')): return [] if a==b else [where]
        return [] if math.isclose(a,b,rel_tol=0,abs_tol=1e-10) else [where]
    return [] if a==b else [where]

def compare(expected,actual):
    names=sorted(p.name for p in expected.iterdir() if p.suffix in ['.csv','.json'])
    observed=sorted(p.name for p in actual.iterdir() if p.suffix in ['.csv','.json'])
    if len(names)!=24 or names!=observed: raise ValueError('Se requieren los mismos 24 resultados')
    rows=[]
    for name in names:
        if name.endswith('.csv'):
            details=compare_tables(expected/name,actual/name)
            differences=sum(r['diferencias'] for r in details)
        else:
            details=compare_json(json.loads((expected/name).read_text(encoding='utf-8')),json.loads((actual/name).read_text(encoding='utf-8')))
            differences=len(details)
        rows.append({'archivo':name,'diferencias':differences,'detalle':details})
    return {'status':'APROBADO' if not any(r['diferencias'] for r in rows) else 'FALLOS',
            'tolerancia_continua':1e-10,'categorias_fechas_textos_ausencias':'exactos','archivos':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--esperado',type=Path,required=True);p.add_argument('--actual',type=Path,required=True);p.add_argument('--informe',type=Path,required=True)
    a=p.parse_args();r=compare(a.esperado,a.actual);a.informe.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':r['status'],'archivos':len(r['archivos'])}));raise SystemExit(0 if r['status']=='APROBADO' else 1)
