PHASE: control
OBJECTIVE: Definir la capa mínima de datos necesaria para habilitar backtests reproducibles de la `first minimal combined strategy candidate`, sin abrir `Fase 4`.
SCOPE: Especificación de datos únicamente. Sin descarga de datos, sin backtest, sin tocar otros componentes.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/phase_state.json`, `mgf-control/first_minimal_strategy_candidate.md`, `mgf-control/backtest_first_minimal_strategy.md`, `mgf-control/session_checkpoint.md`, `mgf-control/night_run_summary.md`.
EXPECTED ARTIFACT: `mgf-control/market_data_requirements.md`.
STOP CONDITION: detenerse al dejar especificación de datos completa y persistida.

# Market data requirements

## 1. Propósito
Definir la capa mínima de datos para poder ejecutar de forma reproducible el primer backtest de la estrategia mínima combinada:
- `EL_MOGALEF_Bands`
- `EL_Mogalef_Trend_Filter_V2`
- `EL_Stop_Intelligent`
- entrada: `EL_STPMT_DIV`

## 2. Universo inicial recomendado
Recomendación mínima inicial:
- un solo instrumento líquido por corrida inicial, para no mezclar efectos de universo.
- universo sugerido de arranque: **1 futuro líquido o 1 índice/ETF altamente líquido**, definido explícitamente antes de la carga.

Como especificación mínima, dejar preparado el sistema para un universo inicial de un solo símbolo con identificador estable:
- `symbol`
- `venue` o `exchange` si aplica
- `asset_class`
- `timezone`

## 3. Marco temporal inicial recomendado
Recomendación inicial:
- **barra fija intradía única**, preferiblemente `5m` o `15m`.

Elección operativa recomendada para el primer intento:
- `15m`

### Motivo
- reduce ruido frente a `1m` o `5m`;
- sigue siendo suficiente para una estrategia con filtro, estructura y entrada por divergencia;
- simplifica validación inicial de reproducibilidad.

## 4. Sesión / horario a usar
Debe quedar fijado por dataset y no inferirse ad hoc.

Recomendación mínima:
- usar una sola sesión clara por instrumento;
- almacenar timestamps en UTC;
- documentar la sesión operativa original asociada al instrumento.

Campos mínimos de sesión:
- `session_name`
- `session_start_local`
- `session_end_local`
- `timezone_local`
- política de barras fuera de sesión: `exclude`

Regla inicial recomendada:
- **excluir barras fuera de la sesión principal definida para el instrumento**, para evitar mezclar overnight si no se ha especificado otra política.

## 5. Columnas requeridas del dataset
Columnas mínimas obligatorias por fila:
- `timestamp_utc`
- `symbol`
- `open`
- `high`
- `low`
- `close`
- `volume`

Columnas recomendadas adicionales:
- `trade_count` si existe
- `vwap` si existe
- `session_name`
- `bar_interval`
- `source`
- `ingested_at_utc`

## 6. Reglas estructurales del dataset
- orden cronológico ascendente
- una fila por barra
- sin timestamps duplicados por `symbol` + `bar_interval`
- `high >= max(open, close, low)`
- `low <= min(open, close, high)`
- `open`, `high`, `low`, `close` numéricos y no nulos
- `timestamp_utc` normalizado en formato ISO 8601 o equivalente inequívoco

## 7. Formato de almacenamiento local
Formato recomendado mínimo:
- `csv` canónico para inspección simple
- opcionalmente `parquet` después, pero no como único formato en la primera capa mínima

Ruta recomendada:
- `mgf-data/market/`

## 8. Convención de nombres de archivos
Convención recomendada:
`<symbol>__<bar_interval>__<session_name>__<start_utc>__<end_utc>.csv`

Ejemplo:
`ES__15m__regular_session__2023-01-01__2024-12-31.csv`

Si el símbolo contiene caracteres problemáticos, normalizar a ASCII seguro y `_`.

## 9. Metadatos mínimos asociados
Cada dataset debe tener una nota o manifest mínimo que declare:
- símbolo
- fuente
- intervalo
- rango temporal
- timezone original
- timezone almacenada
- reglas de sesión aplicadas
- filas totales
- hash o checksum del archivo final

## 10. Criterios mínimos de calidad / validación
Antes de considerar el dataset apto para backtest, debe pasar como mínimo:
1. sin duplicados por timestamp y símbolo;
2. sin gaps inexplicados dentro de la sesión, o con gaps documentados;
3. OHLC consistente (`high`/`low` válidos);
4. timestamps monotónicos crecientes;
5. cobertura suficiente para un backtest inicial útil;
6. fuente y rango temporal documentados;
7. archivo persistido localmente dentro del proyecto.

## 11. Capa mínima necesaria para desbloquear `Fase 4`
Para desbloquear `Fase 4` de forma honesta faltan exactamente estos elementos:
1. dataset OHLC persistido localmente para el símbolo elegido;
2. definición explícita del símbolo inicial;
3. definición explícita del marco temporal inicial (`15m` recomendado);
4. definición explícita de la sesión/horario a usar;
5. validación básica del dataset con los criterios de calidad anteriores.

## 12. Recomendación concreta inicial
Recomiendo que la primera capa de datos se cierre así:
- universo inicial: **un solo símbolo líquido**
- marco temporal: **15m**
- sesión: **sesión principal del instrumento, excluyendo fuera de sesión**
- almacenamiento: **CSV canónico en `mgf-data/market/`**
- dataset con columnas OHLCV + metadata mínima documentada

Result:
Artifacts created:
- `mgf-control/market_data_requirements.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-control/phase_state.json`
- `mgf-control/first_minimal_strategy_candidate.md`
- `mgf-control/backtest_first_minimal_strategy.md`
- `mgf-control/session_checkpoint.md`
- `mgf-control/night_run_summary.md`
Scope respected: yes
Next recommended action: preparar el plan de adquisición/carga local de este dataset, sin descargar datos todavía si no está autorizado.
