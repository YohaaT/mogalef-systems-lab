PHASE: exploratory_control
OBJECTIVE: Dejar las reglas operativas mínimas y claras de `COMB_001`.
SCOPE: Solo reglas operativas de la rama principal. Sin nuevas combinaciones, sin Fase 4.
INPUTS: `mgf-control/strategy_candidate_COMB_001.md`.
EXPECTED ARTIFACT: `mgf-control/strategy_candidate_COMB_001_rules.md`.
STOP CONDITION: detenerse al dejar reglas persistidas.

# Strategy candidate COMB_001 rules

## COMB_001
- entrada: `EL_STPMT_DIV`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- salida/riesgo: stop causal simple

## 1. Regla mínima de entrada larga
Abrir largo solo si en barra cerrada `t`:
1. `EL_STPMT_DIV` emite señal long (`pose = 1`)
2. `EL_Mogalef_Trend_Filter_V2` está en estado permitido (`sentiment = pass`)
3. no existe ya una posición abierta

Ejecución:
- entrar en apertura de la barra `t+1`

## 2. Regla mínima de entrada corta
Abrir corto solo si en barra cerrada `t`:
1. `EL_STPMT_DIV` emite señal short (`pose = -1`)
2. `EL_Mogalef_Trend_Filter_V2` está en estado permitido (`sentiment = pass`)
3. no existe ya una posición abierta

Ejecución:
- entrar en apertura de la barra `t+1`

## 3. Regla mínima de stop causal simple
### Si la entrada es larga
- stop inicial = mínimo de la barra de señal

### Si la entrada es corta
- stop inicial = máximo de la barra de señal

## 4. Regla mínima de salida
Cerrar la posición si ocurre cualquiera de estas condiciones:
1. el precio toca el stop causal simple
2. aparece una señal opuesta válida y el filtro sigue permitiendo operar
3. se llega al final del dataset usado en el run

## 5. Gestión de posición
- una sola posición a la vez
- sin pyramiding
- sin target fijo obligatorio
- sin trailing complejo por ahora
- sin money management avanzado en esta etapa

## 6. Orden temporal exacto
1. calcular señal y filtro en barra cerrada `t`
2. decidir si existe setup válido
3. ejecutar entrada en apertura de `t+1`
4. aplicar stop y salida solo desde la posición viva en adelante

## 7. Supuesto metodológico actual
Estas reglas se mantienen deliberadamente simples para conservar trazabilidad y comparabilidad dentro de la rama STPMT.

## 8. Advertencia
Estas reglas definen una estrategia candidata principal reusable para próximas iteraciones, pero no constituyen todavía una validación definitiva del sistema.

Result:
Artifacts created:
- `mgf-control/strategy_candidate_COMB_001_rules.md`
Files read:
- `mgf-control/strategy_candidate_COMB_001.md`
Scope respected: yes
Next recommended action: usar estas reglas como contrato operativo base de la rama principal `COMB_001`.
