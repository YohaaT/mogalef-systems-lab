PHASE: exploratory_control
OBJECTIVE: Comparar `COMB_001` base frente a `COMB_001 Candidate A` usando exactamente el mismo dataset práctico.
SCOPE: Solo comparación base vs Candidate A. Sin nuevas combinaciones, sin Fase 4 definitiva.
INPUTS: `mgf-control/strategy_candidate_COMB_001_rules.md`, `mgf-control/COMB_001_candidate_A_rules.md`, dataset `MNQ 5m` ya validado.
EXPECTED ARTIFACT: `mgf-control/COMB_001_candidate_A_comparison.md`.
STOP CONDITION: detenerse al dejar la comparación persistida.

# COMB_001 Candidate A comparison

## 1. Qué cambia y qué no cambia
### Se mantiene igual
- entrada: `EL_STPMT_DIV`
- filtro: `EL_Mogalef_Trend_Filter_V2`
- dataset
- instrumento
- timeframe
- convención temporal
- una sola posición a la vez

### Lo único que cambia
- la salida/riesgo

#### COMB_001 base
- stop inicial simple fijado en extremo de la barra de señal
- salida por stop o señal opuesta válida

#### COMB_001 Candidate A
- misma lógica base
- más una regla adicional: mover el stop a break-even tras `1R` favorable

## 2. Resultado orientativo de COMB_001 base
- trades: `97`
- wins: `17`
- losses: `80`
- flats: `0`
- net points: `1369.5`
- avg points: `14.1186`

## 3. Resultado orientativo de COMB_001 Candidate A
- trades: `110`
- wins: `9`
- losses: `42`
- flats: `59`
- net points: `-116.25`
- avg points: `-1.0568`

## 4. Lectura comparativa breve
`Candidate A` convirtió muchos trades en salidas neutras (`break-even`) y redujo fuertemente la capacidad de la rama para retener avance útil en esta muestra.

Eso produjo:
- más trades cerrados sin ganancia/pérdida (`59` flats)
- menos trades ganadores netos efectivos
- deterioro claro del neto frente a la base

## 5. Dictamen final
- Dictamen: `keep_base`

## 6. Motivo del dictamen
La mejora mínima propuesta era razonable como hipótesis, pero en esta muestra degrada el comportamiento orientativo de la rama principal.

Por tanto:
- `COMB_001` base se mantiene como versión principal vigente
- `Candidate A` no pasa a ser la nueva base

## 7. Qué queda pendiente después
- si se quiere seguir iterando `COMB_001`, el siguiente cambio debería ser distinto de este break-even a `1R`
- conviene buscar una mejora igual de simple pero menos destructiva para el flujo del trade

Result:
Artifacts created:
- `mgf-control/COMB_001_candidate_A_comparison.md`
Files read:
- `mgf-control/strategy_candidate_COMB_001_rules.md`
- `mgf-control/COMB_001_candidate_A_rules.md`
- dataset `MNQ 5m` ya validado
Scope respected: yes
Next recommended action: mantener `COMB_001` base y preparar un siguiente candidato distinto si se autoriza.
