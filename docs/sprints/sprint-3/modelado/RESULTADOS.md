# PM10 horario: resultados del primer experimento

Ejecutado localmente en `sprint-3/historico-prediccion`, sin publicar ni cambiar la interfaz o los documentos finales. Objetivo observado en µg/m³, horizontes +1,+2,+3 desde un mismo origen. Error firmado = predicho − observado, positivo para sobreestimación. No se usaron categorías, NowCast o medias diarias como objetivos.

## Registro y configuración seleccionada

Protocolo registrado antes de entrenar: `config/sprint3_modelado_protocolo.json`, SHA-256 `3833f883b244954690a43e2f933bb9c5920a0829a0a3750530678772cc4ecd08`. Congelación anterior a evaluar 2024: `config_congelada.json`, SHA-256 `6d3962cfbd281fec25b0e85e2d2f0d7f04c48f3d8f0e2ed92801e2aaf16f48a0`. La cronología queda en `eventos.jsonl` y se verifica automáticamente. 2024 ya se había explorado descriptivamente: esta evaluación es retrospectiva, no una prueba ciega. Sus métricas no se utilizaron para escoger decisiones.

Configuración **C05**, de ocho previamente fijadas: **max_leaf_nodes=31, learning_rate=0.05, max_iter=150**; pérdida squared_error, min_samples_leaf=30, L2=1, early_stopping=False, validation_fraction=None, semilla 20261108. Tres estimadores directos independientes, 47 características causales de PM10 y calendario, sin meteorología ni escaladores. Selección por promedio de MAE de 2023: **18.107754 µg/m³**. El desempate quedó definido en el protocolo; no fue necesario añadir configuraciones ni cambiar características al ver test.

La búsqueda se ajustó con 2015–2022. Después se congeló y reajustó con **47,380 ventanas de 2015–2023**. No se recuperaron ventanas extra de una frontera interna en este conjunto real. La función `pm10_modelado.predict_at` puede emitir los tres pronósticos con solo las últimas 24 observaciones y su origen, sin etiquetas futuras. No se recortaron predicciones; las de evaluación resultaron todas no negativas.

## Conciliación y disponibilidad

**53,608** ventanas iniciales del inventario → **3** orígenes excluidos por objetivos que cruzan 2023/2024 → **53,605** orígenes: **41,844** entrenamiento, **5,536** validación y **6,225** evaluación. Los tres orígenes excluidos son 2023-12-31 a las 21:00, 22:00 y 23:00. El contexto anterior a una partición sí puede utilizarse si era conocido en t. Las fechas bisiestas y los ceros reales se conservan.

| year | partition | expected_origins | pm10_observed | initial_window | boundary_excluded | included |
| --- | --- | --- | --- | --- | --- | --- |
| 2015 | train | 8760 | 6444 | 5535 | 0 | 5535 |
| 2016 | train | 8784 | 2100 | 1232 | 0 | 1232 |
| 2017 | train | 8760 | 7650 | 6492 | 0 | 6492 |
| 2018 | train | 8760 | 8070 | 7681 | 0 | 7681 |
| 2019 | train | 8760 | 8220 | 7135 | 0 | 7135 |
| 2020 | train | 8784 | 7989 | 5765 | 0 | 5765 |
| 2021 | train | 8760 | 5048 | 3769 | 0 | 3769 |
| 2022 | train | 8760 | 7452 | 4235 | 0 | 4235 |
| 2023 | validation | 8760 | 7976 | 5539 | 3 | 5536 |
| 2024 | test | 8784 | 8051 | 6225 | 0 | 6225 |

La conciliación por los 120 meses de origen está en `conciliacion_mensual.csv`; `auditoria_muestras.csv` documenta también los orígenes descartados por contexto u objetivos incompletos. No se compactó la rejilla ni se imputaron mediciones. En 2024 se observa PM10 en 8,051/8,784 horas (91.7 %), pero solo hay 6,225/8,784 orígenes completos (70.9 %). En julio quedan 268 fechas objetivo por horizonte, frente a hasta 716 en diciembre. El subconjunto es dependiente de las ausencias y no demuestra rendimiento en las horas omitidas.

