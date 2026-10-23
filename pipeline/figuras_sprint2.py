"""Seis figuras de reporte desde el mismo contrato que consume la aplicación."""
import json
from pathlib import Path
import shutil
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
import anual as A
from exportar_sprint2_web import FIGURES, build

ROOT=A.ROOT
OUT=ROOT/'docs/sprints/sprint-2/figuras'
COLORS=['#00e400','#ffff00','#ff7e00','#ff0000','#8f3f97','#d2d7df']

def figures():
    d=build();OUT.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.labelcolor':'#33415a','text.color':'#17253d','axes.titleweight':'bold','svg.hashsalt':'mir-sprint2-revision02'})
    catalog=[]
    def save(fig,idx,filters,metric,denominator,finding,decision):
        name,question=FIGURES[idx]
        for ext in ['svg','png']:
            fig.savefig(OUT/f'{name}.{ext}',dpi=220,facecolor='white',bbox_inches='tight',metadata={'Creator':'Academia Miravalle · pipeline Sprint 2'})
        plt.close(fig)
        catalog.append({'archivo':name+'.svg / '+name+'.png','pregunta':question,'filtros':filters,'estadistico':metric,
            'denominador':denominator,'fuente':'data/processed/sprint-2/; contrato web exportado desde esos resultados',
            'decision':decision,'hallazgo':finding})
    def foot(fig,note):
        fig.text(.02,.012,textwrap.fill('Fuente: SEMADET · pipeline MIR · referencia retrospectiva 2024. '+note,155),fontsize=8,color='#526078',va='bottom')

    fig,ax=plt.subplots(figsize=(12,5.7));rows=[r for r in d['comparisons'] if r['pollutant']=='PM10' and r['month']>0]
    x=np.arange(1,13)
    for key,label,color in [('a','2023','#7a879d'),('b','2024','#2c56cf')]:
        ax.plot(x,[r[key] if r[key] is not None else np.nan for r in rows],marker='o',label=label,color=color)
    for i,r in enumerate(rows):
        ax.text(i+1,-.13,f"n={r['n']}/{r['expected']}"+(' *' if not r['comparable'] else ''),transform=ax.get_xaxis_transform(),ha='center',fontsize=7)
    ax.set(xticks=x,xticklabels=[m[:3] for m in d['months']],ylabel='Media de promedios diarios de 24 h (µg/m³)',title=FIGURES[0][1]);ax.legend();ax.grid(axis='y',alpha=.2)
    fig.subplots_adjust(bottom=.25)
    foot(fig,'Solo fechas diarias pareadas. * Menos de 75% de pares: descriptivo, sin destacar cambio. No se conectan huecos.')
    save(fig,0,'PM10 · meses 2023 y 2024 · solo fechas pareadas','Media de bases diarias PM10 antes de redondear','n de pares / días del mes de 2023','Diciembre: 31/31 pares; PM10 +65.20%, sin inferencia causal.','D10–D11; separar cobertura y cambio.')

    fig,ax=plt.subplots(figsize=(12,5.8));labels=[]
    for i,(p,y) in enumerate((p,y) for p in ['PM10','PM2.5','CO'] for y in [2023,2024]):
        r=next(r for r in d['periods'] if r['pollutant']==p and r['year']==y and r['month']==12);left=0
        labels.append(f"{p} · {y} (n={r['valid']}/{r['expected']})")
        for j,n in enumerate(r['counts']+[r['missing']]):
            if n:
                ax.barh(i,n,left=left,color=COLORS[j],edgecolor='white',label=(d['categories'][j]['name'] if j<5 else 'Sin datos') if i==0 else None)
                ax.text(left+n/2,i,str(n),ha='center',va='center',color='white' if j==4 else '#152239',fontsize=9)
            left+=n
    # Leyenda explícita incluso si una categoría no aparece en la primera fila.
    handles=[Rectangle((0,0),1,1,color=c) for c in COLORS]
    ax.legend(handles,[r['name'] for r in d['categories']]+['Sin datos'],loc='upper center',bbox_to_anchor=(.5,-.12),ncol=3,fontsize=9)
    ax.set(yticks=range(6),yticklabels=labels,xlim=(0,31),xlabel='Días calendario de diciembre',title=FIGURES[1][1]);ax.invert_yaxis();fig.subplots_adjust(left=.2,bottom=.27)
    foot(fig,'Denominador: 31 días por año/contaminante. CO permanece en Buena 31/31 en ambos años, aunque aumenta la media de sus máximos móviles.')
    save(fig,1,'PM10/PM2.5/CO · diciembre 2023 y 2024','Conteo de categorías diarias','31 días calendario por fila','Mala o peor: PM10 15→27 y PM2.5 7→19; CO Buena 31→31.','D12–D14; no promediar categorías ni equiparar cambio relativo con riesgo.')

    fig,axes=plt.subplots(1,2,figsize=(15,9));variables=['PM10','PM2.5','O3','CO','NO2','ET','RH','WS']
    for ax,y in zip(axes,[2023,2024]):
        matrix=np.array([[next(r for r in d['coverage'] if r['year']==y and r['month']==m and r['variable']==v)['pct'] for v in variables] for m in range(1,13)])
        image=ax.imshow(matrix,vmin=0,vmax=100,cmap='Blues',aspect='auto')
        for mi in range(12):
            for vi,v in enumerate(variables):
                r=next(r for r in d['coverage'] if r['year']==y and r['month']==mi+1 and r['variable']==v)
                ax.text(vi,mi,f"{r['pct']:.0f}%\n{r['usable']}/{r['expected']}",ha='center',va='center',fontsize=7,color='white' if r['pct']>65 else '#17253d')
        ax.set(xticks=range(8),xticklabels=variables,yticks=range(12),yticklabels=[m[:3] for m in d['months']],title=str(y))
    fig.suptitle(FIGURES[2][1],fontsize=14);fig.subplots_adjust(left=.06,bottom=.13,top=.90,right=.86,wspace=.18)
    fig.colorbar(image,cax=fig.add_axes([.90,.24,.018,.52]),label='Horas utilizables / esperadas (%)')
    foot(fig,'Rejillas completas; sí faltan mediciones. NO2 es complementario; el patrón estacional de RH difiere. La disponibilidad no acredita calibración.')
    save(fig,2,'Ambos años · 12 meses · contaminantes comunes, NO2 y ET/RH/WS','Porcentaje y conteo de horas utilizables','Horas calendario de cada mes (672–744; febrero 2024=696)','O3 2023 comienza en julio; RH cubre temporadas distintas; NO2 aparece en parte de 2024.','D03–D04, D17; mostrar cobertura antes de interpretar.')

    fig,axes=plt.subplots(2,1,figsize=(14,9));cmap=plt.colormaps['Blues'].copy();cmap.set_bad('#d2d7df')
    for ax,y in zip(axes,[2023,2024]):
        rows=[[next(r for r in d['profiles'] if r['pollutant']=='PM10' and r['year']==y and r['month']==m and r['hour']==h) for h in range(24)] for m in range(1,13)]
        matrix=np.array([[r['bad_pct'] if r['bad_pct'] is not None else np.nan for r in row] for row in rows])
        image=ax.imshow(np.ma.masked_invalid(matrix),cmap=cmap,vmin=0,vmax=100,aspect='auto')
        for mi,row in enumerate(rows):
            for h,r in enumerate(row):
                if r['valid']/r['expected']<.75: ax.add_patch(Rectangle((h-.5,mi-.5),1,1,fill=False,edgecolor='#59667b',linestyle='--',linewidth=.7))
        ax.set(xticks=range(24),xticklabels=[str(h).zfill(2) for h in range(24)],yticks=range(12),yticklabels=[m[:3] for m in d['months']],xlabel='Hora local codificada en la fuente',title=f'{y} · PM10 · NowCast 12 h')
    fig.suptitle(FIGURES[3][1],fontsize=14);fig.subplots_adjust(left=.07,right=.86,bottom=.14,hspace=.3)
    fig.colorbar(image,cax=fig.add_axes([.90,.24,.018,.52]),label='Mala o peor / horas evaluables (%)')
    peak=max((r for r in d['profiles'] if r['year']==2024 and r['pollutant']=='PM10' and r['valid']>=.75*r['expected']),key=lambda r:r['bad_pct'] if r['bad_pct'] is not None else -1)
    peak_text=f"Mayor frecuencia 2024 entre celdas con ≥75% cobertura: {d['months'][peak['month']-1]}, {peak['hour']:02d}:00, {peak['bad']}/{peak['valid']} = {peak['bad_pct']:.2f}% Mala o peor (cobertura {peak['valid']}/{peak['expected']})."
    foot(fig,'Denominador por celda: horas con categoría a ese mes/hora; n en profiles.csv. Gris=sin indicador; borde discontinuo=cobertura <75%. '+peak_text)
    save(fig,3,'PM10 · ambos años · 12 meses × 24 horas','Proporción de categorías horarias Mala o peor del NowCast','Horas evaluables por mes/hora; expected=días calendario del mes',peak_text,'D04 y D14; contrastar patrones sin mezclar NowCast y concentración cruda.')

    ep=next(r for r in d['episodes'] if r['pollutant']=='PM10' and r['crossYear'])
    fig,ax=plt.subplots(figsize=(12,5.6));pts=ep['context'];dates=pd.to_datetime([p['t'] for p in pts]);vals=[p['indicator'] if p['indicator'] is not None else np.nan for p in pts]
    ax.plot(dates,vals,color='#2c56cf',marker='o');ax.axvspan(pd.Timestamp(ep['start']),pd.Timestamp(ep['end']),color='#ff7e00',alpha=.15,label=f"Episodio completo: {ep['days']} días")
    ax.set(ylabel='Promedio diario de 24 h PM10 (µg/m³)',title=FIGURES[4][1]);ax.legend();ax.grid(axis='y',alpha=.2);fig.autofmt_xdate();fig.subplots_adjust(bottom=.24)
    foot(fig,f"Episodio {ep['start']} → {ep['end']}; {ep['days']} días reales, {ep['n_raw_hours']}/{ep['expected_hours']} lecturas. El cruce no duplica duración; no identifica una causa.")
    save(fig,4,'PM10 · 29/12/2023–05/01/2024 · episodio 31/12–03/01','Base diaria antes de redondear, con dos días de contexto a cada lado','24 h/día; episodio 96/96 lecturas y 4 días','El episodio de cuatro días cruza el año y se conserva como un único intervalo.','D18; fechas reales y continuidad, sin atribuciones causales.')

    r=next(r for r in d['meteorology'] if r['year']==2024 and r['month']==12 and r['pollutant']=='PM10' and r['variable']=='ET')
    fig,ax=plt.subplots(figsize=(10,6));ax.scatter([p[1] for p in r['points']],[p[2] for p in r['points']],s=36,color='#2c56cf',alpha=.8)
    ax.set(xlabel='Temperatura externa media diaria ET (°C)',ylabel='Promedio diario de 24 h PM10 (µg/m³)',title=FIGURES[5][1]);ax.grid(alpha=.15);ax.text(.02,.98,f"Spearman ρ={r['rho']:.3f}\nn={r['n']}/{r['expected']} pares · {r['coverage_pct']:.1f}% cobertura",transform=ax.transAxes,va='top',bbox={'facecolor':'white','alpha':.9,'edgecolor':'#dbe1e9'});fig.subplots_adjust(bottom=.18)
    foot(fig,'Exactamente los pares exportados del mes. Medias meteorológicas con ≥18 lecturas y rho con ≥15 pares. Sin p-valores; asociación descriptiva, no causalidad.')
    save(fig,5,'PM10 y ET · diciembre 2024','Pares diarios y rho de Spearman descriptivo',f"{r['n']}/{r['expected']} pares diarios",f"Se describe asociación ρ={r['rho']:.3f}; la cobertura no permite inferir causalidad.",'D15; ET externa, sin usar IT para afirmar inversión.')

    lines=['# Catálogo de figuras · revisión 02','', 'Seis preguntas complementarias, sin agregar contaminantes con unidades distintas. SVG vectorial y PNG a 220 dpi, fondo blanco. No se elaboró aún el PDF final.','']
    for i,row in enumerate(catalog,1):
        lines += [f"## Figura {i}: {row['archivo']}",'']+[f"- **{k}:** {v}" for k,v in row.items() if k!='archivo']+['']
    (OUT/'catalogo_figuras.md').write_text('\n'.join(lines),encoding='utf-8')
    findings=[]
    for p in ['PM10','PM2.5','CO']:
        r=next(r for r in d['comparisons'] if r['pollutant']==p and r['month']==12)
        a=next(r for r in d['periods'] if r['year']==2023 and r['month']==12 and r['pollutant']==p)
        b=next(r for r in d['periods'] if r['year']==2024 and r['month']==12 and r['pollutant']==p)
        findings.append({'hallazgo':f'{p} diciembre: cambio de magnitud y categorías','csv':'comparacion_pareada.csv;monthly.csv',
            'filtro':f'pollutant={p};month=12;year=2023/2024','columnas':'a;b;change_pct;n;expected;counts;bad;valid',
            'n':r['n'],'esperados':r['expected'],'a':r['a'],'b':r['b'],'calculo':'100*(b-a)/a','resultado_pct':r['change_pct'],
            'mala_o_peor_2023':f"{a['bad']}/{a['valid']}",'mala_o_peor_2024':f"{b['bad']}/{b['valid']}",
            'alcance':'Solo fechas pareadas; CO permanece Buena 31/31 en ambos años' if p=='CO' else 'Comparación mensual suficiente; sin atribución causal'})
    for p in A.N.CORE+['GLOBAL']:
        r=next(r for r in d['comparisons'] if r['pollutant']==p and r['month']==0)
        findings.append({'hallazgo':f'{p}: insuficiencia de comparación anual','csv':'comparacion_pareada.csv','filtro':f'pollutant={p};month=0',
            'columnas':'n;expected;coverage;quarterly_coverage;comparable','n':r['n'],'esperados':r['expected'],
            'calculo':'n/365 y cada trimestre ≥75%','resultado_pct':r['coverage'],'alcance':'No destacar mejora/deterioro representativo anual'})
    findings.append({'hallazgo':'PM10: episodio cruza de año','csv':'episodios.csv','filtro':'pollutant=PM10;start=2023-12-31;end=2024-01-03','columnas':'start;end;days;n_raw_hours;expected_hours','n':4,'esperados':4,'calculo':'end-start+1','alcance':'Un intervalo, cuatro días; sin causa demostrada'})
    findings.append({'hallazgo':'PM10: mayor frecuencia horaria desfavorable de 2024 entre celdas suficientes','csv':'profiles.csv','filtro':f"year=2024;month={peak['month']};hour={peak['hour']};pollutant=PM10;valid/expected>=0.75",'columnas':'bad;valid;expected;bad_pct','n':peak['valid'],'esperados':peak['expected'],'calculo':f"100*{peak['bad']}/{peak['valid']}",'resultado_pct':peak['bad_pct'],'alcance':'Frecuencia de categorías de NowCast 12h, no concentración cruda ni fuente emisora'})
    meteo=next(v for v in d['meteorology'] if v['year']==2024 and v['month']==12 and v['pollutant']=='PM10' and v['variable']=='ET')
    findings.append({'hallazgo':'Asociación PM10/ET en diciembre 2024','csv':'meteorologia.csv;pares_meteorologicos.csv','filtro':'year=2024;month=12;pollutant=PM10;variable=ET','columnas':'rho;n;expected;date;meteorology;concentration','n':meteo['n'],'esperados':meteo['expected'],'calculo':'Correlación de rangos de los pares exportados','resultado_pct':None,'alcance':f"rho={meteo['rho']:.6f}; sin p-valores ni causalidad"})
    A.csv_table(OUT/'hallazgos.csv',findings)
    (OUT/'hallazgos.md').write_text('# Hallazgos trazables\n\nEl archivo hallazgos.csv identifica filtros, columnas, fechas, n, denominadores y cálculo para cada hallazgo. No equivale a una conclusión anual ni atribuye una fuente de emisión.\n',encoding='utf-8')
    dest=ROOT/'web/public/descargas/sprint-2/figuras';dest.mkdir(parents=True,exist_ok=True)
    for path in OUT.iterdir(): shutil.copy2(path,dest/path.name)
    return catalog

if __name__=='__main__':
    print(json.dumps({'figuras':len(figures())}))
