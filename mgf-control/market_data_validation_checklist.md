PHASE: control
OBJECTIVE: Dejar una única estrategia mínima de validación del primer dataset local de mercado.
SCOPE: Checklist de validación únicamente. Sin validación ejecutada todavía.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/market_data_requirements.md`, `mgf-control/market_data_download_unit.md`.
EXPECTED ARTIFACT: `mgf-control/market_data_validation_checklist.md`.
STOP CONDITION: detenerse al dejar checklist persistido.

# Market data validation checklist

## Dataset objetivo
- instrumento: `MNQ`
- timeframe: `10m`
- sesión: `regular_session`
- rango esperado: `2023-01-01` a `2024-12-31`
- ruta esperada: `mgf-data/market/MNQ__10m__regular_session__2023-01-01__2024-12-31.csv`

## Validaciones mínimas antes de usar el dataset
### A. Presencia y estructura
- [ ] el archivo existe en la ruta esperada
- [ ] el archivo es legible como CSV
- [ ] existen las columnas mínimas: `timestamp_utc`, `symbol`, `open`, `high`, `low`, `close`, `volume`
- [ ] todas las filas tienen `symbol = MNQ`
- [ ] todas las filas tienen `bar_interval = 10m` si esa columna existe

### B. Integridad temporal
- [ ] `timestamp_utc` está en orden cronológico ascendente
- [ ] no hay timestamps duplicados
- [ ] los timestamps están en UTC o fueron normalizados a UTC de forma documentada
- [ ] el rango cubre efectivamente desde `2023-01-01` hasta `2024-12-31` o la cobertura real queda documentada

### C. Integridad OHLCV
- [ ] `open`, `high`, `low`, `close` son numéricos y no nulos
- [ ] `volume` existe y es numérico
- [ ] `high >= open`, `high >= close`, `high >= low`
- [ ] `low <= open`, `low <= close`, `low <= high`

### D. Sesión
- [ ] el dataset respeta una sola política de sesión
- [ ] las barras fuera de la sesión principal fueron excluidas o documentadas explícitamente
- [ ] la definición de `regular_session` quedó escrita junto al dataset o en su manifest

### E. Metadata mínima
- [ ] existe manifest o nota del dataset
- [ ] la nota declara símbolo, fuente, timeframe, rango temporal, timezone, sesión y filas totales
- [ ] existe hash o checksum del archivo final

## Criterio de pase
El dataset queda apto para backtest solo si todas las casillas anteriores pueden marcarse como cumplidas o si cualquier excepción queda documentada sin afectar reproducibilidad.

Result:
Artifacts created:
- `mgf-control/market_data_validation_checklist.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-control/market_data_requirements.md`
- `mgf-control/market_data_download_unit.md`
Scope respected: yes
Next recommended action: esperar autorización explícita para ejecutar la unidad de adquisición real y luego correr esta validación.
