# cepa-cro-automatizaciones

Scripts de los reportes comerciales que generan las tareas programadas de Claude a partir de Pipedrive.
El repo es público y **no contiene datos de CEPA**: nombres, mails, IDs de Pipedrive y filtros viven en el
`config.json` que cada tarea escribe desde su propio prompt.

## Cómo lo usa una tarea programada

1. Clona una versión fija: `git clone --depth 1 --branch v1.0 https://github.com/despiga/cepa-cro-automatizaciones repo`
2. Escribe `config.json` con la configuración de su base (va en el prompt de la tarea).
3. Trae los datos de Pipedrive con el conector y los guarda como JSON.
4. Lee las cotizaciones del día desde la planilla de Google y escribe `fx.json`.
5. Corre el script, verifica la salida con `scripts/verificar.py` y publica.

Si un script falla, la tarea **no lo modifica**: no publica y avisa el error.

## Scripts

| Script | Qué genera | Argumentos |
|---|---|---|
| `scripts/dashboard_equipo.py` | Dashboard de una base con varios vendedores | `config.json ABIERTOS GANADOS PERDIDOS HECHAS PENDIENTES salida.html AAAA-MM-DD [fx.json]` |
| `scripts/dashboard_vendedor.py` | Dashboard de una base con un vendedor y leads etiquetados | `config.json DEALS HECHAS PENDIENTES LEADS salida.html AAAA-MM-DD [fx.json]` |
| `scripts/plan_vendedor.py` | Plan semanal de un vendedor | `config.json DEALS PENDIENTES HECHAS LEADS ORGS salida.html AAAA-MM-DD` |
| `scripts/briefing_template.py` | Plantilla HTML fija del briefing diario por mail | `from briefing_template import render` |
| `scripts/verificar.py` | Control de calidad del HTML (sin None/NaN/undefined) | `salida.html` |

Cada argumento de datos acepta una ruta o varias separadas por coma (páginas de Pipedrive).

### fx.json

```json
{"COP": {"valor": 3301.43, "fecha": "2026-11-17", "fuente": "Google", "respaldo": false}}
```

Las monedas que no estén en `fx.json` usan el valor de `fx_respaldo` del config, y el pie del reporte lo indica.

## Probar antes de publicar una versión nueva

```bash
bash tests/probar.sh 2026-11-17
```

Genera datos ficticios, corre todos los scripts y verifica la salida. Una versión nueva se publica con un tag
(`v1.1`, `v1.2`…) y se cambia el tag en el prompt de cada tarea solo después de que la prueba pase.
