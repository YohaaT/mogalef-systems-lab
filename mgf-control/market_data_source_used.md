PHASE: control
OBJECTIVE: Documentar la fuente realmente usada para adquirir un dataset intradía reproducible de `MNQ 5m` en este entorno.
SCOPE: Solo la fuente usada para este dataset práctico. Sin afirmar cobertura histórica definitiva.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, descarga efectiva realizada en este run.
EXPECTED ARTIFACT: `mgf-control/market_data_source_used.md`.
STOP CONDITION: detenerse al dejar la fuente documentada.

# Market data source used

## Fuente usada
- proveedor efectivo: `Yahoo Finance chart API`
- símbolo consultado en origen: `MNQ=F`
- intervalo efectivo obtenido: `5m`
- parámetro de rango efectivo usado: `60d`
- endpoint usado: `https://query1.finance.yahoo.com/v8/finance/chart/MNQ=F?range=60d&interval=5m&includePrePost=false`

## Motivo de uso
Esta fue la fuente viable y realmente accesible desde este entorno para obtener un dataset intradía reproducible de `MNQ`.

## Límite real detectado
La fuente no entregó `MNQ 10m 2023-2024` en este entorno.
La fuente sí entregó `MNQ 5m` con una ventana reciente limitada.

## Cobertura real obtenida en este run
- primer timestamp útil: `2026-02-03T05:05:00Z`
- último timestamp útil: `2026-04-15T19:56:20Z`
- total de filas válidas: `13725`

## Nota de interpretación
Este dataset queda autorizado como base práctica para:
- pruebas
- smoke tests
- validación funcional
- backtests ligeros

No debe interpretarse como sustituto automático de una validación futura más robusta si luego hiciera falta una cobertura histórica más amplia o una fuente de mayor calidad.

## Posible uso derivado
El dataset `5m` puede agregarse localmente a `10m` si más adelante hiciera falta para pruebas equivalentes, pero eso no fue requisito obligatorio en este run.

Result:
Artifacts created:
- `mgf-control/market_data_source_used.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- datos efectivamente descargados en este run
Scope respected: yes
Next recommended action: validar y dejar nota de alcance práctico del dataset obtenido.