## Búsqueda solo en 2023

| id | max_leaf_nodes | learning_rate | max_iter | mean_mae | mae_h1 | mae_h2 | mae_h3 | rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C05 | 31 | 0.050 | 150 | 18.108 | 13.501 | 19.309 | 21.513 | 1 |
| C06 | 31 | 0.050 | 300 | 18.132 | 13.465 | 19.369 | 21.563 | 2 |
| C02 | 15 | 0.050 | 300 | 18.158 | 13.467 | 19.388 | 21.620 | 3 |
| C04 | 15 | 0.100 | 300 | 18.160 | 13.437 | 19.461 | 21.582 | 4 |
| C03 | 15 | 0.100 | 150 | 18.166 | 13.490 | 19.454 | 21.553 | 5 |
| C01 | 15 | 0.050 | 150 | 18.196 | 13.567 | 19.410 | 21.611 | 6 |
| C07 | 31 | 0.100 | 150 | 18.206 | 13.465 | 19.477 | 21.676 | 7 |
| C08 | 31 | 0.100 | 300 | 18.323 | 13.543 | 19.603 | 21.823 | 8 |

MAE y RMSE se expresan en µg/m³; R² es adimensional. n es el número de predicciones por modelo y horizonte. Las tablas mantienen R² negativos. `n.c.` denota no calculable; los CSV incluyen el motivo. Los errores de entrenamiento son en muestra y no estiman generalización.

## Entrenamiento 2015–2022: métricas en muestra, optimistas

| model | horizon | n | mae | rmse | r2 | bias |
| --- | --- | --- | --- | --- | --- | --- |
| Diaria | 1 | 41844 | 29.157 | 49.355 | 0.003 | 0.024 |
| Diaria | 2 | 41844 | 29.160 | 49.488 | -0.002 | 0.051 |
| Diaria | 3 | 41844 | 29.189 | 49.457 | -0.004 | 0.069 |
| HGB | 1 | 41844 | 12.807 | 21.599 | 0.809 | -0.001 |
| HGB | 2 | 41844 | 17.215 | 27.329 | 0.695 | -0.002 |
| HGB | 3 | 41844 | 18.810 | 29.056 | 0.653 | -0.004 |
| Persistencia | 1 | 41844 | 16.426 | 30.476 | 0.620 | 0.010 |
| Persistencia | 2 | 41844 | 24.694 | 41.782 | 0.286 | -0.010 |
| Persistencia | 3 | 41844 | 30.008 | 48.868 | 0.019 | -0.018 |

## Validación 2023: selección; sin reajuste con 2023

| model | horizon | n | mae | rmse | r2 | bias |
| --- | --- | --- | --- | --- | --- | --- |
| Diaria | 1 | 5536 | 29.520 | 44.937 | -0.073 | 0.077 |
| Diaria | 2 | 5536 | 29.581 | 45.026 | -0.074 | 0.180 |
| Diaria | 3 | 5536 | 29.608 | 44.996 | -0.072 | 0.283 |
| HGB | 1 | 5536 | 13.501 | 20.522 | 0.776 | 0.318 |
| HGB | 2 | 5536 | 19.309 | 28.321 | 0.575 | 0.427 |
| HGB | 3 | 5536 | 21.513 | 31.155 | 0.486 | 0.322 |
| Persistencia | 1 | 5536 | 15.702 | 23.781 | 0.699 | 0.005 |
| Persistencia | 2 | 5536 | 25.195 | 37.246 | 0.265 | -0.069 |
| Persistencia | 3 | 5536 | 30.963 | 45.154 | -0.079 | -0.108 |

## Evaluación retrospectiva 2024: reajuste 2015–2023

