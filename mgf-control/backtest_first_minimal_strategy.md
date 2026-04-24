PHASE: 4
OBJECTIVE: Ejecutar un backtest ligero y validación funcional de la `first minimal combined strategy candidate` usando únicamente el dataset práctico `MNQ 5m` ya validado.
SCOPE: Solo esta estrategia mínima combinada, solo este dataset `5m`, sin abrir otros sistemas, sin descargar más datos, sin presentar el resultado como validación histórica definitiva.
INPUTS: `mgf-control/first_minimal_strategy_candidate.md`, `mgf-bands-lab/src/EL_MOGALEF_Bands.py`, `mgf-regime-filter-lab/src/EL_Mogalef_Trend_Filter_V2.py`, `mgf-stop-lab/src/EL_Stop_Intelligent.py`, `mgf-divergence-lab/src/EL_STPMT_DIV.py`, `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`.
EXPECTED ARTIFACT: `mgf-control/backtest_first_minimal_strategy.md`.
STOP CONDITION: detenerse al dejar el backtest ligero documentado y dictaminado.

# Backtest first minimal strategy

## 1. Estrategia exacta usada
Primera variante mínima combinada:
- estructura/contexto: `EL_MOGALEF_Bands`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- entrada: `EL_STPMT_DIV`
- salida/riesgo: `EL_Stop_Intelligent`

## 2. Dataset usado
- archivo: `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
- instrumento: `MNQ`
- timeframe: `5m`
- cobertura real: `2026-02-03T05:05:00Z` -> `2026-04-15T19:56:20Z`
- filas: `13725`
- naturaleza del dataset: base práctica reciente, no validación histórica definitiva

## 3. Reglas de entrada usadas
### Entrada larga
Abrir largo cuando en barra disponible se cumplía simultáneamente:
1. `EL_Mogalef_Trend_Filter_V2` con `sentiment = pass`.
2. `EL_STPMT_DIV` con `pose = 1`.
3. cierre dentro del canal disponible de `EL_MOGALEF_Bands` (`mog_b <= close <= mog_h`).
4. existencia de stop funcional calculable por `EL_Stop_Intelligent`.

### Entrada corta
Abrir corto cuando en barra disponible se cumplía simultáneamente:
1. `EL_Mogalef_Trend_Filter_V2` con `sentiment = pass`.
2. `EL_STPMT_DIV` con `pose = -1`.
3. cierre dentro del canal disponible de `EL_MOGALEF_Bands` (`mog_b <= close <= mog_h`).
4. existencia de stop funcional calculable por `EL_Stop_Intelligent`.

## 4. Reglas de salida usadas
- salida principal por `EL_Stop_Intelligent`.
- si no salta el stop antes del final del dataset, cierre forzado en la última barra disponible.
- una sola posición a la vez.
- sin target fijo.
- sin pyramiding.
- sin sizing avanzado.

## 5. Métricas observadas del run
- barras procesadas: `13725`
- trades: `116`
- ganadores: `109`
- perdedores: `7`
- win rate: `93.97%`
- net points: `152920.6`
- promedio por trade: `1318.2810`
- profit factor: `90.5176`
- mejor trade: `2293.45`
- peor trade: `-576.375`

Primer trade observado:
- lado: `short`
- entrada: `2026-02-06T02:40:00Z`
- salida: `2026-02-06T02:45:00Z`
- pnl puntos: `1449.95`

Último trade observado:
- lado: `short`
- entrada: `2026-04-15T15:55:00Z`
- salida: `2026-04-15T19:56:20Z`
- pnl puntos: `-161.5`

## 6. Limitaciones críticas detectadas
Las métricas resultantes son demasiado buenas para considerarlas creíbles como validación funcional limpia.

Sospechas técnicas principales:
- posible sesgo de lookahead derivado de cómo algunos componentes reconstruidos usan recorridos retrospectivos o estados calculados con información futura en su forma actual de integración de estrategia;
- posible ambigüedad temporal entre barra de señal, barra de ejecución y barra de stop;
- el stop se recalculó sobre una serie `market_position` simplificada, útil para prueba técnica pero no todavía validada como motor de ejecución fiel barra a barra;
- el dataset es corto y reciente, por lo que aunque las métricas fueran limpias no sería una validación histórica definitiva.

## 7. Dictamen final
- Dictamen: `FIX`

### Motivo del dictamen
El run sí sirve para una primera validación funcional ligera de integración, porque demuestra que:
- la combinación corre sobre el dataset práctico;
- los componentes pueden conectarse sin romper el pipeline;
- se generan trades y salidas.

Pero el resultado no es confiable todavía como backtest ligero interpretable por la magnitud anómala de las métricas y la sospecha real de sesgo temporal/lookahead.

Antes de aceptar una lectura seria del resultado hace falta:
1. fijar una convención temporal estricta de señal -> entrada -> stop;
2. revisar la integración barra a barra para eliminar cualquier uso inadvertido de información futura;
3. rerun del mismo backtest con esa corrección metodológica.

Result:
Artifacts created:
- `mgf-control/backtest_first_minimal_strategy.md`
Files read:
- `mgf-control/first_minimal_strategy_candidate.md`
- `mgf-bands-lab/src/EL_MOGALEF_Bands.py`
- `mgf-regime-filter-lab/src/EL_Mogalef_Trend_Filter_V2.py`
- `mgf-stop-lab/src/EL_Stop_Intelligent.py`
- `mgf-divergence-lab/src/EL_STPMT_DIV.py`
- `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
Scope respected: yes
Next recommended action: corregir la metodología temporal del backtest antes de tratar esta estrategia como resultado interpretable.
