PHASE: exploratory_control
OBJECTIVE: Preparar la hoja de ruta de iteración controlada de `COMB_001` sin ejecutar todavía la siguiente iteración.
SCOPE: Solo planificación sobre la rama principal `COMB_001`. Sin nuevas combinaciones, sin Fase 4.
INPUTS: `mgf-control/strategy_candidate_COMB_001.md`, `mgf-control/strategy_candidate_COMB_001_rules.md`, `mgf-control/stpmt_branch_comparison.md`, `mgf-control/combination_registry.md`.
EXPECTED ARTIFACT: `mgf-control/COMB_001_iteration_plan.md`.
STOP CONDITION: detenerse al dejar el plan persistido.

# COMB_001 iteration plan

## 1. Estado actual de COMB_001
`COMB_001` es la rama principal vigente del proyecto.

Composición actual:
- `EL_STPMT_DIV`
- `EL_Mogalef_Trend_Filter_V2`
- stop causal simple

Estado operativo:
- suficientemente clara y reusable para próximas iteraciones
- limpia frente a las ramas contaminadas por componentes no causales
- seleccionada como mejor candidata provisional frente a `COMB_004` y `COMB_007`

## 2. Principales límites actuales
1. la salida sigue siendo demasiado simple;
2. el filtro de régimen es binario en esta versión y puede estar dejando pasar o bloqueando demasiado sin matiz;
3. todavía no hay una iteración de refinamiento focalizada solo dentro de la rama principal;
4. no se está buscando edge definitivo, así que la prioridad es mejorar claridad operativa y comparabilidad interna.

## 3. Estrategia de iteración recomendada
No abrir nuevas combinaciones todavía.
Primero refinar `COMB_001` con cambios mínimos, reversibles y fáciles de comparar contra la versión actual.

## 4. Candidatos de cambio mínimo
### Candidato A
**Ajustar la lógica de salida causal simple**

Idea:
- mantener la entrada igual;
- mantener el filtro igual;
- modificar solo la salida/riesgo con una variante causal igualmente simple pero algo mejor estructurada.

Ejemplos posibles:
- stop inicial igual, pero mover a break-even bajo condición simple y verificable;
- salida por tiempo máximo en trade;
- salida parcial no, todavía no.

### Candidato B
**Añadir una restricción mínima temporal/horaria dentro de COMB_001**

Idea:
- conservar exactamente la misma lógica base;
- permitir entradas solo en ciertas horas más razonables según el comportamiento observado;
- mantenerlo como una restricción simple y auditable.

### Candidato C
**Endurecer ligeramente la entrada STPMT sin añadir nuevos componentes**

Idea:
- seguir usando solo `STPMT_DIV + Trend_Filter_V2`;
- exigir una condición interna mínima adicional sobre la señal ya existente, sin traer otro filtro nuevo.

## 5. Recomendación principal
### Probar primero: Candidato A
**mejora mínima de la salida causal simple**

## 6. Por qué recomiendo el Candidato A primero
- toca una sola parte de la estrategia: la salida;
- preserva la identidad de `COMB_001`;
- no abre una nueva rama conceptual;
- permite comparación limpia contra la base actual;
- el mayor límite actual de la rama está precisamente en la crudeza de la salida.

## 7. Por qué esto es mejor que abrir nuevas combinaciones
- la rama principal ya fue seleccionada;
- abrir nuevas combinaciones ahora añadiría ruido y dispersión;
- una mejora mínima sobre la rama principal produce aprendizaje más acumulativo;
- conserva disciplina de una sola línea de desarrollo activa.

## 8. Secuencia sugerida
1. iterar salida causal simple (`Candidato A`)
2. si no aporta claridad, probar restricción temporal mínima (`Candidato B`)
3. solo después considerar endurecer entrada (`Candidato C`)

Result:
Artifacts created:
- `mgf-control/COMB_001_iteration_plan.md`
Files read:
- `mgf-control/strategy_candidate_COMB_001.md`
- `mgf-control/strategy_candidate_COMB_001_rules.md`
- `mgf-control/stpmt_branch_comparison.md`
- `mgf-control/combination_registry.md`
Scope respected: yes
Next recommended action: preparar una única iteración mínima sobre la salida de `COMB_001` sin cambiar de rama.