| model | horizon | n | mae | rmse | r2 | bias |
| --- | --- | --- | --- | --- | --- | --- |
| Diaria | 1 | 6225 | 31.024 | 51.993 | 0.071 | -0.240 |
| Diaria | 2 | 6225 | 31.054 | 52.000 | 0.070 | -0.243 |
| Diaria | 3 | 6225 | 31.132 | 52.188 | 0.068 | -0.282 |
| HGB | 1 | 6225 | 16.208 | 27.717 | 0.736 | -0.619 |
| HGB | 2 | 6225 | 20.731 | 33.981 | 0.603 | -0.934 |
| HGB | 3 | 6225 | 22.801 | 36.939 | 0.533 | -1.053 |
| Persistencia | 1 | 6225 | 18.547 | 31.815 | 0.652 | -0.093 |
| Persistencia | 2 | 6225 | 27.398 | 45.058 | 0.302 | -0.162 |
| Persistencia | 3 | 6225 | 33.080 | 53.060 | 0.036 | -0.256 |

## Qué mejora y qué se pierde con el horizonte

| horizon | mae_reduction_vs_persistence_pct | mae_reduction_vs_daily_pct |
| --- | --- | --- |
| 1.000 | 12.607 | 47.755 |
| 2.000 | 24.335 | 33.242 |
| 3.000 | 31.074 | 26.761 |

En validación y evaluación el HGB mejora globalmente ambas referencias en MAE, RMSE y R². El MAE de test aumenta de **16.21 a 20.73 y 22.80 µg/m³** al pasar de +1 a +2 y +3 horas; el R² cae de 0.736 a 0.603 y 0.533. La concentración futura se vuelve menos próxima al estado reciente y al patrón calendario utilizado, sin que este experimento identifique causas del error.

La mejora global no es uniforme por mes. En julio de 2024, +1 h, HGB es **0.070 µg/m³ peor** en MAE que persistencia; a +2/+3 sí mejora. En julio de validación 2023 no mejora persistencia en ninguno de los tres horizontes. Estas excepciones se conservan, sin reajustar el experimento. Los CSV mensuales permiten inspeccionar todas las comparaciones. La referencia diaria y la persistencia a +3 en validación tienen R² negativos; no se han convertido en cero.

## Resultados mensuales del HGB en 2024

| horizon | month | n | mae | rmse | r2 | bias |
| --- | --- | --- | --- | --- | --- | --- |
| 1.000 | 1.000 | 713.000 | 19.262 | 30.467 | 0.779 | -0.786 |
| 1.000 | 2.000 | 387.000 | 19.681 | 31.095 | 0.702 | -1.523 |
| 1.000 | 3.000 | 540.000 | 18.615 | 30.122 | 0.671 | -1.825 |
| 1.000 | 4.000 | 451.000 | 14.882 | 23.314 | 0.627 | -0.864 |
| 1.000 | 5.000 | 486.000 | 13.275 | 18.756 | 0.666 | -0.098 |
| 1.000 | 6.000 | 425.000 | 9.464 | 14.662 | 0.731 | 0.104 |
| 1.000 | 7.000 | 268.000 | 7.282 | 9.980 | 0.590 | 1.627 |
| 1.000 | 8.000 | 439.000 | 7.504 | 10.938 | 0.542 | 0.827 |
| 1.000 | 9.000 | 488.000 | 7.172 | 10.506 | 0.490 | 1.026 |
| 1.000 | 10.000 | 621.000 | 17.090 | 28.759 | 0.637 | -0.908 |
| 1.000 | 11.000 | 693.000 | 19.615 | 34.211 | 0.641 | -0.260 |
| 1.000 | 12.000 | 714.000 | 27.110 | 42.520 | 0.659 | -2.632 |
| 2.000 | 1.000 | 712.000 | 27.811 | 42.076 | 0.579 | -0.643 |
| 2.000 | 2.000 | 387.000 | 25.625 | 38.752 | 0.541 | -2.327 |
| 2.000 | 3.000 | 540.000 | 20.535 | 31.176 | 0.641 | -2.492 |
| 2.000 | 4.000 | 451.000 | 18.517 | 28.166 | 0.455 | -1.624 |
| 2.000 | 5.000 | 487.000 | 16.218 | 22.285 | 0.548 | -0.963 |
| 2.000 | 6.000 | 424.000 | 11.576 | 16.659 | 0.651 | -0.061 |
| 2.000 | 7.000 | 268.000 | 8.619 | 11.941 | 0.413 | 2.371 |
| 2.000 | 8.000 | 439.000 | 9.140 | 13.342 | 0.350 | 1.061 |
| 2.000 | 9.000 | 488.000 | 8.715 | 12.513 | 0.277 | 1.495 |
| 2.000 | 10.000 | 621.000 | 22.741 | 35.773 | 0.440 | -2.019 |
| 2.000 | 11.000 | 693.000 | 26.001 | 42.161 | 0.454 | 1.127 |
| 2.000 | 12.000 | 715.000 | 34.081 | 51.344 | 0.502 | -4.533 |
| 3.000 | 1.000 | 711.000 | 31.214 | 46.443 | 0.484 | -0.542 |
| 3.000 | 2.000 | 387.000 | 28.947 | 42.686 | 0.445 | -2.027 |
| 3.000 | 3.000 | 540.000 | 21.926 | 32.593 | 0.609 | -2.114 |
| 3.000 | 4.000 | 451.000 | 18.744 | 28.462 | 0.447 | -1.596 |
| 3.000 | 5.000 | 488.000 | 17.028 | 23.395 | 0.502 | -1.292 |
| 3.000 | 6.000 | 423.000 | 12.803 | 17.965 | 0.588 | -0.076 |
| 3.000 | 7.000 | 268.000 | 9.523 | 13.485 | 0.250 | 2.955 |
| 3.000 | 8.000 | 439.000 | 9.855 | 14.468 | 0.257 | 1.062 |
| 3.000 | 9.000 | 488.000 | 9.517 | 13.155 | 0.210 | 1.920 |
| 3.000 | 10.000 | 621.000 | 25.321 | 38.694 | 0.344 | -2.949 |
| 3.000 | 11.000 | 693.000 | 28.205 | 44.752 | 0.385 | 1.016 |
| 3.000 | 12.000 | 716.000 | 38.725 | 57.529 | 0.385 | -5.485 |

