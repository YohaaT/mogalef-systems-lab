PHASE: 4
OBJECTIVE: Ejecutar un rerun causal ligero de la `first minimal combined strategy candidate` y registrar día/hora de entradas y salidas para análisis horario.
SCOPE: Solo `MNQ 5m`, solo esta estrategia, sin abrir otros sistemas, sin descargar datos nuevos.
INPUTS: `mgf-control/backtest_causal_wrapper_design.md`, `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`, `EL_Mogalef_Trend_Filter_V2`, `EL_STPMT_DIV`.
EXPECTED ARTIFACT: `mgf-control/backtest_first_minimal_strategy_causal.md` y trade log horario.
STOP CONDITION: detenerse al dejar el rerun causal documentado.

# Backtest first minimal strategy causal

## 1. Qué se hizo en este rerun
Se ejecutó un wrapper causal ligero para eliminar la contaminación principal del backtest anterior.

### Convención temporal usada
- señal en barra cerrada `t`
- entrada en apertura de `t+1`
- una sola posición a la vez
- salida por stop causal simple o por señal opuesta

## 2. Componentes usados en este rerun causal
- filtro de régimen: `EL_Mogalef_Trend_Filter_V2`
- disparo de entrada: `EL_STPMT_DIV`

## 3. Componentes excluidos del motor causal final de este rerun
- `EL_MOGALEF_Bands`
- `EL_Stop_Intelligent`

### Motivo
Quedaron excluidos del motor de ejecución de este rerun porque la auditoría previa los señaló como retrospectivos/no causales en su forma actual de uso estratégico.

## 4. Gestión de riesgo usada en este rerun
Stop causal simplificado:
- en largos: stop inicial = mínimo de la barra de señal
- en cortos: stop inicial = máximo de la barra de señal
- salida también por señal opuesta válida

## 5. Qué hace realmente la estrategia en esta versión causal
Esta versión causal ya no intenta validar toda la estrategia completa final, sino una hipótesis ejecutable limpia:
- entrar cuando `STPMT_DIV` da señal y `Trend Filter V2` permite operar;
- salir si salta el stop causal simple o si aparece señal contraria válida.

## 6. Métricas principales del rerun causal
- trades: `97`
- ganadores: `17`
- perdedores: `80`
- net points: `1369.5`
- promedio por trade: `14.1186`

## 7. Lectura del resultado
Estas métricas son mucho más plausibles que las del run contaminado anterior.
Eso refuerza la hipótesis de que el problema real estaba en el uso no causal de `Bands` y `Stop Intelligent`.

## 8. Registro horario incorporado
Se generó un trade log con:
- día de la semana de entrada
- hora UTC de entrada
- día de la semana de salida
- hora UTC de salida
- razón de salida
- pnl por trade
- duración en barras

Archivo generado:
- `mgf-control/backtest_first_minimal_strategy_trade_log.csv`

## 9. Franjas observadas en esta muestra
### Horas con mejor neto observado
- `13 UTC`: `+549.0`
- `14 UTC`: `+396.0`
- `21 UTC`: `+329.75`
- `18 UTC`: `+275.0`
- `22 UTC`: `+264.25`

### Días con mejor neto observado
- `Thursday`: `+591.75`
- `Wednesday`: `+387.25`
- `Friday`: `+222.0`
- `Tuesday`: `+176.25`

## 10. Limitación importante
Esto sigue siendo un backtest ligero sobre un dataset corto y reciente.
Los patrones horarios observados son útiles para exploración, no para concluir robustez definitiva.

Result:
Artifacts created:
- `mgf-control/backtest_first_minimal_strategy_causal.md`
- `mgf-control/backtest_first_minimal_strategy_trade_log.csv`
Files read:
- `mgf-control/backtest_causal_wrapper_design.md`
- `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
Scope respected: yes
Next recommended action: usar el trade log para análisis horario más fino y, si interesa, reintroducir versiones causales de `Bands` y `Stop Intelligent` más adelante.
