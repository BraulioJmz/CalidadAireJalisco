# Calidad del aire · Miravalle (MIR)

Proyecto de **Análisis y Visualización de la Información** (Equipo 3). Nuestra "agencia" es una institución
académica ficticia, la **Academia Miravalle**, que usa los datos de SEMADET y la **NOM-172-SEMARNAT-2023**
(Índice AIRE Y SALUD) para decidir cuándo y cómo realizar actividades al aire libre.

Cada sprint entrega un **boletín** (una ruta del sitio) y el sitio completo es el **dashboard final**.

```
calidad-aire-miravalle/
├─ BD_2024.xlsx         base anual de SEMADET (no se versiona; solo lectura)
├─ pipeline/
│  ├─ etl.py            BD_<AÑO>.xlsx → año limpio y recorte del periodo (con 24 h de calentamiento)
│  ├─ calculos.py       periodo limpio → Archivo1 (horario) y Archivo2 (diario), NOM-172
│  ├─ procesar.py       orquesta los tres pasos y arma el JSON del sitio y los Excel
│  ├─ nom172.py         NowCast de la profesora, CO 8 h, bandas y categorías
│  └─ limpieza.py       perfil, control de calidad y bitácora
├─ tests/               NowCast de la profesora, reglas de categorías y regresión de marzo
├─ data/processed/
│  ├─ miravalle_2024_clean.csv   año limpio (se versiona: permite correr sin BD_2024.xlsx)
│  └─ AAAA-MM/          miravalle_<mes><año>_clean.csv, Archivo1, Archivo2, Excel y bitácora
├─ docs/sprints/        resumen y decisiones de cada entrega
└─ web/                 sitio Next.js (dashboard)
   ├─ app/page.tsx              Observatorio: dashboard final, siempre con el último periodo
   ├─ app/sprint-1/page.tsx     Boletín 1 (marzo 2024), congelado
   ├─ app/metodologia/          criterios y cómo crece el proyecto
   ├─ components/               calendario, simulación, gráficas, tablas (reutilizables)
   ├─ lib/site.ts               nombre de la academia y registro de sprints
   └─ data/periodos/*.json      salida del pipeline que lee el sitio
```

## Pipeline (Python)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python pipeline/procesar.py --periodo 2024-03        # ETL + cálculos + JSON del sitio (usa BD_2024.xlsx si está en la raíz)
python pipeline/etl.py --periodo 2024-03             # solo el ETL
python pipeline/calculos.py --periodo 2024-03        # solo Archivo1 y Archivo2
python -m pytest tests
```

## Sitio (Next.js)

```bash
cd web
npm install
npm run dev          # http://localhost:3000
npm run build        # verificación antes de subir
```

### Vercel
Importar el repositorio en vercel.com y en **Settings → Build & Deployment → Root Directory** poner `web`.
Framework: Next.js (se detecta solo). Cada rama y cada pull request obtiene su propio enlace de vista previa;
`main` es producción.

## Flujo de trabajo por sprint

| Paso | Comando / acción |
|---|---|
| 1. Rama del sprint | `git switch -c sprint-2` |
| 2. Nuevo periodo | `python pipeline/procesar.py --periodo 2024-04` |
| 3. Nueva ruta | copiar `web/app/sprint-1` a `web/app/sprint-2` y agregar la fila en `web/lib/site.ts` |
| 4. Revisión | pull request → enlace de preview en Vercel |
| 5. Entrega | merge a `main` y `git tag sprint-2 && git push --tags` |

Las entregas pasadas no se tocan: su ruta y su tag quedan como evidencia de lo entregado.
