async(page)=>{
const reference={};
await page.setViewportSize({width:1440,height:1000});await page.emulateMedia({reducedMotion:'reduce'});
for(const path of ['/sprint-1','/sprint-2']){
 await page.goto('http://127.0.0.1:3033'+path);await page.locator('h1').waitFor();await page.locator('main').ariaSnapshot();await page.waitForTimeout(650);
 // El cuerpo y CSS son idénticos a HEAD. Normalizar SOLO la navegación compartida
 // según sus cuatro entradas en HEAD, para fijar la referencia anterior a integración.
 await page.locator('nav[aria-label="Principal"]').evaluate(nav=>{nav.querySelector('a[href="/sprint-3"]')?.remove();const a=nav.querySelector('a[href="/"]');a.querySelector('.sm\\:hidden').textContent='Inicio';a.querySelector('.sm\\:inline').textContent='Observatorio';});
 await page.screenshot({path:'output/playwright/editorial/archivo_antes_'+path.slice(1)+'.png',animations:'disabled'});
 reference[path]=await page.evaluate(()=>{
  const props=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return{text:e.textContent.trim().slice(0,200),font:s.fontFamily,fontSize:s.fontSize,lineHeight:s.lineHeight,color:s.color,background:s.backgroundColor,x:r.x,y:r.y,width:r.width,height:r.height}};
  return{h1:props(document.querySelector('h1')),nav:[...document.querySelectorAll('nav[aria-label="Principal"] a')].map(props),cards:[...document.querySelectorAll('main .card')].slice(0,6).map(props),paragraphs:[...document.querySelectorAll('main p')].slice(0,6).map(props)};
 });
}
return reference;
}
