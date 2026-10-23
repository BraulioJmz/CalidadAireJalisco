# Desarrollo y organización técnica

Esta documentación acompaña al análisis retrospectivo MIR 2023–2024. Las instrucciones de Git, estructura y arranque se mantienen aquí; `/metodologia` explica al público las fuentes, reglas y límites del análisis.

## Estructura vigente

```text
CalidadAireJalisco/
├─ config/fuentes_sprint2.json       procedencia y hashes de fuentes
├─ data/source/sprint-2/             originales y extractos, sin modificar
├─ data/processed/sprint-2/          24 resultados calculados
├─ pipeline/
│  ├─ normativa.py                  reglas de la revisión retrospectiva
│  ├─ anual.py                      análisis 2023–2024
│  ├─ exportar_sprint2_web.py        resultados → contrato JSON y descargas
│  ├─ figuras_sprint2.py             equivalentes científicos SVG/PNG
│  ├─ verificar_revision02.py        verificación integral local
│  ├─ reproducir_zip_sprint2.py      reproducción aislada desde un ZIP
│  └─ etl.py, calculos.py, procesar.py, nom172.py
│                                   flujo mensual histórico del Sprint 1
├─ tests/                           pruebas de cálculo y regresiones
├─ docs/sprints/sprint-2/            decisiones, reproducción y evidencia
├─ output/playwright/               registros y capturas de revisión
└─ web/
   ├─ app/page.tsx                  portada y observatorio mensual
   ├─ app/sprint-1/                 evidencia histórica de marzo de 2024
   ├─ app/sprint-2/                 análisis retrospectivo
   ├─ app/metodologia/              explicación pública 2023–2024
   ├─ components/sprint2/           presentación y filtros del análisis
   ├─ lib/site.ts                  identidad, enlaces y registro de sprints
   ├─ lib/sprint2-contract.ts       validación de datos al leer el JSON
   ├─ data/sprint2.json             resultados exportados, sin normativa JS
   └─ public/descargas/             CSV, figuras y documentación de evidencia
```

`pipeline/procesar.py --periodo AAAA-MM` corresponde al flujo mensual histórico; no sustituye la reproducción anual del Sprint 2. Los dos métodos y su evidencia se documentan por separado. No copiar la página del Sprint 1 para reemplazarla ni modificar sus datos al editar contenido público.

## Entorno y desarrollo web

Python 3.12 y dependencias fijadas en `requirements-sprint2-lock.txt`; Node 24 y `web/package-lock.json`. Las instrucciones completas del cálculo, fuentes y empaquetado están en [REPRODUCIR.md](sprints/sprint-2/REPRODUCIR.md). Para editar únicamente textos públicos no se necesita recalcular los datos ni exportar de nuevo las figuras.

Desde `web/`:

```powershell
npm ci --no-audit --no-fund
npm run dev
```

Antes de revisar cambios web:

```powershell
node scripts/validar-sprint2.mjs
npm run lint
npm run build
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3012
```

`lint` ejecuta TypeScript (`tsc --noEmit`). Revisar `/`, `/sprint-1`, `/sprint-2` y `/metodologia`, la navegación y las descargas reales. Detener los servidores locales antes de reinstalar dependencias si Windows mantiene bloqueada una biblioteca de Next.

Los indicadores y categorías se calculan en Python. El navegador presenta el JSON validado y los archivos calculados; no debe implementar otra normativa. Los resúmenes, las proporciones, los nulos y las unidades deben conservar su significado al cambiar textos.

### Interacciones visuales vigentes

`web/components/sprint2/Motion.tsx` centraliza las entradas cancelables y la preferencia de movimiento reducido. Las pestañas desplazan su indicador y admiten flechas, Inicio y Fin. Paneles, tarjetas y detalles usan entradas de 320 ms; líneas y barras se revelan mediante recorte de su geometría final y los puntos meteorológicos aparecen por opacidad. Se usan Web Animations y CSS del navegador, sin dependencias adicionales. Cambios rápidos sustituyen la entrada anterior, sin colas ni paneles duplicados.

El calendario muestra progreso por día, conserva selección sincronizada y al final ofrece «Volver a reproducir». Solo pulsarlo reinicia desde el día 1; con movimiento reducido vuelve pausado al inicio. Los cambios de filtro pausan incluso si el mes efectivo permanece igual al alternar con «Todo el año». Las animaciones no modifican coordenadas de las gráficas, valores, colores de categoría, escalas, fuentes ni reglas científicas.

## Git y revisión

Comenzar leyendo el estado real del checkout:

```powershell
git status --short
git branch --show-current
git diff --check
git diff
```

Trabajar en la rama que corresponda al encargo y conservar cambios locales existentes. Una solicitud de revisión de contenido no implica crear otra rama, descartar archivos, hacer commit, fusionar, etiquetar, subir cambios ni desplegar. La revisión pública se realizó en `sprint-2/revision-01`; la publicación del Sprint 2 completo se prepara en una rama nueva `sprint-2/analisis-2023-2024-dashboard`, mediante PR hacia `BraulioJmz/CalidadAireJalisco:main`, sin merge ni despliegue manual.

En futuros cambios autorizados, agregar cada ruta y su registro en `web/lib/site.ts` sin sobrescribir las páginas históricas. Una vista previa y un pull request pueden servir para revisión cuando se soliciten; no acreditan entrega académica ni publicación. El estado técnico interno del registro y la etiqueta pública de una ficha tienen funciones distintas: una descripción neutral no marca la entrega como realizada.

Conservar el enlace del [repositorio](https://github.com/BraulioJmz/CalidadAireJalisco). Añadir un enlace al PDF del Sprint 2 solo cuando exista el archivo definitivo y se compruebe su descarga. La participación individual y las reflexiones del equipo se documentan fuera del dashboard.

## Alcance de los informes y paquetes históricos

Los informes, capturas y ZIP de la revisión 02 acreditan los archivos identificados por sus hashes en esa fecha. No se reescriben como resultado de una edición posterior de contenido. Para una nueva entrega empaquetada deben repetirse los verificadores y producirse un artefacto con su propia huella. La revisión pública del 23 de octubre de 2026 se documenta por separado.
