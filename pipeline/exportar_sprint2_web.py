"""Contrato y recursos web a partir de resultados procesados, sin segunda normativa.

python pipeline/exportar_sprint2_web.py
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import math
import calendar
import pandas as pd
import anual as A

ROOT=A.ROOT
COLORS=['#00e400','#ffff00','#ff7e00','#ff0000','#8f3f97']
POLLUTANTS=[
    {'key':'PM10','label':'PM₁₀','unit':'µg/m³','daily':'Media de promedios diarios de 24 h','hourly':'NowCast de 12 h'},
    {'key':'PM2.5','label':'PM₂.₅','unit':'µg/m³','daily':'Media de promedios diarios de 24 h','hourly':'NowCast de 12 h'},
    {'key':'O3','label':'O₃','unit':'ppm','daily':'Media de máximos horarios diarios','hourly':'Concentración base de una hora'},
    {'key':'CO','label':'CO','unit':'ppm','daily':'Media de máximos diarios móviles de 8 h','hourly':'Promedio móvil de 8 h'},
    {'key':'NO2','label':'NO₂','unit':'ppm','daily':'Media de máximos horarios diarios','hourly':'Concentración base de una hora'},
]
FIGURES=[
    ('01_mensual_pm10','¿Cómo cambió PM₁₀ en los días coincidentes de cada mes?'),
    ('02_diciembre_categorias','¿Cómo cambió la distribución diaria de partículas y CO en diciembre?'),
    ('03_cobertura','¿Qué meses permiten comparar las mediciones?'),
    ('04_patron_horario','¿En qué horarios fueron frecuentes las categorías desfavorables de PM₁₀?'),
    ('05_episodio_cruce','¿Cómo se extendió el episodio de PM₁₀ entre diciembre y enero?'),
    ('06_meteorologia','¿Cómo coincidieron PM₁₀ y la temperatura externa en diciembre de 2024?'),
]
DOWNLOADS=['monthly.csv','annual.csv','comparacion_pareada.csv','pares_diarios.csv','coverage.csv',
           'profiles.csv','meteorologia.csv','pares_meteorologicos.csv','dias_relevantes.csv',
           'horas_relevantes.csv','episodios.csv','dominance.csv','statistics.csv','bitacora_calidad.csv',
           'MIR_2023_diario.csv','MIR_2024_diario.csv']
DAILY_STATS={
    'PM10': {'label':'Promedio diario de 24 h','unit':'µg/m³'},
    'PM2.5': {'label':'Promedio diario de 24 h','unit':'µg/m³'},
    'O3': {'label':'Máximo horario diario','unit':'ppm'},
    'CO': {'label':'Máximo diario del promedio móvil de 8 h','unit':'ppm'},
}

def finite(v):
    return None if pd.isna(v) else float(v)

def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'),parse_constant=lambda x: (_ for _ in ()).throw(ValueError('JSON no finito: '+x)))

def validate(data):
    """Rechaza dimensiones, unidades y denominadores incoherentes antes de exportar."""
    if data['schema']!='mir-s2-v2' or data['reference']!=2024: raise ValueError('Versión/referencia web inesperada')
    if len(data['months'])!=12 or len(data['categories'])!=5: raise ValueError('Dimensiones de meses/categorías')
    if data['pollutants']!=POLLUTANTS: raise ValueError('Contrato de contaminantes/unidades alterado')
    if len(data['periods'])!=182: raise ValueError('Se esperaban 182 resúmenes de periodo')
    keys=set()
    for r in data['periods']:
        key=(r['year'],r['month'],r['pollutant'])
        if key in keys or r['year'] not in [2023,2024] or not 0<=r['month']<=12 or r['pollutant'] not in A.N.CORE+['GLOBAL','AVAILABLE','NO2']: raise ValueError('Llave de periodo inválida')
        keys.add(key)
        if len(r['counts'])!=5 or any(not isinstance(v,int) or v<0 for v in r['counts']): raise ValueError('Conteos inválidos')
        if sum(r['counts'])!=r['valid'] or r['valid']+r['missing']!=r['expected']: raise ValueError('Denominador diario incoherente')
        if r['bad']!=sum(r['counts'][2:]): raise ValueError('Numerador de Mala o peor incoherente')
        expected_pct=100*r['bad']/r['valid'] if r['valid'] else None
        if r['badPct']!=expected_pct: raise ValueError('Porcentaje sin denominador consistente')
        if r['valid']==0 and r['mean'] is not None: raise ValueError('Un faltante no es cero')
    if len(data['comparisons'])!=65 or len(data['profiles'])!=2304 or len(data['coverage'])!=390:
        raise ValueError('Dimensiones de comparaciones, patrón horario o cobertura incorrectas')
    if data.get('dailyStatistics')!=DAILY_STATS: raise ValueError('Estadísticos diarios inesperados')
    expected_dates=pd.date_range('2023-01-01','2024-12-31',freq='D')
    if len(data.get('daily',[]))!=len(expected_dates): raise ValueError('Dimensión del calendario diario incorrecta')
    for r,date in zip(data['daily'],expected_dates):
        if (r['date'],r['year'],r['month'],r['day'])!=(date.strftime('%Y-%m-%d'),date.year,date.month,date.day):
            raise ValueError('Fecha diaria inexistente, repetida o fuera de orden')
        if r['expected']!=24 or set(r['pollutants'])!=set(A.N.CORE) or set(r['weather'])!={'ET','RH','WS'}:
            raise ValueError('Dimensiones del detalle diario incorrectas')
        for p,v in r['pollutants'].items():
            if any(type(v[k]) is not int or not 0<=v[k]<=24 for k in ['readings','indicators']): raise ValueError('Conteo diario incorrecto')
            c=v['category']
            if c is not None and (type(c) is not int or not 0<=c<=4): raise ValueError('Categoría diaria incorrecta')
            if (c is None)!=(v['indicator'] is None) or (c is None)!=(v['exact'] is None): raise ValueError('Ausencia diaria incoherente')
            for k in ['indicator','exact']:
                if v[k] is not None and (not isinstance(v[k],(int,float)) or not math.isfinite(v[k]) or v[k]<0): raise ValueError('Indicador diario no finito/negativo')
        for v in r['weather'].values():
            if type(v['readings']) is not int or not 0<=v['readings']<=24: raise ValueError('Conteo meteorológico diario incorrecto')
            if v['value'] is not None and (v['readings']<18 or not math.isfinite(v['value'])): raise ValueError('Meteorología diaria insuficiente/no finita')
    # Reconciliar las categorías exportadas con todos los resúmenes existentes.
    for period in data['periods']:
        if period['pollutant'] not in A.N.CORE: continue
        selected=[r['pollutants'][period['pollutant']]['category'] for r in data['daily'] if r['year']==period['year'] and (not period['month'] or r['month']==period['month'])]
        if [selected.count(c) for c in range(5)]!=period['counts'] or selected.count(None)!=period['missing']:
            raise ValueError('Calendario no reconcilia con categorías/denominadores del periodo')
    for r in data['comparisons']:
        if r['n']>r['expected'] or not 0<=r['coverage']<=100: raise ValueError('Cobertura pareada inválida')
        if r['a']==0 and r['change_pct'] is not None: raise ValueError('Cambio relativo con base cero')
        if len(r['dates'])!=r['n']: raise ValueError('Fechas pareadas no reconcilian con n')
        if r['n']:
            delta=r['b']-r['a']
            if not math.isclose(r['delta'],delta,rel_tol=0,abs_tol=1e-10): raise ValueError('Diferencia absoluta incorrecta')
            if r['pollutant']!='GLOBAL' and r['a']!=0 and not math.isclose(r['change_pct'],100*delta/r['a'],rel_tol=0,abs_tol=1e-10): raise ValueError('Cambio relativo incorrecto')
    coverage_keys=set()
    for r in data['coverage']:
        key=(r['year'],r['month'],r['variable'])
        if key in coverage_keys: raise ValueError('Cobertura duplicada')
        coverage_keys.add(key)
        if r['usable']+r['absent_rows']+r['missing_measurements']+r['excluded']!=r['expected'] or r['source_rows']+r['absent_rows']!=r['expected']:
            raise ValueError('Estados de cobertura no reconcilian')
        if any(r[k]<0 for k in ['usable','expected','absent_rows','missing_measurements','excluded']): raise ValueError('Cobertura negativa')
    profile_keys=set()
    for r in data['profiles']:
        key=(r['year'],r['month'],r['hour'],r['pollutant'])
        if key in profile_keys or r['year'] not in [2023,2024] or r['pollutant'] not in A.N.CORE or not 1<=r['month']<=12 or not 0<=r['hour']<=23: raise ValueError('Llave de patrón horario inválida')
        profile_keys.add(key)
        if r['expected']!=calendar.monthrange(r['year'],r['month'])[1] or sum(r['counts'])!=r['valid'] or r['valid']+r['missing']!=r['expected'] or r['bad']>r['valid'] or r['bad']!=sum(r['counts'][2:]): raise ValueError('Patrón horario incoherente')
    for r in data['meteorology']:
        if r['n']!=len(r['points']) or (r['n']<15 and r['rho'] is not None): raise ValueError('Pares meteorológicos insuficientes/incoherentes')
        if r['rho'] is not None and not -1<=r['rho']<=1: raise ValueError('Spearman fuera de rango')
        if any(len(p)!=3 for p in r['points']): raise ValueError('Dimensión de par meteorológico incorrecta')
    for episode in data['episodes']:
        if (pd.Timestamp(episode['end'])-pd.Timestamp(episode['start'])).days+1!=episode['days']: raise ValueError('Duración del episodio incorrecta')
    def walk(value):
        if isinstance(value,float) and not math.isfinite(value): raise ValueError('Número no finito en recursos web')
        if isinstance(value,dict):
            for v in value.values(): walk(v)
        elif isinstance(value,list):
            for v in value: walk(v)
    walk(data)
    return data

def build(processed=A.OUT):
    source=load_json(processed/'resumen.json')
    daily=pd.concat([pd.read_csv(processed/f'MIR_{y}_diario.csv',parse_dates=['DATE'],float_precision='round_trip') for y in [2023,2024]]).set_index('DATE')
    hours=pd.concat([pd.read_csv(processed/f'MIR_{y}_horario.csv',parse_dates=['DATE'],float_precision='round_trip') for y in [2023,2024]]).set_index('DATE')
    periods=[];determinants=[]
    for year in [2023,2024]:
        for month in range(13):
            days=daily[daily.YEAR.eq(year)]
            if month: days=days[days.MONTH.eq(month)]
            for pol in A.N.CORE+['GLOBAL','AVAILABLE','NO2']:
                if pol=='AVAILABLE': r=next(r for r in source['available'] if r['year']==year and r['month']==month)
                else: r=next(r for r in (source['monthly'] if month else source['annual']) if r['year']==year and r.get('month',0)==month and r['pollutant']==pol)
                periods.append({'year':year,'month':month,'pollutant':pol,'counts':r['counts'],
                    'valid':r['valid'],'missing':r['missing'],'expected':r['expected'],'bad':r['bad'],'badPct':r['bad_pct'],
                    'mean':r.get('mean'),'median':r.get('median'),'sufficient':r['valid']>=math.ceil(.75*r['expected'])})
            for scope,column in [('GLOBAL','DETERMINANTES_GLOBAL'),('AVAILABLE','DETERMINANTES')]:
                vals=days[column].fillna('');counts={p:int(vals.str.split(';').map(lambda v:p in v).sum()) for p in A.N.POLS}
                determinants.append({'year':year,'month':month,'scope':scope,'days':int(vals.ne('').sum()),'counts':counts})
    events=[]
    for i,r in enumerate(source['events']):
        events.append({'id':f'd{i}','kind':'Máximo diario','pollutant':r['pollutant'],'date':r['date'],
            'year':r['year'],'month':r['month'],'value':r['value'],'raw':None,'category':r['category'],'n':r['n'],
            'selection':'Tres máximos diarios por año/contaminante, separados al menos 7 días; empates cronológicos.',
            'context':[{'t':p[0],'raw':p[1],'indicator':p[2]} for p in r['hours']]})
    for i,r in enumerate(source['hourly_peaks']):
        t=pd.Timestamp(r['date']);p=r['pollutant'];w=hours.loc[t-pd.Timedelta(hours=12):t+pd.Timedelta(hours=12)]
        events.append({'id':f'h{i}','kind':'Máximo horario','pollutant':p,'date':r['date'],'year':r['year'],'month':t.month,
            'value':r['indicator'],'raw':r['raw_concentration'],'category':r['category'],'n':None,'selection':r['selection'],
            'context':[{'t':str(t),'raw':finite(row[p]),'indicator':finite(row[f'I_{p}'])} for t,row in w.iterrows()]})
    episodes=[]
    for i,r in enumerate(source['episodes']):
        start,end=pd.Timestamp(r['start']),pd.Timestamp(r['end']);p=r['pollutant']
        w=daily.loc[start-pd.Timedelta(days=2):end+pd.Timedelta(days=2)]
        episodes.append({**r,'id':f'e{i}','crossYear':start.year!=end.year,
            'context':[{'t':str(t.date()),'raw':None,'indicator':finite(row[f'EXACT_{p}'])} for t,row in w.iterrows()]})
    comparisons=[{'pollutant':p,**copy.deepcopy(r)} for p in A.N.CORE+['GLOBAL'] for r in source['comparisons'][p]]
    # No se reconstruye normativa: estos indicadores/categorías vienen de los CSV/JSON calculados.
    calendar_days=[]
    for date,row in daily.iterrows():
        calendar_days.append({'date':date.strftime('%Y-%m-%d'),'year':int(row.YEAR),'month':int(row.MONTH),'day':int(row.DAY),
            'expected':int(row.HORAS_ESPERADAS),
            'pollutants':{p:{'indicator':finite(row[f'I_{p}']),'exact':finite(row[f'EXACT_{p}']),
                'category':None if pd.isna(row[f'C_{p}']) else int(row[f'C_{p}']),
                'readings':int(row[f'N_{p}']),'indicators':int(row[f'N_IND_{p}'])} for p in A.N.CORE},
            'weather':{v:{'value':finite(row[f'M_{v}']),'readings':int(row[f'N_{v}'])} for v in ['ET','RH','WS']}})
    result={'schema':'mir-s2-v2','station':'Miravalle (MIR)','agency':'Academia Miravalle','reference':2024,
        'daily':calendar_days,'dailyStatistics':copy.deepcopy(DAILY_STATS),
        'months':source['months'],'pollutants':POLLUTANTS,'categories':[{'name':n,'color':c} for n,c in zip(source['categories'],COLORS)],
        'periods':periods,'comparisons':comparisons,'coverage':source['coverage'],
        'profiles':[r for r in source['profiles'] if r['pollutant'] in A.N.CORE],
        'determinants':determinants,'meteorology':source['meteorology'],'events':events,'episodes':episodes,
        'quality':source['quality'],'rules':source['rules'],
        'downloads':[{'name':n,'url':'/descargas/sprint-2/'+n} for n in DOWNLOADS],
        'figures':[{'id':n,'question':q,'svg':'/descargas/sprint-2/figuras/'+n+'.svg','png':'/descargas/sprint-2/figuras/'+n+'.png'} for n,q in FIGURES],
        'source':'SEMADET · archivos suministrados · pipeline anual MIR',
        'processedHashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in processed.iterdir() if f.is_file()}}
    return validate(A.native(result))

def export(processed=A.OUT,web=ROOT/'web'):
    result=build(processed)
    A.write_json(web/'data/sprint2.json',result)
    dest=web/'public/descargas/sprint-2';dest.mkdir(parents=True,exist_ok=True)
    for name in DOWNLOADS: shutil.copy2(processed/name,dest/name)
    for name in ['decisiones_metodologicas.md','REPRODUCIR.md']:
        shutil.copy2(ROOT/'docs/sprints/sprint-2'/name,dest/name)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--processed',type=Path,default=A.OUT)
    parser.add_argument('--web',type=Path,default=ROOT/'web')
    args=parser.parse_args();data=export(args.processed,args.web)
    print(json.dumps({'schema':data['schema'],'periodos':len(data['periods']),'perfiles':len(data['profiles'])}))
