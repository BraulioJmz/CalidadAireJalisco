# Reproducir la revisión 02

Python 3.12; comandos desde la raíz de CalidadAireJalisco. No se necesita Node, red, ni la aplicación para ejecutar cálculos con el entorno ya instalado. Los CSV fuente y los dos Excel originales están incluidos. Instalar dependencias requiere acceso a PyPI o ruedas locales.

Para el tablero se necesita Node 24 (verificado con 24.1.0) y npm, usando el package-lock.json suministrado. El ZIP 01 omitió BD_2024.xlsx: la reproducción desde extractos fue correcta, pero no era autosuficiente desde ambos originales. La selección obligatoria y la comprobación limpia de esta revisión corrigen esa omisión. El informe externo identifica el SHA-256 exacto del ZIP probado.

## Exportación web, figuras y arranque

Después de instalar el lock Python y ejecutar el pipeline:

```powershell
.\.venv\Scripts\python.exe -X utf8 -W error pipeline\exportar_sprint2_web.py
.\.venv\Scripts\python.exe -X utf8 -W error pipeline\figuras_sprint2.py
Set-Location web
npm ci --no-audit --no-fund
node scripts/validar-sprint2.mjs
npm run lint
npm run build
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3012
```

Abrir `http://127.0.0.1:3012/sprint-2`. La portada enlaza también el análisis anual. Para desarrollo, `npm run dev`. Estos comandos operan sobre recursos del ZIP y no necesitan el paquete anterior. El build no ejecuta Python: el exportador ya produjo `web/data/sprint2.json`, validado al leerlo, y los CSV/figuras en `web/public/descargas/sprint-2/`. No se sirven los Excel completos al navegador.

