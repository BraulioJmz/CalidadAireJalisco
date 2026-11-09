# Interfaz editorial de Academia Miravalle

Refinamiento local de la aplicación, sobre `sprint-3/historico-prediccion`. Esta nota técnica complementa la evidencia de integración anterior; no sustituye el protocolo, los hallazgos ni el experimento congelado.

La navegación actual organiza la lectura en Panorama, Histórico, Episodios y Predicción. Comparación, categorías y cobertura pertenecen a Histórico; consulta por origen, métricas y errores pertenecen a Predicción. Las subsecciones tienen URL propia mediante fragmentos y funcionan con atrás/adelante. Los filtros indican su alcance y no se duplican entre funciones.

La portada usa una jerarquía editorial: titular principal y distribución de categorías de diciembre de 2023/2024, tres artículos secundarios y una entrada al pronóstico y su evaluación. Los identificadores históricos permanecen en datos, atributos de trazabilidad y documentación; no se presentan como títulos públicos. Las categorías anuales respetan el filtro de año: para 2015–2024 se muestran diez distribuciones con sus denominadores, sin promediar códigos ordinales.

`ApplicationShell` aísla el encabezado y pie actuales de los de archivo. `ArchiveNavigation` conserva las cuatro entradas de la navegación anterior. Los cuerpos de `/sprint-1` y `/sprint-2`, sus componentes analíticos, estilos originales y datos no se modificaron. Esas rutas muestran interfaces anteriores; los enlaces aparecen únicamente en «Versiones anteriores» del pie de la aplicación actual. No se restauraron archivos globales a versiones antiguas.

La meteorología deja de ser una sección visual del tablero. Sus fuentes, agregados, pares, análisis y descargas siguen intactos. Metodología explica que el modelo usa PM10 y calendario, con meteorología discontinua en las fuentes: no se demostró irrelevancia predictiva. Se conserva la distinción entre concentración observada/predicha, categoría retrospectiva, ausencia, insuficiencia y umbral diagnóstico.

Verificación sobre la compilación de producción local en `http://127.0.0.1:3033/`:

- Tipos (`npm run lint`, que ejecuta `tsc --noEmit`) y build aprobados.
- 121 pruebas Python aprobadas. Contratos web de integración y de la comparación anterior aprobados.
- 100 comprobaciones de navegador Edge: 55 escritorio, 33 móvil emulado y 12 del recorrido temporal archivado. Incluyen teclado, foco, movimiento reducido, cambios rápidos, atrás/adelante, filtros, fechas, categorías, métricas y descarga real.
- Estados intermedios observados: opacidad de panel entre 0 y 1, indicador entre posiciones inicial y final, revelado con recorte intermedio. Los elementos terminan legibles; coordenadas y colores de categorías se conservan.
- Referencia de archivo: commit `527af8a4781df65ede43b746dffdddb330915740`. Cuerpo y estilos de las vistas iguales a ese estado; la captura previa normalizó únicamente el encabezado compartido a sus cuatro entradas originales. Comparación de estilos y rectángulos de títulos, navegación, seis tarjetas y seis párrafos por ruta: idénticos. Capturas iniciales de escritorio de 1440×1000: cero píxeles diferentes para ambas rutas. Se probó también su funcionamiento y presentación móvil.
- Los 806 archivos protegidos al inicio de este refinamiento conservan su SHA-256. Por identidad de las entradas y resultados analíticos se reutiliza la verificación histórica previa de 118,525 comprobaciones. No se entrenó ni reajustó el modelo.

Evidencia y scripts: `output/playwright/editorial/`; resumen estructurado en `verificacion.json`. Las capturas incluyen portada, hallazgo, categorías, predicción y vistas archivadas. La revisión móvil utilizó emulación táctil de 390×844 y comprobaciones de ancho de 320 y 360 px; no se probó hardware físico, Safari ni Firefox. No se añadieron dependencias.

Para repetir las interacciones, iniciar el servidor desde `web` con `node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3033`. Desde la raíz del repositorio, usar Playwright CLI con las sesiones `mir-final` (Edge, escritorio) y `mir-mobile` (Edge, `--mobile`), y ejecutar `comprobar_interfaz.js` y `comprobar_movil.js` de la carpeta de evidencia. El recorrido archivado usa el script anterior `output/playwright/integracion_sprint3/comprobar_conservacion_sprint2.js`.

El servidor local se deja activo. No se hicieron commits ni publicaciones; PDF, Word, modelos y resultados anteriores permanecen intactos.
