async(page)=>{
 const base='http://127.0.0.1:3033',names=[],errors=[],animations={},zoom={},ok=(n,v,d)=>{if(!v)throw new Error(n+': '+JSON.stringify(d));names.push(n)};
 const combo=name=>page.getByRole('combobox',{name,exact:true}),format=n=>n.toLocaleString('es-MX',{minimumFractionDigits:2,maximumFractionDigits:2});
 const snap=()=>page.locator('main').ariaSnapshot();
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)errors.push(r.status()+' '+r.url())});
 await page.setViewportSize({width:1440,height:1050});await page.emulateMedia({reducedMotion:'no-preference'});await page.goto(base+'/#prediccion');await page.reload();await snap();await page.locator('.am-forecast-card').nth(2).waitFor();
 const source=await(await page.request.get(base+'/datos/sprint-3/predicciones/2024-12.json')).json();const chosen=source.find(r=>r.origin.endsWith('23:00:00'));
 await page.getByLabel(/Origen t ·/).fill(chosen.origin.slice(0,16));await page.waitForTimeout(450);
 const cards=await page.locator('.am-forecast-card').evaluateAll(es=>es.map(e=>({h:+e.dataset.horizon,target:e.dataset.target,time:e.querySelector('time').dateTime,fields:[...e.querySelectorAll('dd')].map(d=>d.textContent.replace(' µg/m³','').trim()),units:[...e.querySelectorAll('dd small')].map(d=>d.textContent)})));
 ok('Tres horizontes en resumen previo al detalle',cards.length===3&&await page.locator('.am-prediction-detail').evaluate(e=>!e.open));
 ok('Fechas objetivo exactas al cruzar medianoche',cards.every((c,i)=>c.h===i+1&&c.target===chosen.target[i]&&c.time===chosen.target[i]),cards);
 ok('Observado predicho y diferencia corresponden a C05',cards.every((c,i)=>c.fields[0]===format(chosen.observed[i])&&c.fields[1]===format(chosen.models.HGB.predicted[i])&&c.fields[2].replace(/^\+/,'')===format(chosen.models.HGB.error[i])),cards);
 ok('Cada magnitud conserva unidades',cards.every(c=>c.units.every(u=>u==='µg/m³')));
 ok('Botones compactos con nombres accesibles completos',(await page.getByRole('button',{name:'Origen disponible anterior',exact:true}).innerText()).includes('Anterior')&&(await page.getByRole('button',{name:'Siguiente origen disponible',exact:true}).innerText()).includes('Siguiente'));
 const checkAxis=async()=>page.locator('#prediccion-contexto svg').evaluate(svg=>{const v=svg.viewBox.baseVal;return[...svg.querySelectorAll('[data-axis-tick]')].every(e=>{const b=e.getBBox();return b.x>=0&&b.x+b.width<=v.width+.1&&b.y+b.height<=v.height+.1})});
 const graph=page.locator('#prediccion-contexto svg');await graph.waitFor();await page.waitForTimeout(600);
 const max=await graph.getAttribute('data-domain-max');
 for(const h of [48,12,6]){
  await combo('Horas de contexto observado').selectOption(String(h));await page.waitForTimeout(600);
  zoom[h]={samples:await graph.getAttribute('data-samples'),maximum:await graph.getAttribute('data-domain-max')};
  ok('Acercamiento '+h+' h conserva contexto y tres objetivos',+zoom[h].samples===h+3&&zoom[h].maximum===max,zoom[h]);
  ok('Etiquetas del eje completas con '+h+' h',await checkAxis());
  const predictions=await graph.locator('[data-series="Predicción del modelo"] circle').evaluateAll(es=>es.map(e=>({t:e.dataset.time,v:+e.dataset.value})));
  ok('Predicciones sin interpolar al acercar '+h+' h',predictions.length===3&&predictions.every((p,i)=>p.t===chosen.target[i]&&p.v===chosen.models.HGB.predicted[i]));
 }
 ok('Observación y predicción con estilos distinguibles',await graph.locator('[data-series="Predicción del modelo"] line').evaluateAll(es=>es.every(e=>e.getAttribute('stroke-dasharray')==='7 5'))&&await graph.locator('[data-series="Observado hasta el origen"] line').evaluateAll(es=>es.every(e=>!e.hasAttribute('stroke-dasharray'))));
 await page.getByText('Tabla ampliada y referencias',{exact:true}).click();const table=page.getByRole('region',{name:'Pronósticos de PM10 y observados',exact:true});
 ok('Tabla ampliada consultable',await table.isVisible()&&await table.locator('tbody tr').count()===3);
 const tableText=await table.innerText();ok('Etiquetas públicas comprensibles',tableText.includes('Predicción del modelo')&&tableText.includes('Última lectura conocida')&&tableText.includes('Misma hora del día anterior')&&!tableText.includes('HGB'));
 ok('Referencias conservan valores congelados',chosen.models.persistencia.predicted.every(p=>tableText.includes(format(p)))&&chosen.models.diaria.predicted.every(p=>tableText.includes(format(p))));
 await page.getByText('Tabla ampliada y referencias',{exact:true}).click();
 // Buscar un origen evaluado que tenga huecos antes de sus 24 horas completas.
 const july=await(await page.request.get(base+'/datos/sprint-3/predicciones/2024-07.json')).json();
 const hourly=new Map();for(const m of ['2024-06','2024-07']){const c=await(await page.request.get(base+'/datos/sprint-3/horas/'+m+'.json')).json();c.time.forEach((t,i)=>hourly.set(t,c.values.PM10[i]))}
 const shift=(t,h)=>new Date(Date.parse(t+'Z')+h*3600000).toISOString().slice(0,19);
 const gapOrigin=july.find(r=>Array.from({length:24},(_,i)=>hourly.get(shift(r.origin,i-47))).some(v=>v===null));ok('Existe caso real con hueco en contexto ampliado',!!gapOrigin);
 await combo('Mes de origen · 2024').selectOption('7');await page.locator('.am-forecast-card').nth(2).waitFor();await page.getByLabel(/Origen t ·/).fill(gapOrigin.origin.slice(0,16));await combo('Horas de contexto observado').selectOption('48');await page.waitForTimeout(650);
 const expected=Array.from({length:48},(_,i)=>hourly.get(shift(gapOrigin.origin,i-47))??null);
 const segments=expected.slice(1).filter((v,i)=>v!==null&&expected[i]!==null).length;
 ok('Los huecos reales interrumpen líneas',await graph.locator('[data-series="Observado hasta el origen"] line').count()===segments);
 ok('Puntos del contexto coinciden con horas observadas',await graph.locator('[data-series="Observado hasta el origen"] circle').count()===expected.filter(v=>v!==null).length);
 await page.getByLabel(/Origen t ·/).fill('2024-07-31T23:00');
 // Usar un origen fuera de la evaluación siempre conocido al final de diciembre.
 await combo('Mes de origen · 2024').selectOption('12');await page.locator('.am-forecast-card').nth(2).waitFor();await page.getByLabel(/Origen t ·/).fill('2024-12-31T23:00');await page.getByText(/Este origen no pertenece/).waitFor();ok('No se inventa resumen para origen no evaluado',await page.locator('.am-forecast-card').count()===0);
 await page.getByLabel(/Origen t ·/).fill(chosen.origin.slice(0,16));await combo('Horas de contexto observado').selectOption('6');await page.locator('.am-forecast-card').nth(2).waitFor();
 animations.cards=await page.evaluate(async()=>{document.querySelector('input[type="datetime-local"]').focus();const button=[...document.querySelectorAll('button')].find(e=>e.getAttribute('aria-label')==='Siguiente origen disponible');button.click();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));await new Promise(r=>setTimeout(r,55));const e=document.querySelector('.am-forecast-summary').parentElement;const mid=+getComputedStyle(e).opacity;await new Promise(r=>setTimeout(r,450));return{mid,final:+getComputedStyle(e).opacity}});
 ok('Entrada de horizontes visible y final legible',animations.cards.mid>0&&animations.cards.mid<1&&animations.cards.final===1,animations.cards);
 await page.getByRole('button',{name:'Métricas y errores',exact:true}).click();await snap();const metrics=page.getByRole('region',{name:'Métricas congeladas del modelo y referencias',exact:true}).first();await metrics.waitFor();
 ok('Métricas sin cambios y nombres claros',(await metrics.innerText()).includes('Última lectura conocida')&&(await metrics.innerText()).includes('16.21')&&await metrics.locator('tbody tr').count()===9);
 await page.getByText('Concentraciones altas: observado ≥114 µg/m³',{exact:true}).click();ok('Se conservan R² negativos y limitación de altas',(await page.locator('#evaluacion-error').innerText()).includes('-0.730')&&(await page.locator('.am-model-scope').innerText()).includes('subestimar'));
 await page.getByRole('button',{name:'Explorar un origen',exact:true}).click();await page.locator('.am-forecast-card').nth(2).waitFor();await page.getByLabel(/Origen t ·/).fill(chosen.origin.slice(0,16));await combo('Horas de contexto observado').selectOption('6');await page.waitForTimeout(700);await page.setViewportSize({width:1440,height:2050});await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));await page.waitForTimeout(650);await page.screenshot({path:'output/playwright/editorial/prediccion_ajustes_escritorio.png'});
 await page.emulateMedia({reducedMotion:'reduce'});await combo('Horas de contexto observado').selectOption('12');await page.waitForTimeout(100);ok('Movimiento reducido deja gráfico en estado final',await graph.locator('.s2-line-reveal').evaluate(e=>e.getAnimations().length===0&&getComputedStyle(e).clipPath==='none'));
 ok('Sin errores de navegador en Predicción',errors.length===0,errors);
 return{status:'APROBADO',checks:names.length,names,zoom,animations,errors};
}
