PHASE: 4
OBJECTIVE: Añadir lectura de `R:R` al backtest causal y probar la reintroducción conservadora sugerida de `EL_MOGALEF_Bands`.
SCOPE: Solo dataset `MNQ 5m`, solo backtest causal ligero, sin descargar datos nuevos.
INPUTS: `mgf-control/backtest_first_minimal_strategy_causal.md`, `mgf-control/backtest_causal_wrapper_design.md`, `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`.
EXPECTED ARTIFACT: `mgf-control/backtest_rr_and_reintroduction_note.md`.
STOP CONDITION: detenerse al dejar la nota persistida.

# Backtest R:R and reintroduction note

## 1. R:R del backtest causal
Se recalculó el trade log añadiendo:
- `initial_stop`
- `risk_points`
- `rr_multiple`

Archivo generado:
- `mgf-control/backtest_first_minimal_strategy_trade_log_rr.csv`

### Métricas R:R observadas
- trades: `97`
- net points: `1369.5`
- R:R medio: `1.3025`
- R:R mediano: `-1.0`
- mejor R:R observado: `47.81`
- peor R:R observado: `-1.0`

## 2. Lectura correcta del R:R
- que el R:R medio sea positivo es buena señal exploratoria;
- que la mediana sea `-1.0` indica que la mayoría de trades pierden 1R o cerca de eso;
- el resultado agregado depende de unas pocas ganancias grandes, lo que es compatible con una estrategia de baja tasa de acierto limpia o con una muestra todavía insuficiente/ruidosa.

## 3. Reintroducción sugerida ejecutada
Se probó una reintroducción conservadora de `EL_MOGALEF_Bands` como filtro amplio de contención, con warmup adicional.

### Resultado
La reintroducción no cambió las métricas del rerun causal:
- trades: `97`
- wins: `17`
- losses: `80`
- net points: `1369.5`

## 4. Interpretación
Eso sugiere una de estas dos cosas:
1. el filtro `Bands` así reintroducido no está aportando información discriminante útil en esta muestra; o
2. su salida sigue sin ser apropiada todavía para filtrado causal fino de estrategia.

## 5. Conclusión operativa
- el `R:R` ya queda incorporado al análisis del backtest causal;
- la primera reintroducción conservadora de `Bands` no añade valor observable en esta muestra;
- el siguiente candidato natural a reintroducción seria sería un wrapper causal mejor definido para `Stop Intelligent`, pero solo si se implementa de forma estrictamente secuencial.

Result:
Artifacts created:
- `mgf-control/backtest_rr_and_reintroduction_note.md`
- `mgf-control/backtest_first_minimal_strategy_trade_log_rr.csv`
Files read:
- `mgf-control/backtest_first_minimal_strategy_causal.md`
- `mgf-control/backtest_causal_wrapper_design.md`
- `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
Scope respected: yes
Next recommended action: explotar el trade log con R:R y, si se desea, diseñar una reintroducción causal estricta de `Stop Intelligent`.
