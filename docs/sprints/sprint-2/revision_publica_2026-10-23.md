# Revisión del contenido público · 23 de octubre de 2026

Trabajo local en la rama `sprint-2/revision-01`. Se revisaron portada, ficha del Sprint 2, dashboard y `/metodologia`, sin recalcular resultados ni sustituir evidencia histórica.

## Cambios

- Portada y ficha: descripciones neutrales del análisis 2023–2024, sin mensajes de PDF ni gestión interna. La ficha usa una etiqueta pública descriptiva; el estado técnico interno sigue «en curso». El registro histórico del Sprint 1 conserva su estado anterior.
- Dashboard: encabezado descriptivo y sección «Metodología y evidencia del análisis». Se retiraron los mensajes sobre PDF y reporte del líder, así como el enlace de arranque del flujo principal. Siguen disponibles las descargas CSV, SVG y PNG.
- Metodología: ahora explica los dos años, fuentes, control de calidad, indicadores, unidades, población de cada resumen y limitaciones. Los nombres de indicadores y unidades se leen del contrato de datos existente. Las reglas normativas se distinguen de las decisiones del proyecto: referencia común 2024, 18 lecturas para máximos diarios de gases, contexto inicial, pareamiento, umbrales de cobertura, conjunto común, eventos y meteorología.
- Desarrollo: instrucciones de Git, estructura vigente y arranque en [docs/DESARROLLO.md](../../DESARROLLO.md), enlazadas desde README. La página pública ya no prescribe ramas, comandos, pull requests, fusiones ni etiquetas.
- Se conserva la URL del repositorio `https://github.com/BraulioJmz/CalidadAireJalisco`, correspondiente al remoto origin. No se encontró un PDF definitivo del Sprint 2; no se añadió un enlace a PDF. No se incorporó una bitácora de participación al dashboard.

## Conservación científica e histórica

Se mantuvieron los avisos de cobertura insuficiente, falta de validación instrumental, NO₂ exploratorio y ausencia de inferencia causal. No cambiaron reglas de cálculo, límites, datos, denominadores, figuras, dependencias ni evidencia del Sprint 1.

La comparación de SHA-256 antes y después confirmó 128 archivos intactos: código y pruebas de cálculo, configuración, fuentes, resultados, datos web, descargas y figuras, página del Sprint 1, pie del sitio y manifiestos de dependencias. La documentación histórica de decisiones y reproducción permanece en su ubicación técnica; sus copias de evidencia no se reescribieron.

## Verificación realizada

- `npm run lint`: aprobado (`tsc --noEmit`).
- `npm run build`: aprobado; genera `/`, `/sprint-1`, `/sprint-2` y `/metodologia`.
- `node scripts/validar-sprint2.mjs`: contrato aprobado y cuatro mutaciones rechazadas.
- `python -X utf8 -W error -m pytest tests -q` con el entorno local del proyecto: **73 pruebas aprobadas**.
- `git diff --check`: sin errores de espacios. Git avisa de la normalización LF/CRLF del archivo de metodología, sin impedir las comprobaciones.
- Servidor local de producción: cuatro páginas con HTTP 200 y navegación interna presente. Las 33 descargas enlazadas (26 del Sprint 2 y siete históricas) respondieron 200 y coincidieron por bytes con sus archivos locales.
- Playwright CLI con Edge aislado: navegación portada → metodología → Sprint 2 y Sprint 2 → Sprint 1; revisión de metodología en escritorio 1440×1000 y móvil 390×844. Ancho del documento y ventana móvil: 390 px. Descargas reales de `monthly.csv` y una figura SVG cotejadas por hash.
- Se conservaron cinco capturas y registros en `output/playwright/revision_publica_2026-10-23/`: `revision_visual.json`, `http_y_conservacion.json` y `conservacion_archivos.json`.

La consola mostró el 404 preexistente de favicon y un aviso de precarga CSS en portada. No se observaron errores de ejecución de la aplicación. Esta revisión no repite exhaustivamente todas las combinaciones de filtros, cuya lógica no cambió. El servidor temporal y el navegador de comprobación se cerraron al terminar.

## Estado de retorno

Cambios locales sin commit, push ni despliegue. No se marcó la entrega como realizada en Classroom ni en otro servicio. Los ZIP e informes anteriores conservan sus bytes y su alcance histórico; esta revisión de contenido no los reemplaza ni afirma una nueva verificación de empaquetado.
