# Hallazgos trazables y recursos de integración

Documento técnico de revisión; no es el informe final ni la presentación del Sprint 3.

| ID | Hallazgo | Figura / vista | Periodo | Población | Limitación |
|---|---|---|---|---|---|
| H01 | PM₁₀ tiene 2,100 / 8,784 horas utilizables en 2016 (23.9 %). | [historico-cobertura](figuras/01_cobertura.png) | 2016 | Horas esperadas y PM10 del inventario | No permite sostener un cambio anual representativo. |
| H02 | No hay mediciones numéricas de PM₂.₅ en 2015–2017. La cobertura mejora en 2022–2024. | [historico-cobertura](figuras/01_cobertura.png) | 2015–2024 | Horas crudas PM2.5 | Ausencia de mediciones no significa aire favorable; no se rellena. |
| H03 | La media observada más alta aparece a las 08:00: 94.4 µg/m³, con 2,892 / 3,653 observaciones. | [historico-horas](figuras/02_perfiles_pm10.png) | 2015–2024 | PM10 crudo observado, agrupado por hora | Mezcla años y estaciones con cobertura desigual; no identifica fuentes emisoras. |
| H04 | 15 / 31 frente a 27 / 31 días Mala o peor. La media diaria pareada cambia +65.2 % (31 / 31 pares). | [comparacion-periodos](figuras/03_diciembre.png) | Diciembre 2023 y 2024 | Fechas mes/día coincidentes con base diaria suficiente | Referencia retrospectiva de 2024; el pareamiento no controla meteorología ni actividades. |
| H05 | En 2024, MAE de 16.21, 20.73 y 22.80 µg/m³ a +1, +2 y +3 h; subestimación en concentraciones altas. | [evaluacion-error](../modelado/figuras/05_error_firmado.png) | 2024 | 6,225 orígenes comunes; 70.9 % de las horas del año | Evaluación retrospectiva; no acredita operación en tiempo real ni validez instrumental. |
| H06 | 52 días consecutivos de PM₁₀ Mala o peor: 2021-12-04 a 2022-01-24. | [episodios-secuencia](figuras/04_episodio.png) | 2021-12-04 — 2022-01-24 | Categorías de promedio diario PM10 con al menos 18 lecturas | Criterio de episodio del proyecto y bandas retrospectivas; no demuestra una fuente o causa del evento. |

## Reproducir y verificar

Los originales, el inventario y todo el experimento C05 se conservan. La portada recibe solo el resumen (aproximadamente 22 KB), y los detalles se cargan por año/mes, contaminante o consulta. No hay API de entrenamiento ni peticiones entre dominios para datos. CORS no se modifica.

```powershell
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/historico_sprint3.py
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/exportar_integracion_sprint3.py
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/figuras_integracion_sprint3.py
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/verificar_integracion_sprint3.py
.\.venv\Scripts\python.exe -X utf8 -W error -m pytest tests -q
Set-Location web
node scripts/validar-integracion.mjs
npm run lint
npm run build
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3033
```

El histórico rechaza sobrescribir un análisis terminado; si ya existe su manifiesto, usar los verificadores y exportador sobre la evidencia existente. Los resultados completos están en `data/processed/sprint-3/historico/`; C05 sigue en su carpeta `modelado/` sin cambios. La navegación conserva `/sprint-1`, `/sprint-2` y la antigua portada en `/observatorio-mensual`.

Suficiencia: ver `CRITERIOS_HISTORICOS.md`, registrado antes del análisis. Los pisos del diagnóstico robusto conservan PM10=10, PM2.5=5 y CO=0.1 del Sprint 2, y usan 0.005 para O3, NO2 y los gases adicionales SO2/NO/NOX; esos límites no son normativos y las señales nunca se eliminan.

La continuidad histórica utiliza el contexto disponible desde 2015 y puede diferir del arranque de 2023 del Sprint 2 (que no disponía de 2022). Las páginas y resultados originales de los sprints 1 y 2 siguen disponibles. La comparación de categorías utiliza la referencia retrospectiva de 2024; no reconstruye avisos históricos.

## Verificación de esta integración

Ejecutada sobre la compilación de producción local en `http://127.0.0.1:3033/` (rama local `sprint-3/historico-prediccion`, sin commit ni publicación).

