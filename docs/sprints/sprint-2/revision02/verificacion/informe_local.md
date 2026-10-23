# Verificación local · revisión 02

Estado: **APROBADO en el entorno local**. No equivale a comprobación de transporte.

- 73 pruebas Python con avisos tratados como errores; 0 fallos, 0 errores, 0 omitidas. Incluyen las 54 anteriores.
- npm ci con package-lock sin cambiar versiones web; contrato, tipos y build de producción correctos.
- Recursos web derivados del pipeline, pruebas contra CSV de diciembre y denominadores, 31/31 Buena en CO en ambos años.
- Matplotlib 3.10.8 se añade para seis figuras SVG/PNG; se preservan versiones numéricas previas y se actualiza el lock Python coherentemente.
- Lista de insumos obligatorios para firma y ZIP, independiente de Git; ambos Excel y recursos públicos exigidos antes de empaquetar.
- Revisión visual efectiva y capturas: output/playwright/revision_visual.json. Se conserva un 404 preexistente de favicon; no se detectaron errores de ejecución de la aplicación en las vistas revisadas.

La verificación limpia se entrega como informe externo asociado al SHA-256 exacto del ZIP: el script reproducir_zip_sprint2.py crea entornos nuevos, prueba originales y extractos separadamente y arranca la aplicación de la extracción. Este informe local no declara por adelantado el éxito de ese control.

Rama: sprint-2/revision-01; cambios locales sin commit, push o deploy. Se preserva Sprint 1; navegación, portada, registro del Sprint 2 y configuración de build reciben las ediciones autorizadas. El PDF final, reflexiones, bitácora del líder y correcciones de clase permanecen pendientes de aportaciones reales.
