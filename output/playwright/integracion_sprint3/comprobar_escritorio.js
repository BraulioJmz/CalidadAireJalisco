async (page) => {
  const base = 'http://127.0.0.1:3033';
  const checks = [], animations = {}, snapshots = [], requests = [], errors = [];
  const ok = (name, condition, detail) => { if (!condition) throw new Error(name + ': ' + JSON.stringify(detail)); checks.push(name); };
  const snapshot = async name => snapshots.push({name, excerpt:(await page.locator('#am-content').ariaSnapshot()).slice(0,180)});
  const tab = async i => { await page.locator(`#am-tab-${i}`).click(); await snapshot('tab-'+i); };
  const focusPanel = async () => page.evaluate(() => window.scrollTo(0,document.querySelector('#am-content').getBoundingClientRect().top + scrollY - 180));
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', req => { if (req.url().includes('/datos/sprint-3/')) requests.push(req.url()); });
  page.on('response', res => { if (res.url().startsWith(base) && res.status()>=400) errors.push(res.status()+' '+res.url()); });
  await page.setViewportSize({width:1440,height:1000});
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.goto(base);
  await page.locator('.am-finding').nth(5).waitFor(); await page.waitForTimeout(550);
  ok('Seis hallazgos trazables', await page.locator('.am-finding').count()===6);
  ok('Portada sin detalle horario ni predicciones', !requests.some(u=>/\/(horas|predicciones)\//.test(u)), requests);
  await snapshot('resumen');
  await page.screenshot({path:'output/playwright/integracion_sprint3/resumen_escritorio.png'});

  animations.tabs = await page.evaluate(async () => {
    const marker=document.querySelector('.am-tab-marker'); const initial=getComputedStyle(marker).transform;
    document.querySelector('#am-tab-1').click();
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    await new Promise(r=>setTimeout(r,65));
    const mid={opacity:+getComputedStyle(document.querySelector('#am-content')).opacity,marker:getComputedStyle(marker).transform};
    await new Promise(r=>setTimeout(r,600));
    return {initial,mid,final:{opacity:+getComputedStyle(document.querySelector('#am-content')).opacity,marker:getComputedStyle(marker).transform}};
  });
  ok('Entrada visible de panel',animations.tabs.mid.opacity>0&&animations.tabs.mid.opacity<1,animations.tabs);
  ok('Indicador deslizante con posición intermedia',animations.tabs.mid.marker!==animations.tabs.initial&&animations.tabs.mid.marker!==animations.tabs.final.marker,animations.tabs);
  ok('Panel termina legible',animations.tabs.final.opacity===1);
  await snapshot('historico');
  await page.getByRole('combobox',{name:'Agregación',exact:true}).selectOption('year');
  await page.getByRole('combobox',{name:'Año del histórico',exact:true}).selectOption('2020');
  await page.getByText('Ver medias, denominadores y suficiencia',{exact:true}).click();
  const historyPanel=page.locator('#historico-evolucion');
  ok('2020 no se presenta suficiente por total anual', (await historyPanel.innerText()).includes('Solo descriptivo'));
  await page.getByRole('combobox',{name:'Año del histórico',exact:true}).selectOption('0');
  await page.waitForTimeout(650);
  ok('Huecos por insuficiencia no se conectan',await historyPanel.locator('.s2-line-reveal line').count()===4,await historyPanel.locator('.s2-line-reveal line').count());
  animations.lines=await page.evaluate(async()=>{
    const control=[...document.querySelectorAll('label')].find(e=>e.textContent.includes('Mostrar también medias')).querySelector('input');
    control.click(); await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    const group=document.querySelector('#historico-evolucion .s2-line-reveal');
    const coords=()=>[...group.querySelectorAll('line')].map(e=>[e.getAttribute('x1'),e.getAttribute('y1'),e.getAttribute('x2'),e.getAttribute('y2')]);
    await new Promise(r=>setTimeout(r,75)); const mid={clip:getComputedStyle(group).clipPath,coords:coords()};
    await new Promise(r=>setTimeout(r,600));return{midClip:mid.clip,finalClip:getComputedStyle(group).clipPath,geometryFixed:JSON.stringify(mid.coords)===JSON.stringify(coords())};
  });
  ok('Revelado visible de líneas',animations.lines.midClip!=='none'&&animations.lines.midClip!==animations.lines.finalClip,animations.lines);
  ok('Coordenadas finales constantes durante entrada',animations.lines.geometryFixed);
  await page.getByRole('combobox',{name:'Año meteorología',exact:true}).selectOption('2018');
  await page.getByRole('combobox',{name:'Variable meteorológica',exact:true}).selectOption('RH');
  await page.getByText('Sin pares observados para esta consulta.',{exact:true}).waitFor();
  ok('Meteorología ausente no se convierte en correlación cero',(await page.locator('.am-metric-line').innerText()).includes('No calculable'));

  await tab(2);
  await page.locator('.am-kpis').waitFor();
  ok('Diciembre pareado 31/31',(await page.locator('.am-kpis').innerText()).includes('31 / 31'));
  ok('Cambio pareado diciembre 65.2%',(await page.locator('#comparacion-periodos').innerText()).includes('65.2 %'));
  animations.cards=await page.evaluate(async()=>{
    const select=[...document.querySelectorAll('label')].find(e=>e.textContent.includes('Periodo comparado')).querySelector('select');select.value='2';select.dispatchEvent(new Event('change',{bubbles:true}));
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));await new Promise(r=>setTimeout(r,55));
    const mid=+getComputedStyle(document.querySelector('.am-kpis')).opacity; await new Promise(r=>setTimeout(r,450));return{mid,final:+getComputedStyle(document.querySelector('.am-kpis')).opacity};
  });
  ok('Tarjetas muestran transición intermedia',animations.cards.mid>0&&animations.cards.mid<1&&animations.cards.final===1,animations.cards);
  ok('Febrero 2023/2024 usa 28 fechas posibles',(await page.locator('.am-kpis').innerText()).includes('/ 28'));

  await tab(3); await page.locator('.am-day').nth(30).waitFor();
  await page.getByRole('combobox',{name:'Contaminante',exact:true}).selectOption('CO');
  await page.waitForTimeout(450);
  const green=await page.locator('.am-day').evaluateAll(es=>es.every(e=>getComputedStyle(e).backgroundColor==='rgb(0, 228, 0)'&&e.getAttribute('aria-label').includes('Buena')));
  ok('CO Buena 31/31: código 0 válido',green);
  animations.calendar=await page.evaluate(async()=>{
    const button=document.querySelectorAll('.am-day')[7];const before=getComputedStyle(button).backgroundColor;button.click();
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));await new Promise(r=>setTimeout(r,50));
    const mid=+getComputedStyle(document.querySelector('.am-day-detail')).opacity;await new Promise(r=>setTimeout(r,450));return{before,after:getComputedStyle(button).backgroundColor,mid,final:+getComputedStyle(document.querySelector('.am-day-detail')).opacity};
  });
  ok('Detalle diario con entrada visible y color preservado',animations.calendar.mid>0&&animations.calendar.mid<1&&animations.calendar.final===1&&animations.calendar.before===animations.calendar.after,animations.calendar);
  await page.getByRole('combobox',{name:'Año del calendario',exact:true}).selectOption('2023');
  await page.getByRole('combobox',{name:'Mes del calendario',exact:true}).selectOption('1');
  await page.getByRole('combobox',{name:'Contaminante',exact:true}).selectOption('O3');
  await page.locator('.am-day[aria-label^="2023-01-31"]').waitFor();await page.waitForTimeout(100);
  ok('O3 enero 2023 ausente, sin verde',(await page.locator('.am-day.am-missing').count())===31);
  await page.getByRole('combobox',{name:'Año del calendario',exact:true}).selectOption('2024');
  await page.getByRole('combobox',{name:'Mes del calendario',exact:true}).selectOption('2');
  await page.getByRole('button',{name:/^2024-02-29:/}).click();
  ok('29 febrero 2024 conservado',(await page.locator('.am-day-detail h3').innerText())==='2024-02-29');
  await page.getByRole('combobox',{name:'Año del calendario',exact:true}).selectOption('2023');
  await page.getByRole('button',{name:/^2023-02-28:/}).waitFor();
  ok('Sin fecha inexistente en febrero 2023',await page.locator('.am-day').count()===28&&!(await page.locator('#am-content').innerText()).includes('2023-02-29'));
  await tab(0); await page.locator('.am-finding').filter({hasText:'H06'}).getByRole('button').click(); await snapshot('episodio52');
  await page.locator('#episodios-secuencia').getByText('2022-01-24',{exact:true}).waitFor();
  ok('Episodio cruzado conserva fin real',(await page.getByRole('combobox',{name:'Año del calendario',exact:true}).inputValue())==='2021'&&(await page.locator('#episodios-secuencia').innerText()).includes('52'));

  await tab(4); await page.getByLabel(/Origen t ·/).waitFor();
  await page.locator('table[aria-label]').count().catch(()=>0);
  await page.getByRole('region',{name:'Pronósticos de PM10 y observados',exact:true}).waitFor();
  const source=await (await page.request.get(base+'/datos/sprint-3/predicciones/2024-12.json')).json();
  const chosen=source.at(-1);await page.getByLabel(/Origen t ·/).fill(chosen.origin.slice(0,16));
  await page.waitForTimeout(100);
  const display=await page.getByRole('region',{name:'Pronósticos de PM10 y observados',exact:true}).innerText();
  ok('Tres fechas objetivo reales visibles',chosen.target.every(t=>display.includes(t.replace('T',' · '))),display);
  const format=n=>n.toLocaleString('es-MX',{minimumFractionDigits:2,maximumFractionDigits:2});
  ok('Predicciones visibles concuerdan con congeladas',chosen.models.HGB.predicted.every(p=>display.includes(format(p))));
  await page.getByLabel(/Origen t ·/).fill('2024-12-31T23:00');
  await page.getByText(/Este origen no pertenece/).waitFor();
  ok('No se inventan pronósticos para origen no evaluado',await page.getByRole('region',{name:'Pronósticos de PM10 y observados',exact:true}).count()===0);
  await page.getByRole('combobox',{name:'Mes de origen · 2024',exact:true}).selectOption('1');
  await page.getByRole('region',{name:'Pronósticos de PM10 y observados',exact:true}).waitFor();await page.waitForTimeout(200);
  ok('Contexto anterior cruza año sin salto',requests.some(u=>u.endsWith('/horas/2023-12.json')));
  await focusPanel(); await page.screenshot({path:'output/playwright/integracion_sprint3/prediccion_escritorio.png'});

  await tab(5); await page.getByRole('region',{name:'Métricas congeladas del modelo y referencias',exact:true}).first().waitFor();
  ok('N global idéntico entre modelos y horizontes',(await page.getByRole('region',{name:'Métricas congeladas del modelo y referencias',exact:true}).first().locator('tbody tr').count())===9&&(await page.getByRole('region',{name:'Métricas congeladas del modelo y referencias',exact:true}).first().locator('tbody tr').allTextContents()).every(t=>t.includes('6,225')));
  await page.getByText('Concentraciones altas: observado ≥114 µg/m³',{exact:true}).click();
  ok('R² negativos de altas conservados',(await page.locator('#evaluacion-error').innerText()).includes('-0.466')&&(await page.locator('#evaluacion-error').innerText()).includes('-0.730'));
  await page.getByRole('combobox',{name:'Mes de fecha objetivo · 2024',exact:true}).selectOption('7');
  await page.locator('.am-point-reveal').first().locator('circle').nth(267).waitFor();
  ok('Filtro por fecha objetivo usa 268 puntos julio',await page.locator('.am-point-reveal').first().locator('circle').count()===268);
  const metricResponse=await(await page.request.get(base+'/datos/sprint-3/metricas.json')).json();
  const metricText=await page.locator('#evaluacion-error').innerText();
  const july=metricResponse.mensuales.filter(r=>r.partition==='test'&&r.month===7);
  ok('Métricas mensuales exactas con referencias',july.every(r=>metricText.includes(format(r.mae))));
  await page.getByRole('combobox',{name:'Horizonte de las gráficas',exact:true}).selectOption('3');
  await page.waitForTimeout(650);ok('Horizonte +3 aplicado a gráficas',(await page.locator('.am-point-reveal').first().locator('circle').count())===268);

  await page.evaluate(async()=>{ for(const i of [1,2,3,4,5,1]) {document.querySelector('#am-tab-'+i).click();await new Promise(r=>requestAnimationFrame(r));} });
  await page.waitForTimeout(700);
  ok('Cambios rápidos conservan un panel y selección',await page.getByRole('tabpanel').count()===1&&await page.getByRole('tab',{selected:true}).count()===1);
  ok('Sin animaciones encoladas al terminar',await page.locator('#am-content').evaluate(e=>e.getAnimations().length)===0);

  await page.emulateMedia({reducedMotion:'reduce'}); await tab(3);await page.locator('.am-day').first().waitFor();await page.waitForTimeout(100);
  const reduced=await page.evaluate(()=>({panel:document.querySelector('#am-content').getAnimations().length,marker:getComputedStyle(document.querySelector('.am-tab-marker')).transitionDuration,opacity:+getComputedStyle(document.querySelector('#am-content')).opacity}));
  ok('Movimiento reducido: estados finales sin transiciones',reduced.panel===0&&reduced.opacity===1&&reduced.marker==='0s',reduced);
  await page.locator('.am-day').nth(4).click();ok('Control manual utilizable con movimiento reducido',(await page.locator('.am-day[aria-pressed=true] b').innerText())==='5');
  await page.locator('#am-tab-3').focus();await page.keyboard.press('End');ok('Teclado Fin selecciona método',await page.locator('#am-tab-6').getAttribute('aria-selected')==='true');
  await page.keyboard.press('Home');ok('Teclado Inicio selecciona resumen',await page.locator('#am-tab-0').getAttribute('aria-selected')==='true');
  await page.keyboard.press('ArrowRight');ok('Teclado flecha y foco visible',await page.evaluate(()=>document.activeElement.id==='am-tab-1'&&getComputedStyle(document.activeElement).outlineStyle!=='none'));
  await tab(6);await page.getByRole('link',{name:/^modelo_metricas_globales.csv/}).waitFor();
  const downloadPromise=page.waitForEvent('download');await page.getByRole('link',{name:/^modelo_metricas_globales.csv/}).click();const download=await downloadPromise;
  ok('Descarga real de métricas',download.suggestedFilename()==='modelo_metricas_globales.csv'&&(await download.failure())===null);
  for(const path of ['/sprint-1','/sprint-2','/sprint-3','/observatorio-mensual','/metodologia']) {const response=await page.goto(base+path);ok('Ruta conservada '+path,response.status()===200);}
  await page.goto(base);await page.waitForTimeout(300);
  ok('Sin errores de navegador o recursos',errors.length===0,errors);
  ok('Consultas de datos del mismo origen',requests.every(u=>u.startsWith(base+'/datos/sprint-3/')));
  ok('Sin detalle horario de toda la década',requests.filter(u=>u.includes('/horas/')).every(u=>/\/horas\/20(1[5-9]|2[0-4])-\d{2}\.json$/.test(u)) && new Set(requests.filter(u=>u.includes('/horas/'))).size<120,requests.filter(u=>u.includes('/horas/')));
  return {status:'APROBADO',checks:checks.length,names:checks,animations,snapshots,errors,uniqueDataRequests:[...new Set(requests)]};
}
