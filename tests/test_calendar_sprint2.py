"""Calendario: cotejo de todas las fechas/valores contra los CSV diarios verificados."""
import copy
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
    return W.load_json(ROOT/'web/data/sprint2.json')

@pytest.mark.parametrize('year',[2023,2024])
def test_each_day_matches_processed_csv(data,year):
    csv=pd.read_csv(ROOT/f'data/processed/sprint-2/MIR_{year}_diario.csv',float_precision='round_trip')
    days=[r for r in data['daily'] if r['year']==year]
    assert len(days)==len(csv)
    for day,(_,source) in zip(days,csv.iterrows()):
        assert (day['date'],day['year'],day['month'],day['day'],day['expected'])==(source.DATE,source.YEAR,source.MONTH,source.DAY,source.HORAS_ESPERADAS)
        for p in W.A.N.CORE:
            for key,col in [('indicator','I'),('exact','EXACT'),('category','C'),('readings','N'),('indicators','N_IND')]:
                value=source[f'{col}_{p}']
                assert day['pollutants'][p][key]==(None if pd.isna(value) else value)
        for variable in ['ET','RH','WS']:
            value=source[f'M_{variable}']
            assert day['weather'][variable]=={'value':None if pd.isna(value) else value,'readings':source[f'N_{variable}']}

def test_leap_day_and_missing_are_different(data):
    feb={y:[r for r in data['daily'] if r['year']==y and r['month']==2] for y in [2023,2024]}
    assert len(feb[2023])==28 and len(feb[2024])==29
    assert feb[2024][-1]['date']=='2024-02-29'
    assert all(r['date']!='2023-02-29' for r in data['daily'])
    january=[r['pollutants']['O3'] for r in data['daily'] if r['year']==2023 and r['month']==1]
    assert len(january)==31 and all(r['category'] is None and r['indicator'] is None and r['readings']==0 for r in january)

@pytest.mark.parametrize('year,bad',[(2023,15),(2024,27)])
def test_december_zero_is_buena_not_missing(data,year,bad):
    days=[r for r in data['daily'] if r['year']==year and r['month']==12]
    assert len(days)==31
    assert sum(r['pollutants']['CO']['category']==0 for r in days)==31
    assert all(r['pollutants']['CO']['indicator'] is not None for r in days)
    assert sum(r['pollutants']['PM10']['category'] is not None and r['pollutants']['PM10']['category']>=2 for r in days)==bad

@pytest.mark.parametrize('kind',['date','missing_day','category','zero_missing','count','weather','statistic','period_count'])
def test_calendar_export_rejects_corruption(data,kind):
    d=copy.deepcopy(data)
    if kind=='date': d['daily'][424]['date']='2023-02-29'
    elif kind=='missing_day': d['daily'].pop()
    elif kind=='category': d['daily'][0]['pollutants']['PM10']['category']=5
    elif kind=='zero_missing': d['daily'][0]['pollutants']['O3']['category']=0
    elif kind=='count': d['daily'][0]['pollutants']['CO']['readings']=25
    elif kind=='weather': d['daily'][0]['weather']['RH']={'value':0,'readings':0}
    elif kind=='statistic': d['dailyStatistics']['CO']['label']='Media de concentración horaria'
    else:
        r=next(r for r in d['daily'] if r['date']=='2023-12-01')['pollutants']['CO']
        r['category']=1
    with pytest.raises(ValueError): W.validate(d)