Figuras: `docs/sprints/sprint-2/figuras/` contiene seis SVG y PNG de 220 dpi, `catalogo_figuras.md` y `hallazgos.csv` con filtros, columnas, fechas, n y cálculos. La propuesta conserva el estilo del sitio y distingue datos ausentes, cobertura, composición de globales y estadísticos horarios/diarios. NO2 solo se muestra como exploratorio 2024. PDF y bitácora real del líder siguen pendientes.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-sprint2-lock.txt
.\.venv\Scripts\python.exe -X utf8 -W error pipeline\anual.py
.\.venv\Scripts\python.exe -X utf8 -W error -m pytest tests -q
```

Si no está instalado el lanzador `py`, sustituirlo por la ruta de Python 3.12. El archivo requirements-sprint2.txt fija las dependencias directas; requirements-sprint2-lock.txt incluye también las transitivas del entorno verificado. UTF-8 explícito evita que Windows use su codificación local para lectura de JSON y registros. No se modifica el Python global.

## Extracción completa desde los originales incluidos

```powershell
.\.venv\Scripts\python.exe -X utf8 -W error pipeline\anual.py --bd-2023 data\source\sprint-2\originales\BD_2023.xlsx --bd-2024 data\source\sprint-2\originales\BD_2024.xlsx --out .scratch\desde_excel
```

El comando valida hashes conocidos de los Excel, lee Data sin escribir en el libro, regenera los extractos con encabezados normalizados y procedencia, y calcula resultados en el destino indicado. La ejecución predeterminada verifica los hashes de los extractos registrados en config/fuentes_sprint2.json. Un archivo diferente causa un error; no se aceptan cambios de fuente silenciosos.

Para incorporar el paquete suministrado desde su ubicación hermana original:

```powershell
.\.venv\Scripts\python.exe -X utf8 pipeline\preparar_sprint2.py --paquete ..\Sprint2_Miravalle_Para_Codex\Sprint2_Miravalle_Para_Codex
```

Comprueba los 38 hashes antes de copiar; rechaza sobrescribir una copia original diferente. Se preservan ambos Excel y cuatro PDF de evidencia. Conserva todas las columnas originales MIR en el extracto, incluyendo NO y NOX, aunque el análisis no los usa como contaminantes criterio.

## Qué revisar

- `data/processed/sprint-2/resumen.json`: resultados, reglas, fuentes, pares, categorías, meteorología y episodios; JSON estricto sin NaN/Infinity.
- `MIR_AAAA_depurado.csv`, `MIR_AAAA_horario.csv` y `MIR_AAAA_diario.csv`: rejillas completas de 8,760/8,784 horas y 365/366 días.
- `coverage.csv`: disponibilidad anual (month=0) y mensual; filas esperadas, filas presentes/ausentes, mediciones faltantes, exclusiones y utilizables. La suma de esos cuatro estados reconcilia con expected. raw cuenta valores numéricos antes de exclusiones.
- `statistics.csv`: estadísticas de magnitudes continuas con unidad, n, denominador, desviación estándar muestral, cuantiles y todas las fechas empatadas en el máximo. `annual.csv` y `monthly.csv` añaden distribuciones de categorías diarias; `profiles.csv` distribuciones por hora del día.
- `available.csv`: distribución global disponible; `dominance.csv`: todos los determinantes empatados del global comparable. Porcentajes de Mala o peor usan días/horas con categoría, no todos los esperados; missing y expected se entregan aparte.
- `comparacion_pareada.csv`, `pares_diarios.csv`: medias de bases diarias antes de redondear, fechas, cobertura, representación trimestral y banderas; global compara proporciones, sin medias de categorías.
- `meteorologia.csv`, `pares_meteorologicos.csv`: Spearman mensual y los pares exactos usados. Sin p-valores; mínimo 15 pares. La dirección WD se trata circularmente solo en el archivo diario.
- `bitacora_calidad.csv`: valor original, regla, acción, motivo, fuente y fila Excel para cada exclusión o señalamiento. Los estados por variable del horario diferencian fila ausente, medición faltante, exclusión y utilizable; una categoría horaria puede existir con medición actual ausente si la ventana cumple suficiencia.
- `dias_relevantes.csv`, `contexto_dias_relevantes.csv`, `horas_relevantes.csv`, `episodios.csv`: selección definida en decisiones_metodologicas.md.
- `docs/sprints/sprint-2/informe_verificacion.md`, `verificacion.json`, `pruebas.xml`: controles, comandos, resultados y limitaciones.

Columnas: `N_p`=lecturas crudas utilizables del día; `N_IND_p`=bases horarias suficientes; `EXACT_p`=base diaria antes de redondeo; `I_p`=base redondeada; `C_p`=categoría ordinal 0..4 (Buena..Extremadamente Mala), vacío=sin indicador suficiente. I_GLOBAL es un alias histórico de C_GLOBAL, **no una concentración ni un índice numérico para promediar**. N8_CO, N12_PM y N3_PM auditan disponibilidad de ventanas.

`GLOBAL_PARCIAL` indica que falta algún contaminante de seis; `CORE_PARCIAL` indica que falta alguno del conjunto fijo de cuatro. Todas las categorías son retrospectivas con referencia 2024. Fechas sin zona mantienen el tiempo civil de la fuente. WD y WS se usan solo para descripción, sin atribución de fuentes.

## Verificación y paquete

```powershell
.\.venv\Scripts\python.exe -X utf8 pipeline\verificar_revision02.py
.\.venv\Scripts\python.exe -X utf8 pipeline\empaquetar_sprint2.py
.\.venv\Scripts\python.exe -X utf8 pipeline\reproducir_zip_sprint2.py --zip entregas\sprint2_revision_02.zip --informe entregas\verificacion_zip_revision02.json
```

El primer comando separa verificaciones locales: instalación npm con lock, contrato web, tipos, build y controles del pipeline. El verificador base ejecuta todas las pruebas con avisos como errores, verifica conservación de evidencia Sprint 1, fuentes y una muestra independiente de ventanas. Coteja además el camino Excel frente a los resultados entregados. El contraste histórico con el prototipo está conservado; puede repetirse con `pipeline/verificar_sprint2.py --prototipo .scratch/prototipo/data/processed/sprint-2` si se conserva esa copia externa de diagnóstico. No se necesita para reproducir esta revisión.

El tercer comando **crea una carpeta temporal limpia sin Git, un entorno Python nuevo e instala npm ci dentro de la extracción**. Comprueba manifiesto y ambos Excel; reproduce los 24 resultados por separado desde originales y desde extractos, coteja categorías/fechas/textos/ausencias exactamente y magnitudes continuas a tolerancia absoluta 1e-10 (incluye diferencias trigonométricas de WD entre plataformas). Ejecuta pruebas, exportación web, contrato, tipos, build y arranque HTTP desde el código extraído. No utiliza .venv, node_modules, fuentes ni rutas del checkout como reemplazo de archivos omitidos. El directorio temporal queda registrado para auditoría y el servidor de prueba se detiene al terminar. Instalar desde los locks requiere red o cachés de paquetes válidas; las dependencias no se distribuyen en el ZIP.

Las comprobaciones se distinguen expresamente: pruebas locales no prueban por sí solas transporte completo; reproducción desde extractos no prueba presencia de originales; reproducción limpia desde ambos originales sí verifica esa autosuficiencia. Los informes locales están en `revision02/verificacion/`; el informe externo de extracción limpia corresponde al hash del ZIP y se entrega junto a él, evitando un ciclo de reempaquetado del propio informe.

El ZIP contiene el proyecto y los resultados, sin .git, .venv, dependencias, cachés ni .scratch. Incluye manifiesto SHA-256 de contenidos; se entrega otra huella del propio ZIP. El estado Git es una rama local con cambios sin commit de implementación salvo que el informe indique lo contrario. No se hace push, merge ni publicación.
