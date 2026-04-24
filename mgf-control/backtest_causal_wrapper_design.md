PHASE: 4
OBJECTIVE: Diseñar un wrapper causal de backtest para la `first minimal combined strategy candidate` y dejar incorporada la captura de día/hora de ejecuciones y cierres.
SCOPE: Diseño metodológico únicamente. Sin cambiar arquitectura base de componentes en este documento.
INPUTS: `mgf-control/backtest_component_audit.md`, `mgf-control/backtest_first_minimal_strategy.md`, `mgf-control/backtest_fix_temporal_methodology.md`, `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`.
EXPECTED ARTIFACT: `mgf-control/backtest_causal_wrapper_design.md`.
STOP CONDITION: detenerse al dejar el diseño persistido.

# Backtest causal wrapper design

## 1. Objetivo
Construir un wrapper de backtest que use los componentes actuales de forma causal y auditable, sin tratar outputs retrospectivos como si fueran señales ejecutables ya limpias.

## 2. Principio general
Separar estrictamente cuatro capas:
1. cálculo de indicadores;
2. generación de señal en barra cerrada `t`;
3. ejecución en `t+1`;
4. gestión de posición y stop solo con información disponible hasta la barra viva actual.

## 3. Qué debe cambiar respecto al run actual
### A. `Bands`
No usar directamente el canal retrospectivo heredado como filtro de estrategia tal cual.

Wrapper propuesto:
- consumir solo valores ya consolidados hasta `t`;
- si el componente no puede garantizar causalidad, reemplazar temporalmente su uso por una versión de contexto más conservadora para estrategia;
- registrar explícitamente cuándo el filtro estructural queda `usable` y cuándo no.

### B. `Stop Intelligent`
No usar el stop reconstruido a partir de una trayectoria completa futura de `market_position`.

Wrapper propuesto:
- al abrir posición, iniciar un estado vivo de trade;
- recalcular/actualizar stop barra a barra solo desde historia ya conocida hasta esa barra;
- no permitir que el stop de hoy nazca con información de toda la operación futura.

### C. `STPMT_DIV`
Mantenerlo como disparo candidato, pero verificar que la señal usada corresponde a barra cerrada y no a una lectura que dependa de confirmación futura no explícita.

### D. `Trend Filter V2`
Mantenerlo como filtro de permiso, con menor sospecha actual, pero registrando también warmup y barras bloqueadas.

## 4. Registro obligatorio por trade
Para cada trade, guardar como mínimo:
- `trade_id`
- `side`
- `signal_bar_ts`
- `entry_bar_ts`
- `entry_day_of_week`
- `entry_hour_utc`
- `entry_price`
- `exit_bar_ts`
- `exit_day_of_week`
- `exit_hour_utc`
- `exit_price`
- `exit_reason`
- `pnl_points`
- `bars_in_trade`

## 5. Objetivo del registro horario
El usuario quiere medir mejores horarios y franjas más efectivas.

Por tanto, el wrapper debe permitir agregaciones como:
- rendimiento por hora de entrada;
- win rate por hora de entrada;
- rendimiento por día de la semana de entrada;
- rendimiento por hora de salida;
- duración media por franja horaria;
- conteo de trades por franja.

## 6. Reportes recomendados derivados
Cuando se ejecute el rerun causal, generar además:
- tabla por `entry_hour_utc`
- tabla por `entry_day_of_week`
- tabla por `exit_hour_utc`
- tabla de combinaciones `day x hour` si la muestra lo permite

## 7. Qué hará realmente la estrategia en ese wrapper
La estrategia seguirá siendo la misma en intención:
- señal de entrada por `STPMT_DIV`
- permiso por `Trend Filter V2`
- contexto estructural por `Bands`
- salida por `Stop Intelligent`

Pero la ejecución pasará a estar gobernada por un motor causal barra a barra que registra cuándo se entra y cuándo se sale con precisión temporal explotable.

## 8. Resultado esperado
Si este wrapper está bien hecho:
- bajará el riesgo de lookahead;
- el backtest será más honesto;
- quedará lista la capa para análisis horario de efectividad.

Result:
Artifacts created:
- `mgf-control/backtest_causal_wrapper_design.md`
Files read:
- `mgf-control/backtest_component_audit.md`
- `mgf-control/backtest_first_minimal_strategy.md`
- `mgf-control/backtest_fix_temporal_methodology.md`
- `mgf-data/market/MNQ__5m__regular_session__max_available_from_source.csv`
Scope respected: yes
Next recommended action: implementar el wrapper causal y persistir el trade log con día/hora de entradas y salidas.