- Python: **121 pruebas aprobadas**, incluidas las siete nuevas comprobaciones históricas; última ejecución 9.50 s.
- Trazabilidad: **118,525 comprobaciones aprobadas**. Los 349 archivos protegidos del estado inicial conservan SHA-256; las únicas cuatro modificaciones preexistentes autorizadas son las páginas de portada/metodología, navegación y registro del sitio. C05, inventario, originales y evidencia anterior permanecen intactos.
- Contrato web: 3,653 días, 6,225 orígenes y 18,675 objetivos; rechazo de cuatro cargas alteradas. También pasa el verificador anterior del Sprint 2 (once alteraciones rechazadas y controles del calendario).
- `npm run lint` ejecuta `tsc --noEmit`: aprobado. `npm run build`: aprobado; se generaron las rutas previstas, incluida la ruta de error de Next y el recurso de icono.
- Navegador real Microsoft Edge mediante Playwright CLI: **84 comprobaciones aprobadas** (45 escritorio, 27 móvil emulado de 390×844 con pantalla táctil, 12 del recorrido conservado del Sprint 2). No se detectaron errores de ejecución o recursos. La revisión móvil es emulación, no prueba en teléfono físico; no se probaron Safari ni Firefox.
- Animaciones medidas durante su ejecución: panel con opacidad intermedia 0.73 y final 1; indicador en posición intermedia antes de llegar a la pestaña; revelado de líneas, barras y puntos con recorte intermedio y estado final sin recorte. Se verificó igualdad de coordenadas, proporciones y colores entre estados. Se comprobó cancelación sin cola en cambios rápidos y estados finales con movimiento reducido, con teclado y controles manuales disponibles.
- Se contrastaron Buena/código 0 frente a ausencias, SO2 2023, NO2 exploratorio, febrero/29 de febrero, pareamiento de dos años bisiestos, la secuencia de 52 días que cruza de año, los orígenes sin evaluación y las fechas objetivo. Métricas y predicciones corresponden a los archivos congelados, incluidos los R² negativos. Descarga real de CSV y acceso HTTP 200 a las rutas anteriores comprobados.
- En móvil se corrigió el ancho del selector de fecha y hora para mostrar el origen completo. Tablas y gráficas tienen desplazamiento horizontal propio, sin ensanchar la página. Se revisaron capturas en tema claro y oscuro y las cuatro figuras analíticas del histórico.

Evidencia detallada: [verificador de datos](verificacion_datos.json), [resultados de navegador](../../../../output/playwright/integracion_sprint3/revision_navegador.json), scripts reproducibles y capturas en `output/playwright/integracion_sprint3/`. Capturas principales: `resumen_escritorio.png`, `calendario_escritorio.png`, `prediccion_contexto_escritorio.png`, `evaluacion_escritorio.png`, `resumen_movil.png`, `calendario_movil.png`, `prediccion_movil.png` y `evaluacion_movil_oscuro.png`.

Para repetir el navegador, iniciar el servidor anterior y crear sesiones CLI. Los comandos siguientes requieren Microsoft Edge instalado y `npx`; no añaden dependencias al proyecto:

```powershell
npx --yes --package @playwright/cli playwright-cli -s=mir-final open http://127.0.0.1:3033/ --browser msedge --headed
npx --yes --package @playwright/cli playwright-cli -s=mir-final run-code --filename output/playwright/integracion_sprint3/comprobar_escritorio.js
npx --yes --package @playwright/cli playwright-cli -s=mir-final run-code --filename output/playwright/integracion_sprint3/comprobar_conservacion_sprint2.js
npx --yes --package @playwright/cli playwright-cli -s=mir-mobile open http://127.0.0.1:3033/ --browser msedge --mobile --headed
npx --yes --package @playwright/cli playwright-cli -s=mir-mobile run-code --filename output/playwright/integracion_sprint3/comprobar_movil.js
```

Estos comandos de navegador se ejecutan desde la raíz del repositorio, no desde `web`. El servidor local se deja activo en el puerto 3033. El informe académico final del Sprint 3 y la presentación siguen fuera de esta integración. No hay inferencia en tiempo real, acreditación instrumental ni despliegue; los huecos y la exposición descriptiva previa de 2024 limitan la interpretación.
