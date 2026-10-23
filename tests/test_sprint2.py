"""Pruebas de norma, calidad, comparación y reconciliación de la revisión anual."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"pipeline"))
import anual as A
import normativa as N

def synthetic(start="2024-01-01", periods=24):
    df=pd.DataFrame(np.nan,index=pd.date_range(start,periods=periods,freq="h"),columns=N.POLS+A.METEO)
    df.index.name="DATE"
    df["SOURCE_ROW"]=True
    return df

@pytest.mark.parametrize("pol",N.POLS)
def test_all_band_boundaries_and_missing(pol):
    for i,limit in enumerate(N.BANDS[pol]):
        assert N.category(limit,pol)==i
        assert N.category(limit+10**-N.DEC[pol],pol)==i+1
    for value in [np.nan,-1,np.inf,-np.inf]: assert pd.isna(N.category(value,pol))
    assert N.category(0,pol)==0

@pytest.mark.parametrize("value,dec,expected",[(62.5,0,63),(.0585,3,.059),(11.035,2,11.04),(9.4,0,9),(9.5,0,10),(.0955,3,.096),(.0954,3,.095),(11.324,2,11.32)])
def test_normative_half_up(value,dec,expected):
    assert N.half_up(value,dec)==expected

def test_annex_examples():
    assert N.nowcast([50,80,75,90,82,53,64,74,21,10,16,13],"PM2.5")==12
    assert N.nowcast([118,97,130,142,146,144,141,134,147,150,141,103],"PM10")==92

def test_final_rounding_and_zero():
    assert N.nowcast([62.5]*12,"PM10")==45
    assert N.nowcast([0]*12,"PM2.5")==0
    assert pd.isna(N.nowcast([np.nan]*12,"PM10"))

def test_recent_hours_and_gap_age():
    assert pd.isna(N.nowcast([90]*9+[np.nan,np.nan,20],"PM10"))
    assert N.nowcast([np.nan]*9+[100,np.nan,10],"PM10")==20
    assert not pd.isna(N.nowcast([90]*9+[30,np.nan,20],"PM10"))

def test_invalid_window_and_non_hourly_index_rejected():
    with pytest.raises(ValueError): N.nowcast([],"PM10")
    with pytest.raises(ValueError): N.nowcast([1]*13,"PM10")
    with pytest.raises(ValueError): N.indicators(synthetic(periods=4).iloc[[0,2,3]])

def test_co_six_of_eight():
    df=synthetic(periods=8)
    df["CO"]=[1]*5+[np.nan]*3
    assert pd.isna(N.indicators(df).CO.iloc[-1])
    df.iloc[5,df.columns.get_loc("CO")]=1
    assert N.indicators(df).CO.iloc[-1]==1

def test_decimal_averaging_at_rounding_half():
    df=synthetic(periods=8);df.CO=[.41,.42,.43,.44,.53,.54,.55,.56]
    assert N.co_base(df.CO).iloc[-1]==.485
    assert N.indicators(df).CO.iloc[-1]==.49
    assert N.mean_decimal([76.1,76.2,77.2])==76.5

def base(year=2024):
    return pd.DataFrame({"STATION":[" mir "],"DATE":[f"{year}-01-01"],"dia ":[1],"mes ":[1],"HOUR":[0],"PM10":[20]})

def test_normalized_calendar_and_source_mask():
    for year,expected in [(2023,8760),(2024,8784)]:
        df=A.normalize(base(year),year)
        assert len(df)==expected and int(df.SOURCE_ROW.sum())==1
        assert A.normalize(df.reset_index(),year).SOURCE_ROW.equals(df.SOURCE_ROW)
        assert df.SO2.isna().all()

@pytest.mark.parametrize("field,value",[("HOUR",24),("HOUR",1),("DIA",2),("MES ",2),("DATE","2023-01-01"),("DATE","2024-01-01 00:01"),("DATE",None)])
def test_bad_calendar_rejected(field,value):
    df=base();df[field]=value
    with pytest.raises(ValueError): A.normalize(df,2024)

def test_duplicate_keys_and_headers_rejected():
    with pytest.raises(ValueError): A.normalize(pd.concat([base(),base()]),2024)
    df=base();df["pm10 "]=1
    with pytest.raises(ValueError): A.normalize(df,2024)

def test_non_numeric_original_preserved_in_log():
    df=base();df["PM10"]="sensor?";df["SOURCE_FILE"]="BD_2024.xlsx:Data";df["SOURCE_EXCEL_ROW"]=5
    normalized=A.normalize(df,2024)
    clean,log=A.prepare(normalized)
    assert clean.PM10.isna().all()
    assert log.iloc[0].valor_original=="sensor?"
    assert log.iloc[0].fila_excel==5 and log.iloc[0].fuente=="BD_2024.xlsx:Data"

def test_official_so2_outlier_and_negative():
    df=synthetic("2023-02-01",3)
    df["SO2"]=[.02]*3;df["PM10"]=[600,-1,0];df["PM2.5"]=[700,1,0]
    clean,log=A.prepare(df)
    assert clean.SO2.isna().all()
    assert clean['PM2.5'].iloc[0]==700
    assert clean.PM10.iloc[0]==600 and pd.isna(clean.PM10.iloc[1]) and clean.PM10.iloc[2]==0
    assert "PM2.5 > PM10" in log.regla.values
    assert set(A.LOG_COLUMNS).issubset(log.columns)

def test_daily_18_hours_is_required_pm_and_project_gases():
    df=synthetic(periods=48)
    for p in N.CORE:
        df.loc[df.index[:18],p]=10 if p.startswith("PM") else .02
        df.loc[df.index[24:41],p]=10 if p.startswith("PM") else .02
    h,d=A.calculate(df)
    for p in N.CORE:
        assert pd.notna(d.iloc[0][f"I_{p}"])
        assert pd.isna(d.iloc[1][f"I_{p}"])
    assert d.iloc[0].C_GLOBAL==0 and pd.isna(d.iloc[1].C_GLOBAL)

def test_global_available_ties_and_comparable_partial():
    df=synthetic();df.PM10=100;df['PM2.5']=50
    h,d=A.calculate(df)
    assert pd.isna(d.iloc[0].C_GLOBAL) and d.iloc[0].C_DISPONIBLE==2
    assert d.iloc[0].DETERMINANTES=="PM10;PM2.5"
    assert bool(d.iloc[0].CORE_PARCIAL) and bool(d.iloc[0].GLOBAL_PARCIAL)

def test_no2_complement_can_change_only_available():
    df=synthetic()
    for p in N.CORE: df[p]=1 if p.startswith("PM") else .01
    df.NO2=.3
    _,d=A.calculate(df)
    assert d.iloc[0].C_GLOBAL==0 and d.iloc[0].C_DISPONIBLE==4
    assert d.iloc[0].DETERMINANTES=="NO2"

def test_context_cross_year_and_unknown_2022_warmup():
    df=synthetic("2023-12-31",48)
    df.PM10=100;df['PM2.5']=50;df.CO=1
    h,_=A.calculate(df)
    assert h.loc['2024-01-01 00:00','I_PM10']==71
    assert h.loc['2024-01-01 00:00','I_CO']==1
    start=synthetic("2023-01-01",24)
    start.PM10=100;start['PM2.5']=50;start.CO=1
    h,_=A.calculate(start)
    assert h.I_PM10.iloc[:11].isna().all() and h.I_PM10.iloc[11]==71
    assert h.I_CO.iloc[:7].isna().all() and h.I_CO.iloc[7]==1

def test_daily_co_exact_precedes_final_rounding():
    df=synthetic();df.CO=1.005
    _,d=A.calculate(df)
    assert d.iloc[0].EXACT_CO==pytest.approx(1.005)
    assert d.iloc[0].I_CO==1.01

def test_wind_circular_with_effective_pairs_and_calm():
    df=synthetic();df.WD=[359,1]*12;df.WS=1
    _,d=A.calculate(df)
    angle=d.iloc[0].M_WD
    assert min(abs(angle),abs(360-angle))<1e-8
    assert d.iloc[0].N_PARES_WD_WS==24
    df.WS=0
    _,d=A.calculate(df)
    assert pd.isna(d.iloc[0].M_WD) and d.iloc[0].N_PARES_WD_WS==0

def pair_frame():
    idx=pd.date_range('2023-01-01','2024-12-31',freq='D')
    return pd.DataFrame({'YEAR':idx.year,'MONTH':idx.month,'DAY':idx.day,'EXACT_PM10':1.,'I_GLOBAL':0.},index=idx)

def test_pairing_leap_day_and_thresholds():
    df=pair_frame();df.loc['2024-02-29','EXACT_PM10']=10000
    r=A.pairs(df,"PM10")
    assert r['n']==365 and r['b']==1 and '02-29' not in r['dates']
    assert r['comparable'] and sum(q['expected'] for q in r['quarterly_n'])==365
    df.loc['2024-07-01':'2024-07-31','EXACT_PM10']=np.nan
    r=A.pairs(df,"PM10")
    assert r['coverage']>75 and not r['comparable']
    df=pair_frame();df.loc['2024-01-01':'2024-01-07','EXACT_PM10']=np.nan
    assert A.pairs(df,"PM10",1)['comparable']
    df.loc['2024-01-08','EXACT_PM10']=np.nan
    assert not A.pairs(df,"PM10",1)['comparable']

@pytest.fixture(scope="module")
def outputs():
    out=ROOT/'data/processed/sprint-2'
    # La ausencia es un fallo de entrega, nunca un skip silencioso.
    summary=json.loads((out/'resumen.json').read_text(encoding='utf-8'))
    daily=pd.concat([pd.read_csv(out/f'MIR_{y}_diario.csv',parse_dates=['DATE']).set_index('DATE') for y in [2023,2024]])
    return out,summary,daily

def test_calendars_availability_and_no_ordinal_means(outputs):
    _,data,d=outputs
    assert len(d)==731 and pd.Timestamp('2024-02-29') in d.index
    assert d.loc[:'2023-07-23','I_O3'].isna().all()
    assert d.I_SO2.isna().all()
    for r in data['annual']+data['monthly']+data['profiles']+data['available']:
        assert sum(r['counts'])==r['valid'] and r['valid']+r['missing']==r['expected']
        if r.get('pollutant')=='GLOBAL': assert not any(k in r for k in ['mean','median','max','std'])
    for r in data['coverage']:
        assert r['usable']+r['excluded']+r['missing_measurements']+r['absent_rows']==r['expected']

def test_global_completeness_and_ties(outputs):
    _,data,d=outputs
    assert d.C_GLOBAL.notna().equals(d[[f'C_{p}' for p in N.CORE]].notna().all(axis=1))
    assert len(d.loc['2024-03'])==31 and pd.isna(d.loc['2024-03-07','C_GLOBAL'])
    assert any(len(r['pollutants'])>1 for r in data['dominance'])
    assert data['comparisons']['GLOBAL'][0]['n']==62
    assert all(not data['comparisons'][p][0]['comparable'] for p in N.CORE)

def test_meteorology_counts_and_ranks(outputs):
    out,data,_=outputs
    pts=pd.read_csv(out/'pares_meteorologicos.csv')
    for r in data['meteorology']:
        assert r['n']==len(r['points'])
        if r['n']<15: assert r['rho'] is None
        else:
            z=np.array([p[1:] for p in r['points']])
            a=pd.Series(z[:,0]).rank();b=pd.Series(z[:,1]).rank()
            rho=a.corr(b)
            if pd.notna(rho): assert r['rho']==pytest.approx(rho,abs=1e-6)
    assert len(pts)==sum(r['n'] for r in data['meteorology'])

def test_exports_pair_counts_and_episode_reconciliation(outputs):
    out,data,d=outputs
    pairs=pd.read_csv(out/'pares_diarios.csv')
    assert not pairs.date_2024.str.endswith('02-29').any()
    for p in A.METRICS:
        assert pairs.pollutant.eq(p).sum()==data['comparisons'][p][0]['n']
    for r in data['episodes']:
        z=d.loc[r['start']:r['end']]
        assert len(z)==r['days'] and z[f"C_{r['pollutant']}"].ge(2).all()
    assert pd.read_csv(out/'horas_relevantes.csv').shape[0]==len(data['hourly_peaks'])

def test_source_hashes_and_so2_log_count(outputs):
    out,data,_=outputs
    for year,expected in data['source_hashes'].items():
        assert hashlib.sha256((A.SOURCE/f'MIR_{year}.csv').read_bytes()).hexdigest()==expected
    log=pd.read_csv(out/'bitacora_calidad.csv')
    assert log.regla.eq('Invalidación oficial').sum()==8281
    assert len(log)==9847
    assert log.fuente.notna().all() and log.fila_excel.notna().all()

def test_verifier_compares_flags_and_magnitudes(tmp_path):
    from verificar_sprint2 import compare_tables
    a=tmp_path/'a.csv';b=tmp_path/'b.csv'
    pd.DataFrame({'flag':[True,False],'value':[1.,np.nan]}).to_csv(a,index=False)
    pd.DataFrame({'flag':[True,False],'value':[1.,np.nan]}).to_csv(b,index=False)
    assert all(r['diferencias']==0 for r in compare_tables(a,b))

def test_hourly_states_and_category_counts(outputs):
    out,data,_=outputs
    for y in [2023,2024]:
        h=pd.read_csv(out/f'MIR_{y}_horario.csv')
        assert len(h)==data['quality']['raw_hours'][str(y)]
        assert h.I_SO2.isna().all()
        assert h.C_GLOBAL.notna().equals(h[[f'C_{p}' for p in N.CORE]].notna().all(axis=1))
        for p in N.POLS:
            assert sum(h[f'C_{p}'].eq(i).sum() for i in range(5))==h[f'C_{p}'].notna().sum()
            assert h[f'ESTADO_{p}'].isin(['fila_ausente','medicion_faltante','exclusion_documentada','utilizable']).all()
    log=pd.read_csv(out/'bitacora_calidad.csv')
    assert set(log.accion)=={'Excluir de indicadores','Conservar y revisar'}
