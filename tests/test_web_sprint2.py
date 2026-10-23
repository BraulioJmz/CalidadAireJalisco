"""Control de resultados y denominadores web contra CSV reales, no literales HTML."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'pipeline'))
import exportar_sprint2_web as W

@pytest.fixture(scope='module')
def data():
    value=json.loads((ROOT/'web/data/sprint2.json').read_text(encoding='utf-8'))
    return W.validate(value)

@pytest.mark.parametrize('pol',['PM10','PM2.5','CO'])
def test_december_values_and_denominators_from_daily_pairs(data,pol):
    pairs=pd.read_csv(ROOT/'data/processed/sprint-2/pares_diarios.csv',float_precision='round_trip')
    z=pairs[pairs.pollutant.eq(pol)&pairs.month.eq(12)]
    r=next(r for r in data['comparisons'] if r['pollutant']==pol and r['month']==12)
    assert r['n']==len(z)==31 and r['expected']==31 and r['comparable']
    assert r['a']==pytest.approx(z.a.mean(),abs=1e-10)
    assert r['b']==pytest.approx(z.b.mean(),abs=1e-10)
    assert r['change_pct']==pytest.approx(100*(z.b.mean()-z.a.mean())/z.a.mean(),abs=1e-10)
    for year in [2023,2024]:
        daily=pd.read_csv(ROOT/f'data/processed/sprint-2/MIR_{year}_diario.csv',float_precision='round_trip')
        days=daily[daily.MONTH.eq(12)]
        p=next(v for v in data['periods'] if v['year']==year and v['month']==12 and v['pollutant']==pol)
        assert p['valid']==days[f'C_{pol}'].notna().sum()
        assert p['counts']==[int(days[f'C_{pol}'].eq(i).sum()) for i in range(5)]
        if pol=='CO': assert p['counts'][0]==p['valid']==p['expected']==31

def test_web_artifact_is_fresh_and_source_files_are_not_public(data):
    assert W.build()==data
    for name,digest in data['processedHashes'].items():
        assert hashlib.sha256((ROOT/'data/processed/sprint-2'/name).read_bytes()).hexdigest()==digest
    for resource in data['downloads']:
        public=ROOT/'web/public'/resource['url'].lstrip('/')
        assert public.read_bytes()==(ROOT/'data/processed/sprint-2'/resource['name']).read_bytes()
    assert not list((ROOT/'web/public/descargas/sprint-2').rglob('*.xlsx'))

@pytest.mark.parametrize('kind',['unit','counts','dimension','missing','meteo','coverage','profile','comparison'])
def test_contract_rejects_data_changes(data,kind):
    d=copy.deepcopy(data)
    if kind=='unit': d['pollutants'][0]['unit']='ppm'
    elif kind=='counts': d['periods'][0]['counts'][0]+=1
    elif kind=='dimension': d['profiles'].pop()
    elif kind=='missing':
        r=next(r for r in d['periods'] if r['valid']==0);r['mean']=0
    elif kind=='meteo': d['meteorology'][0]['n']+=1
    elif kind=='coverage': d['coverage'][0]['usable']+=1
    elif kind=='profile': d['profiles'][0]['bad']+=1
    else: d['comparisons'][1]['delta']+=1
    with pytest.raises(ValueError): W.validate(d)

def test_episodes_keep_real_cross_year_duration_and_figures_exist(data):
    rows=[r for r in data['episodes'] if r['pollutant']=='PM10' and r['crossYear']]
    assert len(rows)==1
    row=rows[0]
    assert row['start']=='2023-12-31' and row['end']=='2024-01-03' and row['days']==4
    for fig in data['figures']:
        for key in ['svg','png']:
            path=ROOT/'web/public'/fig[key].lstrip('/')
            assert path.is_file() and path.stat().st_size>5000

def test_nulls_and_meteorology_use_exact_exported_points(data):
    r=next(r for r in data['periods'] if r['pollutant']=='O3' and r['year']==2023 and r['month']==1)
    assert r['valid']==0 and r['mean'] is None and r['badPct'] is None
    source=json.loads((ROOT/'data/processed/sprint-2/resumen.json').read_text(encoding='utf-8'))
    assert data['meteorology']==source['meteorology']
    assert not any(r['pollutant']=='NO2' for r in data['comparisons'])
