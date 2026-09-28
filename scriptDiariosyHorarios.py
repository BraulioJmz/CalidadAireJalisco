import pandas as pd
# Resultados
# 1. Cargar datos desde el archivo CSV diario
df = pd.read_csv('Archivo2_Calculos_Diarios.csv')

contaminantes = ['PM10', 'PM2.5', 'CO', 'O3']
total_dias = len(df)

print("=" * 65)
print(f"ANÁLISIS DE RESULTADOS DIARIOS - ESTACIÓN MIRAVALLE ({total_dias} DÍAS)")
print("=" * 65)

# 2. Análisis del Criterio de Suficiencia (75% / >= 18 horas válidas)
print("\n" + "-" * 40)
print("1. EVALUACIÓN DE SUFICIENCIA DIARIA")
print("-" * 40)

for cont in contaminantes:
    col_suf = f'Suficiencia_{cont}'
    conteo_suf = df[col_suf].value_counts()
    cumple = conteo_suf.get('Cumple', 0)
    no_cumple = conteo_suf.get('No cumple', 0)
    pct_cumple = (cumple / total_dias) * 100
    print(f"{cont:6}: {cumple} días Cumple ({pct_cumple:.1f}%) | {no_cumple} días No cumple")

# 3. Estadísticos Descriptivos de los Indicadores Diarios
print("\n" + "-" * 40)
print("2. ESTADÍSTICAS DE LOS INDICADORES CALCULADOS")
print("-" * 40)

for cont in contaminantes:
    col_ind = f'Indicador_{cont}'
    stats = df[col_ind].describe()
    unidad = "ppm" if cont in ['CO', 'O3'] else "µg/m³"
    print(f"\nIndicador Diario {cont} ({unidad}):")
    print(f"  - Días evaluados: {int(stats['count'])}")
    print(f"  - Media mensual:  {stats['mean']:.2f}")
    print(f"  - Desv. estándar: {stats['std']:.2f}")
    print(f"  - Mínimo:         {stats['min']:.2f}")
    print(f"  - Mediana (Q2):   {stats['50%']:.2f}")
    print(f"  - Máximo:         {stats['max']:.2f}")

# 4. Distribución de Categorías Individuales
print("\n" + "-" * 40)
print("3. CATEGORÍAS INDIVIDUALES POR CONTAMINANTE")
print("-" * 40)

for cont in contaminantes:
    col_cat = f'Cat_{cont}'
    print(f"\nDistribución para {cont}:")
    conteo_cat = df[col_cat].value_counts()
    for cat, freq in conteo_cat.items():
        print(f"  - {cat:15}: {freq} días")

# 5. Distribución de la Categoría Global Diaria de la Estación
print("\n" + "-" * 40)
print("4. CATEGORÍA GLOBAL DIARIA DE LA ESTACIÓN (PEOR CONDICIÓN)")
print("-" * 40)

conteo_global = df['Cat_Global_Diaria'].value_counts()
for cat, freq in conteo_global.items():
    pct = (freq / total_dias) * 100
    print(f"  - {cat:15}: {freq} días ({pct:.1f}%)")

# 6. Identificación de contaminantes críticos en días "Mala"
print("\n" + "-" * 40)
print("5. CONTAMINANTES RESPONSABLES DE DÍAS CON CONDICIÓN 'MALA'")
print("-" * 40)

dias_malos = df[df['Cat_Global_Diaria'] == 'Mala']
print(f"Total de días en condición Mala: {len(dias_malos)}")

pm10_responsable = (dias_malos['Cat_PM10'] == 'Mala').sum()
o3_responsable = (dias_malos['Cat_O3'] == 'Mala').sum()
co_responsable = (dias_malos['Cat_CO'] == 'Mala').sum()
pm25_responsable = (dias_malos['Cat_PM2.5'] == 'Mala').sum()

print(f"  - Días donde PM10 estuvo en Mala:  {pm10_responsable}")
print(f"  - Días donde O3 estuvo en Mala:    {o3_responsable}")
print(f"  - Días donde PM2.5 estuvo en Mala: {pm25_responsable}")
print(f"  - Días donde CO estuvo en Mala:    {co_responsable}")

=================================================================
ANÁLISIS DE RESULTADOS DIARIOS - ESTACIÓN MIRAVALLE (31 DÍAS)
=================================================================

----------------------------------------
1. EVALUACIÓN DE SUFICIENCIA DIARIA
----------------------------------------
PM10  : 27 días Cumple (87.1%) | 4 días No cumple
PM2.5 : 22 días Cumple (71.0%) | 9 días No cumple
CO    : 29 días Cumple (93.5%) | 2 días No cumple
O3    : 28 días Cumple (90.3%) | 3 días No cumple

----------------------------------------
2. ESTADÍSTICAS DE LOS INDICADORES CALCULADOS
----------------------------------------

Indicador Diario PM10 (µg/m³):
  - Días evaluados: 27
  - Media mensual:  67.14
  - Desv. estándar: 13.01
  - Mínimo:         41.04
  - Mediana (Q2):   64.25
  - Máximo:         89.96

Indicador Diario PM2.5 (µg/m³):
  - Días evaluados: 22
  - Media mensual:  24.11
  - Desv. estándar: 6.11
  - Mínimo:         13.04
  - Mediana (Q2):   24.94
  - Máximo:         34.58

Indicador Diario CO (ppm):
  - Días evaluados: 29
  - Media mensual:  0.88
  - Desv. estándar: 0.17
  - Mínimo:         0.51
  - Mediana (Q2):   0.90
  - Máximo:         1.22

Indicador Diario O3 (ppm):
  - Días evaluados: 28
  - Media mensual:  0.06
  - Desv. estándar: 0.01
  - Mínimo:         0.04
  - Mediana (Q2):   0.06
  - Máximo:         0.09

----------------------------------------
3. CATEGORÍAS INDIVIDUALES POR CONTAMINANTE
----------------------------------------

Distribución para PM10:
  - Aceptable      : 14 días
  - Mala           : 12 días
  - Sin datos      : 4 días
  - Buena          : 1 días

Distribución para PM2.5:
  - Aceptable      : 20 días
  - Sin datos      : 9 días
  - Buena          : 2 días

Distribución para CO:
  - Buena          : 29 días
  - Sin datos      : 2 días

Distribución para O3:
  - Aceptable      : 19 días
  - Buena          : 9 días
  - Sin datos      : 3 días

----------------------------------------
4. CATEGORÍA GLOBAL DIARIA DE LA ESTACIÓN (PEOR CONDICIÓN)
----------------------------------------
  - Aceptable      : 17 días (54.8%)
  - Mala           : 12 días (38.7%)
  - Sin datos      : 2 días (6.5%)

----------------------------------------
5. CONTAMINANTES RESPONSABLES DE DÍAS CON CONDICIÓN 'MALA'
----------------------------------------
Total de días en condición Mala: 12
  - Días donde PM10 estuvo en Mala:  12
  - Días donde O3 estuvo en Mala:    0
  - Días donde PM2.5 estuvo en Mala: 0
  - Días donde CO estuvo en Mala:    0