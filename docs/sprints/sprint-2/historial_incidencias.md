# Incidencias encontradas y resueltas durante la revisión

1. La carpeta inicial no contenía Git. Se pidió la ruta; el usuario autorizó clonar CalidadAireJalisco en una carpeta hermana. Se comprobó su ausencia antes de clonar; commit inicial 67a385204b87dfe8260974510d2cf305714b264c, sin cambios locales.
2. El Python suministrado no tenía SciPy. Se creó un entorno .venv del repositorio con Python 3.12 y dependencias fijadas, sin modificar el Python global ni los runtimes suministrados.
3. Las pruebas del prototipo fallaron inicialmente por UnicodeDecodeError de la codificación local de Windows. El mismo código pasa sus 24 pruebas con `-X utf8`. Sus FutureWarning de fillna y RuntimeWarning de series vacías permanecen en los logs; no se interpreta una advertencia como validación docente.
4. La primera batería ampliada detectó una discrepancia de Spearman al recalcular rangos desde los pares JSON: seis decimales de exportación fusionaban valores distintos. Se conserva precisión completa del JSON; los pares de Spearman se estabilizan a doce decimales para eliminar ruido de punto flotante y se exportan exactamente como se usan.
5. El comparador de exportaciones intentaba restar banderas booleanas al calcular diferencias. Se corrigió con comparación exacta de banderas y una prueba de regresión. No alteró fuentes ni cálculos ambientales.
6. El control independiente de 579 ventanas encontró CO 2024-03-23 22:00: esperado 0.49, cálculo previo 0.48 para una media exacta de 0.485. Se corrigieron sumas/promedios y ponderación con Decimal y se agregó prueba de frontera. Las diferencias respecto al prototipo se entregan, sin forzar coincidencias.

El resultado vigente de pruebas y verificaciones está en verificacion.json. Los fallos intermedios anteriores no se presentan como fallos pendientes cuando los controles finales pasan.
