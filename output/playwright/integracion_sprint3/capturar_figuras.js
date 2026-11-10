async(page)=>{
 const shots=[],base='http://127.0.0.1:3033';await page.emulateMedia({reducedMotion:'no-preference'});await page.setViewportSize({width:1440,height:1000});
 await page.goto(base+'/#prediccion');await page.locator('#am-content').ariaSnapshot();const plot=page.getByRole('img',{name:/^PM10 observado y predicho desde/});await plot.waitFor();await plot.scrollIntoViewIfNeeded();await page.waitForTimeout(700);await page.screenshot({path:'output/playwright/integracion_sprint3/prediccion_contexto_escritorio.png'});shots.push('prediccion_contexto_escritorio');
 await page.locator('#am-tab-5').click();await page.locator('#am-content').ariaSnapshot();await page.locator('.am-point-reveal').first().waitFor();await page.locator('.am-grid-2').scrollIntoViewIfNeeded();await page.waitForTimeout(700);await page.screenshot({path:'output/playwright/integracion_sprint3/evaluacion_escritorio.png'});shots.push('evaluacion_escritorio');
 await page.locator('#am-tab-3').click();await page.locator('#am-content').ariaSnapshot();await page.getByRole('button',{name:/^2024-12-25:/}).click();await page.locator('.am-calendar-layout').scrollIntoViewIfNeeded();await page.waitForTimeout(650);await page.screenshot({path:'output/playwright/integracion_sprint3/calendario_escritorio.png'});shots.push('calendario_escritorio');
 return{screenshots:shots};
}
