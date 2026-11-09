# Primer modelado PM10: protocolo anterior al entrenamiento

Registro ejecutable: `config/sprint3_modelado_protocolo.json`, creado antes de ajustar los modelos. Guarda fecha UTC, ocho configuraciones, 47 características en orden, reglas y SHA-256 del manifiesto de fuentes. `datos_congelados.json` añade los hashes de las muestras y el umbral diagnóstico antes de la búsqueda. Los eventos de selección, congelación, reajuste y evaluación se registran secuencialmente en `eventos.jsonl`.

Objetivo: PM10 horario observado en µg/m³ a t+1, t+2 y t+3 desde un mismo origen t. No son NowCast, media diaria ni categorías. Se mantiene la hora local codificada de la fuente, sin inferir UTC/DST. 2024 ya fue explorado descriptivamente en el Sprint 2 y en el inventario: la evaluación será retrospectiva, no una prueba ciega.

## Muestras y particiones

- Entrenamiento: orígenes 2015–2022 y los tres objetivos anteriores a 2023.
- Validación/selección: orígenes 2023 y los tres objetivos anteriores a 2024.
- Evaluación final: orígenes 2024; los tres objetivos también pertenecen a la ventana disponible.
- Contexto obligatorio: 24 observaciones reales consecutivas, t−23..t. Las etiquetas se buscan por sus fechas exactas. No se compactan filas ni se interpolan interrupciones.
- Mismos orígenes para los tres modelos y los tres horizontes de la comparación global. La API de predicción solo lee historia hasta t y no requiere etiquetas futuras.
- Ceros finitos válidos; PM10 negativo/no finito no utilizable conforme al inventario. Sin eliminación de picos por magnitud. No se imputa ni recorta objetivo o predicción.
- El contexto de validación o evaluación puede comenzar en la partición anterior. El reajuste final usa las ventanas de 2015–2023 cuyos objetivos no entren en 2024. Una frontera interna de 2022 se puede recuperar en el reajuste si la ventana estaba completa.

Conciliación anterior al entrenamiento: **53,608 ventanas iniciales; tres exclusiones; 53,605 orígenes de comparación**. Se excluyen 2023-12-31 21:00, 22:00 y 23:00, cuyos tres objetivos invadirían 2024. Quedan **41,844 train**, **5,536 validación** y **6,225 test**. `auditoria_muestras.csv` explica cada hora, incluida o no; `conciliacion_mensual.csv` conserva los 120 denominadores mensuales y sus exclusiones por mes de origen. Las ventanas se solapan y no equivalen a observaciones independientes.

## Características y justificación en desarrollo

Las 47 características fijas son:

1. 24 concentraciones del contexto, `pm10_lag_0` a `pm10_lag_23`.
2. Media, desviación poblacional (ddof=0), mínimo y máximo de las últimas 3, 6, 12 y 24 horas, incluyendo t: 16 variables.
3. Seno/coseno de hora del día, día de la semana y fracción del año (365/366 días), más indicador de fin de semana: siete variables conocidas en t.

No se ajustan escaladores ni selección de variables; no hay meteorología. Cada resumen se calcula directamente sobre su propia ventana pasada. Los histogramas y particiones aprendidos por HGB se ajustan únicamente con entrenamiento, y después con 2015–2023 para el reajuste autorizado.

La EDA previa al ajuste usa exclusivamente **52,973 horas PM10 observadas entre 70,128 esperadas de 2015–2022**. Correlación por pares en fechas reales: lag 1 = 0.809 (52,368 pares), lag 3 = 0.512 (51,971), lag 24 = 0.498 (50,362) y lag 168 = 0.415 (47,012). Las medias por hora varían entre 41.3 y 93.2 µg/m³ y las medias por mes entre 32.3 y 86.8, con sus distintos n y ausencias visibles en `eda_perfiles_train.csv`. Esto justifica contexto reciente y calendario, sin demostrar causalidad ni estacionalidad libre de sesgo por faltantes.

## Referencias, familia y búsqueda

Persistencia predice y(t) en los tres horizontes. La referencia diaria predice y(t+h−24), es decir, los rezagos 23, 22 y 21 para h=1,2,3. Todos están dentro del contexto obligatorio; ninguna referencia usa meteorología u observaciones futuras.

Se utiliza `HistGradientBoostingRegressor`, un estimador directo independiente por horizonte. Es una familia tabular que permite relaciones e interacciones no lineales, con búsqueda por histogramas apropiada para decenas de miles de muestras. Una regresión lineal sería una alternativa más simple pero requeriría explicitar relaciones no lineales; Random Forest también puede representar interacciones, con otra estrategia de ensamblado y coste; SARIMA requeriría especificar su dinámica estacional y el tratamiento de las interrupciones. Estas razones motivan la familia inicial solicitada, sin afirmar superioridad previa. Referencias: [API oficial](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html) y [guía de ensembles](https://scikit-learn.org/stable/modules/ensemble.html#histogram-based-gradient-boosting).

Ocho combinaciones prefijadas: `max_leaf_nodes` ∈ {15,31}, `learning_rate` ∈ {0.05,0.1}, `max_iter` ∈ {150,300}. Parámetros fijos: pérdida squared_error, 30 muestras mínimas por hoja, L2=1, 255 bins, todas las características, `early_stopping=False`, `validation_fraction=None`, `warm_start=False`, semilla 20261108 y cuatro hilos. No se crea una partición aleatoria interna.

Selección: menor promedio aritmético del MAE en los tres horizontes de validación 2023. Para desempatar, se redondea ese promedio a ocho decimales y se prefieren menos hojas, menos iteraciones, menor learning_rate y, finalmente, menor identificador. No se añade ninguna configuración después de consultar la evaluación final.

Tras seleccionar, `config_congelada.json` fija parámetros, características, umbral, hashes de datos/código y versiones. Solo entonces se reajusta con 2015–2023 y se generan las predicciones de 2024. La configuración congelada no se cambia por su rendimiento final.

## Métricas y diagnóstico

MAE, RMSE, R² y n por modelo, horizonte y partición; errores firmados **predicho − observado**, positivos para sobreestimación. R² negativos se conservan. Con menos de dos observaciones o concentración observada constante, R² queda no calculable con motivo explícito. No se eliminan parejas no finitas para mejorar una métrica: se rechazan como error del contrato.

La agregación mensual de errores usa el **mes de la fecha objetivo**, manteniendo la partición por origen. El n mensual puede variar ligeramente entre horizontes al cruzar un mes, pero es idéntico entre modelos dentro de cada horizonte/mes. Se generan también filas sin muestras con n=0 y métricas no calculables. Los conteos de conciliación de ventanas usan mes de origen y se documentan por separado.

Concentración alta diagnóstica: observado ≥ **114 µg/m³**, percentil 90 (método lineal) de las horas utilizables únicas de 2015–2022, no de etiquetas repetidas por horizontes. Se fija antes del entrenamiento y no se actualiza al reajustar con 2023. No es una categoría normativa, una alarma validada ni una entrada del modelo.

Las métricas de entrenamiento son en muestra y optimistas. La evaluación final estará condicionada por las ventanas completas, la dependencia temporal, los huecos estacionales y la incertidumbre instrumental. No demuestra funcionamiento en tiempo real, capacidad causal, calibración física ni representatividad de los periodos sin información.
