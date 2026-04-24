PHASE: control
OBJECTIVE: Preparar la primera estrategia mínima combinada para futuro backtest, sin abrir `Fase 4`.
SCOPE: Definición operativa mínima y gate de aprobación. Sin código nuevo de estrategia, sin smoke de combinación, sin backtest.
INPUTS: `PROJECT_MASTER.md`, `TOKEN_POLICY.md`, `RUN_PROTOCOL.md`, `mgf-control/phase_state.json`, `mgf-control/approval_queue.md`, `mgf-control/approval_request.md`, `mgf-control/session_checkpoint.md`, `mgf-control/night_run_summary.md`, `mgf-control/workflow_operating_mode.md`, QA/reportes existentes de `EL_MOGALEF_Bands`, `EL_Mogalef_Trend_Filter_V2`, `EL_Stop_Intelligent`, `EL_STPMT_DIV`, `EL_REPULSE_DIV`.
EXPECTED ARTIFACT: `mgf-control/first_minimal_strategy_candidate.md` y gate de aprobación preparado.
STOP CONDITION: detenerse al dejar la propuesta y el gate listos, sin abrir `Fase 4`.

# First minimal strategy candidate

## 1. Componentes elegidos
- `EL_MOGALEF_Bands`
- `EL_Mogalef_Trend_Filter_V2`
- `EL_Stop_Intelligent`
- entrada candidata principal: `EL_STPMT_DIV`
- entrada candidata alternativa para iteración posterior: `EL_REPULSE_DIV`

## 2. Rol de cada componente
- `EL_MOGALEF_Bands`: estructura base del canal Mogalef y contexto de bandas para no entrar completamente fuera del marco estructural.
- `EL_Mogalef_Trend_Filter_V2`: filtro de régimen y dirección. Su función es permitir solo entradas alineadas con el sesgo permitido por el filtro.
- `EL_Stop_Intelligent`: gestión de salida/riesgo primaria. Debe aportar el stop funcional inicial y su actualización posterior.
- `EL_STPMT_DIV` o `EL_REPULSE_DIV`: motor de entrada. Solo uno debe usarse en la primera variante mínima para no mezclar señales demasiado pronto.

## 3. Recomendación de variante de entrada inicial
Recomiendo abrir primero la variante con `EL_STPMT_DIV`.

### Motivo
- la semántica de señal quedó más acotada en los artefactos de fix, re-QA y smoke;
- sus casos críticos dirigidos (`smooth=1`, divergencia alcista y bajista normal) ya quedaron probados explícitamente;
- `EL_REPULSE_DIV` también está en `PASS`, pero introduce más complejidad de horizontes (`R1`, `R2`, `R3`) y prioridad secuencial interna, por lo que es mejor como segunda variante controlada.

## 4. Reglas mínimas de entrada
### Variante recomendada: Bands + Trend Filter + STPMT_DIV + Stop Intelligent

#### Entrada larga
Abrir largo solo si se cumplen simultáneamente estas condiciones en barra cerrada:
1. `EL_Mogalef_Trend_Filter_V2` permite sesgo alcista o estado compatible con largos.
2. `EL_STPMT_DIV` emite señal de compra (`pose = 1` o `sentiment = 100`).
3. El precio no está en ruptura grotesca fuera del contexto de `EL_MOGALEF_Bands`; como versión mínima, exigir que el cierre esté dentro de banda o no excesivamente extendido respecto a la banda superior en la barra de señal.
4. Existe valor funcional válido en `EL_Stop_Intelligent` para gestionar la posición desde la entrada.

#### Entrada corta
Abrir corto solo si se cumplen simultáneamente estas condiciones en barra cerrada:
1. `EL_Mogalef_Trend_Filter_V2` permite sesgo bajista o estado compatible con cortos.
2. `EL_STPMT_DIV` emite señal de venta (`pose = -1` o `sentiment = 0`).
3. El precio no está en ruptura grotesca fuera del contexto de `EL_MOGALEF_Bands`; como versión mínima, exigir que el cierre esté dentro de banda o no excesivamente extendido respecto a la banda inferior en la barra de señal.
4. Existe valor funcional válido en `EL_Stop_Intelligent` para gestionar la posición desde la entrada.

## 5. Filtro / contexto
Filtro principal: `EL_Mogalef_Trend_Filter_V2`.

Contexto estructural adicional: `EL_MOGALEF_Bands`.

Uso mínimo recomendado del contexto de bandas:
- no usar todavía lógica compleja multi-canal;
- usarlo como filtro de plausibilidad estructural para evitar entrar en barras ya demasiado extendidas fuera del canal;
- no convertir bandas en segundo motor de señal, solo en contexto.

## 6. Salida / riesgo
Salida principal:
- `EL_Stop_Intelligent` como stop operativo base.

Regla mínima propuesta:
- la posición permanece abierta mientras no salte el stop;
- no añadir todavía target fijo ni pyramiding;
- no añadir todavía money management complejo;
- no usar todavía combinación de varios stops.

## 7. Supuestos y límites
- Esta propuesta es deliberadamente mínima y testeable.
- No busca edge final, solo una primera hipótesis combinada limpia.
- No mezcla las dos entradas a la vez.
- No añade sizing avanzado.
- No añade filtros horarios, calendario ni overlays extra.
- No convierte `Bands` en trigger primario de entrada.
- Asume que los componentes individuales en `PASS` son suficientemente estables para servir como bloque base de una propuesta de combinación, pero eso no sustituye el backtest.

## 8. Variante secundaria a preparar después
Segunda variante natural:
- `EL_MOGALEF_Bands`
- `EL_Mogalef_Trend_Filter_V2`
- `EL_Stop_Intelligent`
- entrada: `EL_REPULSE_DIV`

Esta variante debe compararse después contra la primera, no mezclarse con ella en el primer intento.

## 9. Qué faltaría para abrir `Fase 4` con sentido
Antes de abrir `Fase 4` con sentido todavía faltaría:
1. aprobación explícita del usuario para combinación/backtest;
2. fijar la definición exacta operativa de “dentro de banda / no excesivamente extendido” para la estrategia mínima;
3. definir con precisión la convención de entrada en barra cerrada y ejecución de orden para evitar ambigüedad temporal;
4. dejar por escrito si la estrategia permitirá solo una posición a la vez;
5. decidir si la primera prueba de backtest será solo con `EL_STPMT_DIV` o si también se autoriza una segunda corrida separada con `EL_REPULSE_DIV`.

## 10. Recomendación concreta
Primera combinación mínima recomendada para futuro backtest:
- estructura: `EL_MOGALEF_Bands`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- entrada: `EL_STPMT_DIV`
- salida/riesgo: `EL_Stop_Intelligent`

Y dejar `EL_REPULSE_DIV` como segunda variante inmediata, comparable pero separada.

Result:
Artifacts created:
- `mgf-control/first_minimal_strategy_candidate.md`
Files read:
- `PROJECT_MASTER.md`
- `TOKEN_POLICY.md`
- `RUN_PROTOCOL.md`
- `mgf-control/phase_state.json`
- `mgf-control/approval_queue.md`
- `mgf-control/approval_request.md`
- `mgf-control/session_checkpoint.md`
- `mgf-control/night_run_summary.md`
- `mgf-control/workflow_operating_mode.md`
- QA/reportes existentes de los componentes base y entradas
Scope respected: yes
Next recommended action: esperar aprobación explícita para abrir trabajo de `Fase 4` sobre esta combinación mínima.