Los errores mensuales se agrupan por mes de **fecha objetivo**, no por origen. Los tamaños pueden diferir entre horizontes al cruzar mes, pero dentro de cada horizonte/mes se conserva exactamente la misma muestra entre modelos. `metricas_mensuales.csv` incluye los tres modelos; los meses de entrenamiento agrupan sus ocho años. `metricas_anio_mes.csv` desglosa además cada año/mes, incluidas filas con n=0.

## Concentraciones altas y signo del error

Umbral fijo: observado ≥ **114 µg/m³**, percentil 90 de las **52,973 horas PM10 utilizables únicas del entrenamiento inicial** (método lineal). No es una categoría normativa ni se recalcula con validación o test.

| model | horizon | n | mae | rmse | r2 | bias |
| --- | --- | --- | --- | --- | --- | --- |
| Diaria | 1 | 832 | 76.614 | 98.253 | -1.618 | -47.275 |
| Diaria | 2 | 833 | 76.499 | 98.141 | -1.623 | -47.248 |
| Diaria | 3 | 834 | 76.862 | 98.737 | -1.629 | -47.646 |
| HGB | 1 | 832 | 43.394 | 59.224 | 0.049 | -28.078 |
| HGB | 2 | 833 | 56.287 | 73.357 | -0.466 | -44.985 |
| HGB | 3 | 834 | 62.429 | 80.089 | -0.730 | -53.009 |
| Persistencia | 1 | 832 | 50.493 | 66.249 | -0.190 | -20.161 |
| Persistencia | 2 | 833 | 73.193 | 89.371 | -1.176 | -41.861 |
| Persistencia | 3 | 834 | 84.613 | 101.425 | -1.774 | -59.035 |

HGB subestima las concentraciones altas: sesgo de **−28.08, −44.98 y −53.01 µg/m³**. Sus R² en este estrato son **0.049, −0.466 y −0.730**: pese a mejorar el MAE de las referencias, la predicción de extremos sigue siendo limitada. El sesgo negativo crece con el horizonte. Para observados por debajo del mismo umbral, el sesgo es positivo: **+3.62, +5.87 y +6.98 µg/m³**, respectivamente. El sesgo global pequeño oculta esa compensación; no se interpreta como ausencia de errores ni validación instrumental.

## Figuras y artefactos

