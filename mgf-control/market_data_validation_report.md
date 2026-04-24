PHASE: control
OBJECTIVE: Adquirir, guardar, normalizar y validar un dataset reproducible de `MNQ 5m` para pruebas, smoke tests, validación funcional y backtests ligeros.
SCOPE: Solo `MNQ`, solo `5m`, solo CSV local reproducible, sin abrir `Fase 4`, sin backtest todavía, sin otros instrumentos ni otros timeframes.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/phase_state.json`, descarga efectiva desde la fuente viable en este entorno.
EXPECTED ARTIFACT: CSV local y `mgf-control/market_data_validation_report.md`.
STOP CONDITION: detenerse al dejar el dataset validado o reportar fallo honesto.

# Market data validation report

## Resultado general
- Estado: `PASS_WITH_SCOPE_LIMIT`
- CSV creado: `sí`
- Validación estructural aprobada: `sí`

## Dataset obtenido
- instrumento: `MNQ`
- timeframe: `5m`
- ruta: `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
- primer timestamp útil: `2026-02-03T05:05:00Z`
- último timestamp útil: `2026-04-15T19:56:20Z`
- filas válidas: `13725`
- checksum sha256: `b85458a70daf97ff3bd70f776ec16b0aec69190ccf7c1dd078f895c2b82b6b8e`

## Fuente usada
- `Yahoo Finance chart API`
- símbolo en origen: `MNQ=F`
- intervalo solicitado y obtenido: `5m`
- límite real observado: ventana intradía reciente de aproximadamente `60d`

## Validaciones ejecutadas
- archivo CSV creado y legible
- columnas mínimas presentes: `timestamp_utc`, `symbol`, `open`, `high`, `low`, `close`, `volume`
- todas las filas con `symbol = MNQ`
- todas las filas con `bar_interval = 5m`
- timestamps en orden ascendente
- sin timestamps duplicados
- OHLC coherente
- volumen presente como valor numérico

## Límite exacto documentado
Este dataset no cubre `2023-2024`.
La fuente viable en este entorno solo permitió obtener una ventana intradía reciente, y ese límite debe considerarse parte del resultado honesto del run.

## Uso permitido dentro del alcance autorizado
El dataset queda apto para:
- pruebas
- smoke tests
- validación funcional
- backtests ligeros

## Reserva explícita
No debe afirmarse que este dataset sustituye una validación histórica más robusta futura si luego hiciera falta.

## Nota técnica opcional
El dataset `5m` puede agregarse localmente a `10m` para pruebas equivalentes si más adelante se decide, pero eso no fue requisito obligatorio de este run.

Result:
Artifacts created:
- `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
- `mgf-control/market_data_validation_report.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-control/phase_state.json`
- datos descargados desde Yahoo Finance chart API en este run
Scope respected: yes
Next recommended action: usar este dataset como base práctica para pruebas, smoke tests y backtests ligeros, manteniendo cerrada la validación definitiva.
