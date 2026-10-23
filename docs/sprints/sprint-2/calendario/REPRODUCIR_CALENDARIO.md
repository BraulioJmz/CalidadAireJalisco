# Reproducir el calendario comparativo

Python 3.12 y Node 24; ejecutar desde la raíz del proyecto. Las fuentes, los 24 resultados calculados y las figuras se conservan. No es necesario ejecutar de nuevo el análisis normativo para ampliar o visualizar el calendario.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-sprint2-lock.txt
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/exportar_sprint2_web.py
.\.venv\Scripts\python.exe -X utf8 -W error -m pytest tests -q
Set-Location web
npm ci --no-audit --no-fund
node scripts/validar-sprint2.mjs
npm run lint
npm run build
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3012
```

Abrir `http://127.0.0.1:3012/sprint-2` y la pestaña **Episodios**. Elegir contaminante, año y mes en los filtros generales. En «Todo el año», elegir **Mes del calendario**. Seleccionar una fecha o usar los botones de recorrido; el estado inicial es pausado. Con movimiento reducido solo se habilita el recorrido manual.

El contrato `mir-s2-v2` añade 731 registros diarios y los nombres/unidades de sus estadísticos. Cada fecha proviene de `MIR_2023_diario.csv` o `MIR_2024_diario.csv`: I, EXACT, C, N y N_IND del contaminante; M y N de ET/RH/WS; HORAS_ESPERADAS. El exportador valida fechas, dimensiones, nulos, conteos y reconciliación de categorías con los resúmenes mensuales/anuales. El contrato TypeScript vuelve a validar al leer; ninguna de estas comprobaciones reconstruye bandas normativas.

Los CSV diarios se descargan desde el calendario y desde el bloque de evidencia. Se conservan todos los recursos anteriores. La guía metodológica pública y sus avisos científicos siguen en `/metodologia`; Git y desarrollo se documentan en `docs/DESARROLLO.md`.

## Interacciones de la versión actual

Las siete pestañas incluyen indicador deslizante y entrada breve de contenido. Las líneas y barras se revelan sin cambiar su geometría final; los puntos aparecen por opacidad. El calendario anima la selección y el detalle, muestra una barra de avance y ofrece «Volver a reproducir» al finalizar. El 29/02/2024 mantiene la explicación de fecha equivalente inexistente en 2023, sin mostrar esa fecha inexistente como encabezado. No hay avance automático al entrar; movimiento reducido conserva estados finales y controles manuales. Véase `docs/DESARROLLO.md` para la estructura de estas interacciones.

Las comprobaciones aplicables a esta interfaz son los comandos de pruebas, contrato/recorrido, tipos y build indicados al principio de esta guía, junto con revisión en navegador de estados intermedios, cambios rápidos, repetición, filtros y movimiento reducido. Los registros visuales y `comprobar_navegador.js` conservados pertenecen a la revisión anterior al botón de repetición: no son una aprobación automática de la interfaz actual.

## Verificación y paquete de la revisión histórica del calendario

Detener los servidores locales antes de reinstalar npm en Windows. Desde la raíz:

```powershell
.\.venv\Scripts\python.exe -X utf8 pipeline/verificar_calendario.py
.\.venv\Scripts\python.exe -X utf8 pipeline/empaquetar_calendario.py
.\.venv\Scripts\python.exe -X utf8 pipeline/reproducir_zip_sprint2.py --zip entregas/sprint2_calendario_comparativo.zip --informe entregas/verificacion_zip_calendario.json
```

El primer comando verifica la conservación de 108 archivos registrados antes de este cambio, la vigencia de la evidencia visual, instalación npm con lock, contrato/recorrido, tipos, build y todas las pruebas Python. Sus informes se guardan en `calendario/verificacion/` y no sobrescriben los informes históricos de revisión 02. Para revisar otra versión de la interfaz, actualizar el registro visual solo tras comprobarla efectivamente.

Esos verificadores exigen las firmas y los registros de la versión que ensayan y rechazan entradas posteriores desactualizadas. Los informes históricos se preservan; no se regeneran ni se usa su estado para afirmar que las animaciones ya fueron comprobadas por ellos. La publicación en GitHub no requiere crear otro ZIP.

El paquete exige firma de entradas vigente, incluye ambos Excel originales y recursos obligatorios, manifiesto interno y huella SHA-256 externa. El último comando extrae el ZIP sin Git, instala entornos nuevos, reproduce por separado los 24 resultados desde originales y extractos, exporta el calendario, ejecuta pruebas, contrato/recorrido, tipos, build y comprueba las páginas y descargas por HTTP. Los resultados de esa ejecución se entregan fuera del ZIP para identificar el archivo exacto ensayado.

La evidencia interactiva se registra en `output/playwright/calendario_2026-10-23/`. El archivo `comprobar_navegador.js` es una función para Playwright CLI (`run-code --filename`), sin dependencia de `@playwright/test`; requiere una página abierta en el servidor local y usa su mismo origen. Produce seis capturas y comprueba los casos solicitados, teclado y movimiento reducido. La extracción limpia no repite automáticamente esa interacción completa: verifica los datos y el build del mismo código ya revisado.

Se mantienen la rama actual y los cambios locales de la revisión pública. Los paquetes anteriores conservan su alcance histórico. Estos comandos no hacen commit, push, despliegue ni entrega en Classroom.