- `figuras/01_desarrollo.png` y `.svg`: perfiles de entrenamiento, cobertura y autocorrelación con denominadores.
- `figuras/02_observado_predicho.png` y `.svg`: primera semana calendario de 2024, intervalo fijo, sin escoger por desempeño ni unir huecos.
- `figuras/03_dispersion.png` y `.svg`: todos los puntos HGB de evaluación, escalas comunes y picos conservados.
- `figuras/04_error_mensual.png` y `.svg`: MAE de los tres modelos y n mensual.
- `figuras/05_error_firmado.png` y `.svg`: predicho − observado y umbral diagnóstico. Los cinco PNG se revisaron visualmente; se exportaron sus equivalentes SVG. Catálogo con firmas en `figuras/catalogo_figuras.json`.

En `data/processed/sprint-3/modelado/`: protocolo referenciado y configuración congelada; datos horarios con procedencia, `features.npy`, `targets.npy`, orígenes y auditorías; búsqueda y métricas; nueve CSV de predicciones con origen, fecha objetivo, horizonte, observado, predicho, error firmado, modelo, partición y periodo de ajuste. Se conservan los seis artefactos `modelos/desarrollo/pm10_h*.joblib` y `modelos/reajuste/pm10_h*.joblib`, con contrato de características y fechas de entrenamiento. Los modelos de desarrollo son los de las métricas train/validation; los reajustados corresponden a test.

## Verificación y límites

**114 pruebas Python aprobadas**, incluidas 18 nuevas de fechas, fronteras, ceros, referencias, ausencia de futuro, estabilidad de características y métricas. Verificación adicional: **7,727 comprobaciones**, **482,445 filas de predicción** reproducidas desde referencias o artefactos, seis modelos recargados, n y MAE/RMSE/R² conciliados independientemente con scikit-learn, y **294 archivos anteriores intactos**. La conservación incluye originales, inventario y evidencia de ambos sprints. No hubo cambios del dashboard, PDF o Word. No se necesitó un nuevo build web porque sus archivos no cambiaron.

Los huecos son extensos y estacionales, las ventanas se solapan, no hay bitácoras instrumentales suficientes para probar homogeneidad entre años, y el test ya fue expuesto descriptivamente. La evaluación no demuestra funcionamiento en tiempo real, disponibilidad de datos sin retrasos, calibración instrumental, causalidad ni desempeño durante interrupciones. No se estimaron intervalos de incertidumbre o significación para las diferencias. La familia inicial no se comparó todavía con regresión lineal, Random Forest o SARIMA. No se cambió ninguna decisión a partir de los resultados finales.

## Reproducción

Dependencias: `requirements-sprint3-modelado.txt` incorpora el lock previo y fija scikit-learn 1.9.1 y sus dependencias adicionales. No se actualizó el entorno numérico previo. Las funciones de lectura/normalización del inventario se reutilizan sin modificar sus archivos.

Desde la raíz, estos comandos preparan el entorno y reproducen la secuencia ejecutada:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-sprint3-modelado.txt
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/preparar_modelado_sprint3.py
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/entrenar_sprint3.py seleccionar
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/entrenar_sprint3.py evaluar
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/verificar_modelado_sprint3.py
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/figuras_modelado_sprint3.py
.\.venv\Scripts\python.exe -X utf8 -W error pipeline/resumir_modelado_sprint3.py
.\.venv\Scripts\python.exe -X utf8 -W error -m pytest tests -q
```

La instalación real añadió exclusivamente las cinco dependencias nuevas fijadas, con `pip install --no-deps`, conservando las anteriores; `pip check` fue correcto. Los comandos de aprendizaje rechazan sobrescribir un experimento terminado o reabrir selección tras congelarlo. Para reproducir sin alterar esta evidencia, pasar a preparación, selección, evaluación y verificación el mismo `--out .scratch/repro_modelado_pm10`; para las figuras añadir `--figures .scratch/repro_figuras_pm10` y para este resumen `--report .scratch/repro_resultados_pm10.md`. Eso genera solo resultados de otra ejecución, no copia el proyecto. Los originales y el protocolo permanecen como entradas de solo lectura. Los tiempos de ejecución y registros UTC pueden variar, y no se presupone identidad binaria entre plataformas o versiones distintas.
